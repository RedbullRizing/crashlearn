"""Prépare les fiches d'entraînement pour le visualiseur (`visualiseur/`).

    make vue-runs

Lit chaque run de `archives/` (gardés, versionnés) et de `runs/` (brouillon
local) et écrit `recordings/entrainements.json`. Le visualiseur y trouve, pour
chaque run, exactement ce que l'entraînement a écrit : la configuration de
`meta.json`, les chiffres de `bilan.json`, la note de `note.md`, les courbes
TensorBoard et la liste des sauvegardes. Rien n'est recalculé ni corrigé.

Lecture seule : ce script n'ouvre aucun simulateur et ne modifie aucun run.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from training import vers_visualiseur as vv

SOURCES = (("archive", Path("archives")), ("local", Path("runs")))
SORTIE = vv.RECORDINGS / "entrainements.json"
COURBES = ("rollout/ep_rew_mean", "rollout/ep_len_mean")
POINTS_PAR_COURBE = 300
MOTIF_SAUVEGARDE = re.compile(r"model_(\d+)_steps\.zip")


def lire_json(chemin: Path) -> dict:
    """Le contenu d'un fichier JSON, ou un dictionnaire vide s'il manque ou est illisible."""
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def note(dossier: Path) -> str:
    """Le texte de `note.md` sans sa ligne de titre, ou une chaîne vide."""
    try:
        lignes = (dossier / "note.md").read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    return "\n".join(ligne for ligne in lignes if not ligne.startswith("#")).strip()


def sauvegardes(dossier: Path) -> list[int]:
    """Les nombres de pas des modèles intermédiaires de `sauvegardes/`, triés."""
    trouvees = (MOTIF_SAUVEGARDE.fullmatch(p.name) for p in (dossier / "sauvegardes").glob("*.zip"))
    return sorted(int(m.group(1)) for m in trouvees if m)


def courbes(dossier: Path) -> dict[str, dict[str, list[float]]]:
    """Les séries TensorBoard de `COURBES` : pas d'entraînement et valeur, allégées si besoin."""
    if not any(dossier.glob("events.out.tfevents.*")):
        return {}
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    journal = EventAccumulator(str(dossier), size_guidance={"scalars": 0})
    journal.Reload()
    resultat = {}
    for cle in COURBES:
        if cle not in journal.Tags()["scalars"]:
            continue
        points = journal.Scalars(cle)
        points = points[::max(1, len(points) // POINTS_PAR_COURBE)]
        resultat[cle] = {
            "pas": [int(p.step) for p in points],
            "valeurs": [round(float(p.value), 4) for p in points],
        }
    return resultat


def fiche(origine: str, dossier: Path) -> dict:
    """Tout ce qu'un run a écrit sur lui-même, sans transformation."""
    meta = lire_json(dossier / "meta.json")
    return {
        "nom": dossier.name,
        "origine": origine,
        "pilote": meta.get("pilote", ""),
        "algo": meta.get("algo", ""),
        "date": meta.get("date", ""),
        "git": meta.get("git", {}),
        "versions": meta.get("versions", {}),
        "config": meta.get("config", {}),
        "circuits": meta.get("circuits", []),
        "circuits_eval": meta.get("config", {}).get("circuits_eval", []),
        "bilan": lire_json(dossier / "bilan.json"),
        "note": note(dossier),
        "sauvegardes": sauvegardes(dossier),
        "courbes": courbes(dossier),
    }


def traces(circuits: set[str]) -> dict[str, list[float]]:
    """Le tracé allégé de chaque circuit dont la carte existe."""
    resultat = {}
    for circuit in sorted(circuits):
        try:
            resultat[circuit] = vv.trace_allege(vv.lire_carte(circuit)["ligne_centrale"][:, :2])
        except (OSError, KeyError, ValueError):
            continue
    return resultat


def exporter(sources=SOURCES) -> dict:
    """Les fiches de tous les runs, du plus récent au plus ancien, et les tracés de leurs circuits.

    Un run présent dans deux sources garde la fiche de la première, l'archive.
    """
    fiches = [
        fiche(origine, dossier)
        for origine, racine in sources if racine.is_dir()
        for dossier in sorted(racine.iterdir())
        if dossier.is_dir() and (dossier / "meta.json").exists()
    ]
    fiches = list({f["nom"]: f for f in reversed(fiches)}.values())
    fiches.sort(key=lambda f: f["date"], reverse=True)
    circuits = {c for f in fiches for c in (*f["circuits"], *f["circuits_eval"]) if isinstance(c, str)}
    return {"runs": fiches, "circuits": traces(circuits)}


def main() -> None:
    donnees = exporter()
    SORTIE.write_text(json.dumps(donnees, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    archives = sum(f["origine"] == "archive" for f in donnees["runs"])
    print(f"  {SORTIE} : {len(donnees['runs'])} run(s), dont {archives} archivé(s)")
    print("  à voir avec : make visualiseur, onglet Entraînements")


if __name__ == "__main__":
    main()
