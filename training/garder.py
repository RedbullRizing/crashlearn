"""Garde un run : le copie de `runs/` (brouillon local) vers `archives/` (versionné).

    make garder RUN=driver1-20261115-143012-ppo NOTE="première reward qui boucle"

`runs/` est hors dépôt : ce qui y reste disparaît avec la machine ou un
nettoyage. Les runs qu'on veut montrer — l'évolution d'un pilote dans le
rapport, à la soutenance — sont copiés dans `archives/`, commités, et donc
partagés avec toute l'équipe et visibles dans le même TensorBoard.

Seul le léger est copié : courbes TensorBoard, `meta.json`, `bilan.json`,
configuration. Les modèles et points de sauvegarde restent dans `runs/` : un
modèle qu'on livre va dans `submission/`, pas dans l'historique git.

Bibliothèque standard uniquement : tourne sur la machine, sans Docker.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RUNS = RACINE / "runs"
ARCHIVES = RACINE / "archives"

# Poids de modèles, checkpoints, enregistrements : lourds, jamais archivés.
EXCLUS = {".zip", ".pt", ".pth", ".onnx", ".data", ".npz", ".pkl", ".mp4"}
TAILLE_ALERTE = 20 * 1024 * 1024   # au-delà, git souffre : on prévient


def _fichiers_a_garder(source: Path) -> list[Path]:
    return [
        f for f in sorted(source.rglob("*"))
        if f.is_file() and f.suffix not in EXCLUS and f.name != ".DS_Store"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="nom du dossier dans runs/")
    parser.add_argument("--note", default="", help="pourquoi on garde ce run")
    args = parser.parse_args()

    source = RUNS / args.run
    cible = ARCHIVES / args.run
    if not source.is_dir():
        print(f"  runs/{args.run} n'existe pas. Voir la liste avec : make runs")
        return 1
    if cible.exists():
        print(f"  archives/{args.run} existe déjà.")
        return 1

    meta = {}
    try:
        meta = json.loads((source / "meta.json").read_text())
    except (OSError, json.JSONDecodeError):
        print("  [attention] pas de meta.json lisible : run impossible à rattacher à son code.")
    if meta.get("git", {}).get("modifie"):
        print("  [attention] run lancé avec du code non commité : il ne sera pas reproductible.")
    if not (source / "bilan.json").exists():
        print("  [attention] pas de bilan.json : run interrompu ou encore en cours.")

    fichiers = _fichiers_a_garder(source)
    taille = sum(f.stat().st_size for f in fichiers)
    if taille > TAILLE_ALERTE:
        print(f"  [attention] {taille / 1e6:.1f} Mo à versionner : vérifier qu'aucun fichier lourd ne s'est glissé.")

    for f in fichiers:
        destination = cible / f.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, destination)

    # La note dit pourquoi ce run compte : c'est ce qu'on relira en écrivant le rapport.
    note = args.note.strip() or "(pas de note)"
    (cible / "note.md").write_text(
        f"# {args.run}\n\n{note}\n\n"
        f"Archivé le {datetime.now():%Y-%m-%d %H:%M}, "
        f"commit du run : {meta.get('git', {}).get('commit', 'inconnu')}.\n"
    )

    ignores = sum(1 for f in source.rglob("*") if f.is_file() and f.suffix in EXCLUS)
    print(f"  archives/{args.run} : {len(fichiers)} fichier(s), {taille / 1e3:.0f} Ko"
          + (f", {ignores} fichier(s) lourd(s) laissé(s) dans runs/" if ignores > 0 else ""))
    print(f"  Pour le partager : git add archives/{args.run} && git commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
