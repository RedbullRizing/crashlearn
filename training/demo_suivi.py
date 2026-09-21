"""Vérifie la chaîne de suivi de bout en bout, sans attendre train.py.

Fait rouler quelques épisodes avec un pilote naïf — il suit la direction la plus
dégagée du LiDAR — et envoie les métriques dans TensorBoard via un vrai run.
Le pilote est volontairement médiocre : il abandonne, ce qui exerce justement
le code de détection des causes d'abandon.

    make suivi-demo

Ce n'est pas un entraînement, juste la preuve que runs.py et metrics.py
fonctionnent contre le vrai simulateur.

Limite assumée : ce pilote ne boucle jamais un tour, donc `taux_completion`,
`tour/temps_moyen` et `tour/meilleur` restent à zéro. Ces trois-là seront
exercés par la référence pure pursuit de CRA-8.
"""

from __future__ import annotations

import argparse

import numpy as np

import env_simulation as sim
from training.metrics import SuiviCourse, agreger
from training.runs import Run

VITESSE = 3.0
SECTEUR_AVANT = 1.05   # rad, ±60° autour de l'avant
BRAQUAGE_MAX = 0.41    # rad, borne du simulateur


def piloter(obs: dict) -> tuple[float, float]:
    """Vise le secteur le plus dégagé devant soi. Rudimentaire, et ça se voit.

    Attention à l'indexation : le simulateur pose `angle = -fov/2 + i * incr`,
    donc le rayon 0 regarde **vers l'arrière** et l'avant se trouve au milieu du
    tableau. Se tromper là-dessus donne une voiture qui fonce dans le mur en
    croyant suivre le couloir libre.
    """
    lidar = np.asarray(obs["lidar"], dtype=np.float32)
    n = len(lidar)
    angles = np.linspace(-np.pi, np.pi, n)

    devant = np.abs(angles) < SECTEUR_AVANT
    indice = int(np.argmax(np.where(devant, lidar, -np.inf)))

    braquage = float(np.clip(angles[indice], BRAQUAGE_MAX * -1, BRAQUAGE_MAX))
    # Ralentir quand ça se resserre droit devant.
    libre = float(lidar[n // 2])
    vitesse = VITESSE if libre > 3.0 else VITESSE * 0.4
    return vitesse, braquage


def jouer_episode(graine: int, pas_max: int) -> dict:
    sim.reset(num_cars=1, seed=graine)
    suivi = SuiviCourse(nb_voitures=1)

    for _ in range(pas_max):
        vitesse, braquage = piloter(sim.get_obs(0))
        sim.apply_action(0, vitesse, braquage)
        sim.simulation_step()
        info = sim.get_step_info()
        suivi.observer(info)
        if info["race_over"]:
            break

    return suivi.resultats()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilote", default="demo")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--pas-max", type=int, default=1200)
    parser.add_argument("--graine", type=int, default=42)
    parser.add_argument("--circuit", default="example")
    args = parser.parse_args()

    if args.circuit != "example":
        sim.set_map(args.circuit)

    config = {
        "graine": args.graine,
        "circuits": [args.circuit],
        "episodes": args.episodes,
        "pas_max": args.pas_max,
        "vitesse_cible": VITESSE,
    }

    with Run(pilote=args.pilote, algo="naif", config=config,
             graine=args.graine, circuits=[args.circuit]) as run:
        print(f"  run : {run.dossier}")
        episodes = []

        for n in range(args.episodes):
            # Une graine par épisode, dérivée de la graine du run : rejouable,
            # mais chaque épisode reste différent du précédent.
            resultats = jouer_episode(args.graine + n, args.pas_max)
            episodes.append(resultats)

            voiture = resultats[0]
            etat = "arrivée" if voiture.a_termine else (voiture.cause_abandon or "en course")
            print(f"  épisode {n + 1}/{args.episodes} : {etat}, "
                  f"{voiture.tours} tour(s), progression max {voiture.progression_max:.3f}")

            run.mesurer(agreger([resultats]), pas=n)

        bilan = agreger(episodes)
        run.mesurer({f"bilan/{k.split('/', 1)[1]}": v for k, v in bilan.items()},
                    pas=args.episodes)

        print("\n  bilan sur", args.episodes, "épisodes :")
        for cle, valeur in sorted(bilan.items()):
            print(f"    {cle:<38} {valeur:.3f}")
        print(f"\n  courbes : make board  →  http://localhost:6006")


if __name__ == "__main__":
    main()
