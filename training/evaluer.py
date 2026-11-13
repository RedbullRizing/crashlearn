"""Compare des modèles entraînés sur les mêmes 12 courses de validation.

    make evaluer RUN="driver1-20261113-131306-ppo driver1-20261114-101500-ppo"

Le bilan de fin d'entraînement ne joue que 6 courses : trop peu, le même modèle
y passe de 3/6 à 6/6 selon la graine. Ici chaque modèle court 4 fois sur chacun
des 3 circuits de validation, sec et pluie en alternance, avec les mêmes graines
pour tous : les écarts viennent du pilote, pas du tirage.
"""

from __future__ import annotations

import contextlib
import io
import sys
from collections import defaultdict
from multiprocessing import Pool

sys.modules["gym"] = None

CIRCUITS = ["Oschersleben", "Zandvoort", "MexicoCity"]
COURSES_PAR_CIRCUIT = 4
GRAINE = 20_000


def courir(tache: tuple[str, str]) -> tuple[str, list[tuple]]:
    """Fait courir un modèle sur un circuit ; un processus par tâche, car le simulateur n'admet qu'une course par processus."""
    chemin, circuit = tache
    import torch
    torch.set_num_threads(1)
    from stable_baselines3 import PPO
    from training.train import evaluer

    modele = PPO.load(chemin, device="cpu")
    with contextlib.redirect_stdout(io.StringIO()):
        courses = evaluer(modele, [circuit], COURSES_PAR_CIRCUIT, GRAINE)
    return chemin, [(circuit, n % 2, c[0].a_termine, c[0].chocs_mur, c[0].temps_au_tour)
                    for n, c in enumerate(courses)]


def ligne(nom: str, courses: list[tuple]) -> str:
    total = len(courses)
    finies = [c for c in courses if c[2]]
    tours = {circuit: min((t for c in courses if c[0] == circuit for t in c[4]), default=None)
             for circuit in CIRCUITS}
    return (f"{nom:<40} finies {len(finies):>2}/{total} "
            f"sec {sum(1 for c in finies if c[1] == 0)}/{total // 2} "
            f"pluie {sum(1 for c in finies if c[1] == 1)}/{total // 2} "
            f"chocs/course {sum(c[3] for c in courses) / total:5.1f}  meilleur tour "
            + " ".join(f"{c[:5]} {t:.1f}" if t else f"{c[:5]} -" for c, t in tours.items()))


def main() -> None:
    runs = sys.argv[1:]
    if not runs:
        sys.exit("Préciser au moins un run : make evaluer RUN=<nom>  (liste : make runs)")
    chemins = {f"runs/{run}/model.zip": run for run in runs}
    bilan = defaultdict(list)
    with Pool(8, maxtasksperchild=1) as pool:
        for chemin, courses in pool.imap_unordered(courir, [(c, circuit) for c in chemins for circuit in CIRCUITS]):
            bilan[chemin] += courses
    for chemin, run in chemins.items():
        print(ligne(run, bilan[chemin]), flush=True)


if __name__ == "__main__":
    main()
