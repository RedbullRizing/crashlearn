"""Entraîne un pilote avec PPO sur `Course`, puis l'évalue en course.

    make train DRIVER=driver1                                  # training/configs/driver1.yaml
    make train DRIVER=driver1 PAS=1000000
    make train DRIVER=driver1 PAS=200000 CIRCUITS=example     # débogage

Les réglages du pilote (graine, hyperparamètres PPO, poids de la récompense)
viennent de `training/configs/<pilote>.yaml` ; une option de la ligne de commande
l'emporte sur le fichier (voir `config.py`).

Un run complet : `meta.json` (graine, commit, configuration), les courbes PPO
dans TensorBoard, `model.zip` (Stable-Baselines3), puis une évaluation sur le
banc de `courses.py` dont les chiffres vont dans `bilan.json`. L'export ONNX
pour `submission/` est l'affaire de CRA-74.

Les environnements tournent chacun dans son processus (`SubprocVecEnv`) : le
simulateur est un état global, deux environnements dans le même processus
conduiraient la même voiture.
"""

from __future__ import annotations

import argparse
import sys

sys.modules["gym"] = None

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import SubprocVecEnv

import env_simulation as sim
from training.config import charger
from training.env import ENTRAINEMENT, VALIDATION, Course, parametres_recompense
from training.metrics import SuiviCourse, agreger
from training.runs import RACINE_RUNS, Run


def evaluer(model: PPO, circuits: list[str], episodes: int, graine: int,
            adversaires: list[str] = ()) -> list[dict]:
    """Courses complètes sur chaque circuit, politique déterministe, sans fin sur
    choc : la vraie règle du tournoi. Mêmes graines pour toutes les politiques.
    Une course sur deux sous la pluie ; avec des adversaires, tous au départ."""
    env = Course(circuits=circuits, fin_sur_choc=False, pas_max=6000, adversaires=adversaires)
    resultats = []
    for circuit, n in [(c, n) for c in circuits for n in range(episodes)]:
        meteo = n % 2 == 1
        obs, info = env.reset(seed=graine + n, options={
            "circuit": circuit, "meteo": meteo, "adversaires": len(adversaires)})
        suivi = SuiviCourse(nb_voitures=1 + len(adversaires))
        fini = False
        while not fini:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, termine, tronque, _ = env.step(action)
            suivi.observer(sim.get_step_info())
            fini = termine or tronque
        resultats.append({0: suivi.resultats()[info["ego"]]})

        voiture = resultats[-1][0]
        etat = "arrivée" if voiture.a_termine else (voiture.cause_abandon or "temps écoulé")
        print(f"  éval {info['circuit']} {'pluie' if meteo else 'sec'} : {etat}, {voiture.tours} tour(s), "
              f"progression max {voiture.progression_max:.3f}, {voiture.chocs_mur} choc(s) mur, "
              f"{voiture.chocs_voiture} contact(s)")
    return resultats


def main() -> None:
    torch.set_num_threads(1)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilote", default="driver1")
    parser.add_argument("--config", help="fichier YAML (défaut : training/configs/<pilote>.yaml s'il existe)")
    parser.add_argument("--pas", type=int, help="pas d'entraînement au total")
    parser.add_argument("--envs", type=int, help="environnements en parallèle")
    parser.add_argument("--circuits", default="", help="séparés par des virgules (défaut : ENTRAINEMENT)")
    parser.add_argument("--graine", type=int)
    parser.add_argument("--eval-episodes", type=int, help="par circuit d'évaluation")
    args = parser.parse_args()
    circuits = args.circuits.split(",") if args.circuits else list(ENTRAINEMENT)
    circuits_eval = list(VALIDATION) if not args.circuits else circuits

    config, fichier = charger(args.pilote, args.config, {
        "graine": args.graine, "pas": args.pas, "envs": args.envs, "eval_episodes": args.eval_episodes,
    })
    config["recompense"] = parametres_recompense(config["recompense"])
    config["fichier"] = str(fichier) if fichier else None
    config["circuits"] = circuits
    config["circuits_eval"] = circuits_eval
    print(f"  configuration : {fichier or 'valeurs par défaut (aucun fichier)'}")

    with Run(pilote=args.pilote, algo="ppo", config=config,
             graine=config["graine"], circuits=circuits) as run:
        print(f"  run : {run.dossier}")
        envs = make_vec_env(Course, n_envs=config["envs"], seed=config["graine"],
                            vec_env_cls=SubprocVecEnv,
                            env_kwargs={"circuits": circuits, **config["env"],
                                        "recompense": config["recompense"]})

        if config["depuis"]:
            model = PPO.load(RACINE_RUNS / config["depuis"] / "model.zip", env=envs,
                             seed=config["graine"], **config["ppo"])
        else:
            model = PPO("MlpPolicy", envs, seed=config["graine"], verbose=0, **config["ppo"])
        model.set_logger(configure(str(run.dossier), ["stdout", "tensorboard"]))
        sauvegarde = CheckpointCallback(save_freq=max(100_000 // config["envs"], 1),
                                        save_path=str(run.dossier / "sauvegardes"), name_prefix="model")
        model.learn(total_timesteps=config["pas"], callback=sauvegarde)
        envs.close()
        model.save(run.dossier / "model.zip")

        print(f"\n  évaluation, {config['eval_episodes']} course(s) par circuit :")
        episodes = evaluer(model, circuits_eval, config["eval_episodes"], config["graine"] + 10_000,
                           config["env"]["adversaires"])
        bilan = agreger(episodes)
        run.enregistrer_bilan(bilan)
        for cle, valeur in sorted(bilan.items()):
            print(f"    {cle:<38} {valeur:.3f}")
        print(f"\n  modèle : {run.dossier / 'model.zip'}")
        print("  courbes : make board  →  http://localhost:6006")


if __name__ == "__main__":
    main()
