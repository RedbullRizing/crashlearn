"""Entraîne un pilote avec PPO sur `CourseSolo`, puis l'évalue en course.

    make train DRIVER=driver1 PAS=200000 CIRCUITS=example

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
from training.env import CourseSolo
from training.metrics import SuiviCourse, agreger
from training.runs import Run


def evaluer(model: PPO, circuits: list[str], episodes: int, graine: int) -> list[dict]:
    """Courses complètes, politique déterministe, sans fin sur choc : la vraie règle du tournoi."""
    env = CourseSolo(circuits=circuits, fin_sur_choc=False, pas_max=6000)
    resultats = []
    for n in range(episodes):
        obs, info = env.reset(seed=graine + n)
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
        print(f"  éval {n + 1}/{episodes} ({info['circuit']}) : {etat}, {voiture.tours} tour(s), "
              f"progression max {voiture.progression_max:.3f}, {voiture.chocs_mur} choc(s)")
    return resultats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilote", default="driver1")
    parser.add_argument("--pas", type=int, default=200_000, help="pas d'entraînement au total")
    parser.add_argument("--envs", type=int, default=4, help="environnements en parallèle")
    parser.add_argument("--circuits", default="example", help="séparés par des virgules")
    parser.add_argument("--graine", type=int, default=42)
    parser.add_argument("--eval-episodes", type=int, default=3)
    args = parser.parse_args()
    circuits = args.circuits.split(",")

    # Hyperparamètres par défaut de SB3, sauf n_steps : 512 × 4 envs = 2 048
    # pas par mise à jour, comme le défaut à un seul env. À régler dans CRA-72.
    config = {
        "graine": args.graine,
        "circuits": circuits,
        "pas": args.pas,
        "envs": args.envs,
        "ppo": {"n_steps": 512, "batch_size": 64, "gamma": 0.99, "learning_rate": 3e-4},
        "env": {"pas_max": 3000, "fin_sur_choc": True},
    }

    with Run(pilote=args.pilote, algo="ppo", config=config,
             graine=args.graine, circuits=circuits) as run:
        print(f"  run : {run.dossier}")
        envs = make_vec_env(CourseSolo, n_envs=args.envs, seed=args.graine,
                            vec_env_cls=SubprocVecEnv,
                            env_kwargs={"circuits": circuits, **config["env"]})

        model = PPO("MlpPolicy", envs, seed=args.graine, verbose=0, **config["ppo"])
        # Courbes PPO directement dans le dossier du run, à côté de meta.json,
        # plutôt que dans un sous-dossier PPO_1 créé par SB3.
        model.set_logger(configure(str(run.dossier), ["stdout", "tensorboard"]))
        model.learn(total_timesteps=args.pas)
        envs.close()
        model.save(run.dossier / "model.zip")

        print(f"\n  évaluation sur {args.eval_episodes} course(s) :")
        episodes = evaluer(model, circuits, args.eval_episodes, args.graine + 10_000)
        bilan = agreger(episodes)
        run.enregistrer_bilan(bilan)
        for cle, valeur in sorted(bilan.items()):
            print(f"    {cle:<38} {valeur:.3f}")
        print(f"\n  modèle : {run.dossier / 'model.zip'}")
        print("  courbes : make board  →  http://localhost:6006")


if __name__ == "__main__":
    main()
