"""Liste les runs avec leurs chiffres finaux, pour comparer d'un coup d'œil.

Deux sources : `runs/`, le brouillon local, et `archives/`, les runs gardés et
versionnés (`make garder`). La colonne « où » dit d'où vient chaque ligne.

    make runs                  tous les runs
    make runs DRIVER=driver2   seulement ceux d'un pilote

TensorBoard montre l'évolution épisode par épisode ; ce tableau montre le
`bilan.json` de chaque run, c'est-à-dire ce qu'on compare entre deux politiques.
Bibliothèque standard uniquement : tourne sur la machine, sans Docker.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCES = [("archive", RACINE / "archives"), ("local", RACINE / "runs")]

# (clé du bilan, titre de colonne, format)
COLONNES = [
    ("course/taux_completion", "complétion", "{:.0%}"),
    ("abandon/stagnation", "stagnation", "{:.0%}"),
    ("abandon/sortie_de_piste", "sortie", "{:.0%}"),
    ("course/progression_max_moyenne", "progression", "{:.3f}"),
    ("tour/meilleur", "meilleur tour", "{:.2f} s"),
    ("chocs/mur_par_voiture", "chocs mur", "{:.0f}"),
]


def _lire(chemin: Path) -> dict:
    try:
        return json.loads(chemin.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilote", default="", help="filtre sur le préfixe du run")
    args = parser.parse_args()

    dossiers = [
        (ou, d)
        for ou, racine in SOURCES if racine.is_dir()
        for d in sorted(racine.iterdir()) if d.is_dir()
    ]
    if args.pilote:
        dossiers = [(ou, d) for ou, d in dossiers if d.name.startswith(args.pilote + "-")]
    if not dossiers:
        print("  Aucun run dans runs/ ni archives/. Lancer par exemple : make courses")
        return

    lignes = []
    for ou, dossier in dossiers:
        meta, bilan = _lire(dossier / "meta.json"), _lire(dossier / "bilan.json")
        circuits = ",".join(meta.get("circuits", [])) or "?"
        valeurs = [
            fmt.format(bilan[cle]) if cle in bilan else "—"
            for cle, _, fmt in COLONNES
        ]
        # Un run sans bilan est en cours, ou a été interrompu.
        etat = "" if bilan else "  (pas de bilan)"
        lignes.append([ou, dossier.name, circuits, str(meta.get("graine", "?")), *valeurs, etat])

    titres = ["où", "run", "circuits", "graine", *(t for _, t, _ in COLONNES), ""]
    largeurs = [max(len(l[i]) for l in [titres, *lignes]) for i in range(len(titres))]
    for ligne in [titres, *lignes]:
        print("  " + "  ".join(c.ljust(w) for c, w in zip(ligne, largeurs)).rstrip())


if __name__ == "__main__":
    main()
