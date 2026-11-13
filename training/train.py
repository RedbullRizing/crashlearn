"""Entraîne un pilote avec PPO sur `CourseSolo`, puis l'évalue en course.

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

# Le dossier gym/ du simulateur (/app/gym) se fait passer pour le paquet `gym`,
# sans __version__ : model.save() plante en notant les versions installées.
# `import gym` lève ainsi ImportError, que SB3 sait ignorer. Le moteur, lui,
# s'importe sous le nom f110_gym, il n'est pas touché.
sys.modules["gym"] = None

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import SubprocVecEnv

import env_simulation as sim
from training.config import charger
from training.env import ENTRAINEMENT, VALIDATION, CourseSolo, parametres_recompense
from training.metrics import SuiviCourse, agreger
from training.runs import Run


def evaluer(model: PPO, circuits: list[str], episodes: int, graine: int) -> list[dict]:
    """Courses complètes sur chaque circuit, politique déterministe, sans fin sur
    choc : la vraie règle du tournoi. Mêmes graines pour toutes les politiques."""
    env = CourseSolo(circuits=circuits, fin_sur_choc=False, pas_max=6000)
    resultats = []
    for circuit, n in [(c, n) for c in circuits for n in range(episodes)]:
        obs, info = env.reset(seed=graine + n, options={"circuit": circuit})
        suivi = SuiviCourse(nb_voitures=1)
        fini = False
        while not fini:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, termine, tronque, _ = env.step(action)
            suivi.observer(sim.get_step_info())
            fini = termine or tronque
        resultats.append(suivi.resultats())

        voiture = resultats[-1][0]
        etat = "arrivée" if voiture.a_termine else (voiture.cause_abandon or "temps écoulé")
        print(f"  éval {info['circuit']} {n + 1}/{episodes} : {etat}, {voiture.tours} tour(s), "
              f"progression max {voiture.progression_max:.3f}, {voiture.chocs_mur} choc(s)")
    return resultats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilote", default="driver1")
    parser.add_argument("--config", help="fichier YAML (défaut : training/configs/<pilote>.yaml s'il existe)")
    # Pas de valeur par défaut ici : une option non donnée laisse la main au fichier.
    parser.add_argument("--pas", type=int, help="pas d'entraînement au total")
    parser.add_argument("--envs", type=int, help="environnements en parallèle")
    parser.add_argument("--circuits", default="", help="séparés par des virgules (défaut : ENTRAINEMENT)")
    parser.add_argument("--graine", type=int)
    parser.add_argument("--eval-episodes", type=int, help="par circuit d'évaluation")
    args = parser.parse_args()
    circuits = args.circuits.split(",") if args.circuits else list(ENTRAINEMENT)
    # On évalue sur des circuits jamais vus, sauf en débogage sur un circuit choisi à la main.
    circuits_eval = list(VALIDATION) if not args.circuits else circuits

    # Hyperparamètres par défaut de SB3, sauf n_steps (voir config.DEFAUTS). À régler dans CRA-72.
    config, fichier = charger(args.pilote, args.config, {
        "graine": args.graine, "pas": args.pas, "envs": args.envs, "eval_episodes": args.eval_episodes,
    })
    # Poids complets dans meta.json, y compris ceux qu'aucun fichier ne surcharge ;
    # une clé inconnue s'arrête ici, avant de lancer les processus.
    config["recompense"] = parametres_recompense(config["recompense"])
    config["fichier"] = str(fichier) if fichier else None
    config["circuits"] = circuits
    config["circuits_eval"] = circuits_eval
    print(f"  configuration : {fichier or 'valeurs par défaut (aucun fichier)'}")

    with Run(pilote=args.pilote, algo="ppo", config=config,
             graine=config["graine"], circuits=circuits) as run:
        print(f"  run : {run.dossier}")
        envs = make_vec_env(CourseSolo, n_envs=config["envs"], seed=config["graine"],
                            vec_env_cls=SubprocVecEnv,
                            env_kwargs={"circuits": circuits, **config["env"],
                                        "recompense": config["recompense"]})

        model = PPO("MlpPolicy", envs, seed=config["graine"], verbose=0, **config["ppo"])
        # Courbes PPO directement dans le dossier du run, à côté de meta.json,
        # plutôt que dans un sous-dossier PPO_1 créé par SB3.
        model.set_logger(configure(str(run.dossier), ["stdout", "tensorboard"]))
        model.learn(total_timesteps=config["pas"])
        envs.close()
        model.save(run.dossier / "model.zip")

        print(f"\n  évaluation, {config['eval_episodes']} course(s) par circuit :")
        episodes = evaluer(model, circuits_eval, config["eval_episodes"], config["graine"] + 10_000)
        bilan = agreger(episodes)
        run.enregistrer_bilan(bilan)
        for cle, valeur in sorted(bilan.items()):
            print(f"    {cle:<38} {valeur:.3f}")
        print(f"\n  modèle : {run.dossier / 'model.zip'}")
        print("  courbes : make board  →  http://localhost:6006")


if __name__ == "__main__":
    main()
