"""Identité et traçabilité d'un entraînement.

Un run qu'on ne sait pas rattacher à son code, sa configuration et sa graine
n'est pas un résultat exploitable : au bout de trois semaines, `runs/` contient
une dizaine de modèles dont plus personne ne sait lequel marchait.

Chaque run vit donc dans son propre dossier, nommé selon une convention unique,
et pose à côté de ses courbes un `meta.json` qui dit exactement d'où il vient.

    runs/driver1-20261115-143012-ppo/
    ├── meta.json          qui, quoi, quand, avec quel code
    ├── bilan.json         les chiffres finaux du run
    └── events.out.*       les courbes lues par TensorBoard

Le SHA git est passé par variable d'environnement : le conteneur ne monte pas
`.git/`, il ne peut donc pas le lire lui-même. C'est le Makefile qui l'injecte.
"""

from __future__ import annotations

import json
import os
import platform
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

RACINE_RUNS = Path(os.environ.get("RUNS_DIR", "/app/runs"))


def fixer_graine(graine: int) -> None:
    """Fixe l'aléatoire de Python, numpy et torch.

    Le simulateur a sa propre graine, à lui passer séparément :
    `reset(num_cars, seed=graine)` réarme le bruit LiDAR **et** le moteur, ce
    qui rend l'épisode exactement rejouable. Sans graine explicite, le flux de
    bruit continue d'un épisode à l'autre et le run n'est pas reproductible.
    """
    random.seed(graine)
    np.random.seed(graine)
    try:
        import torch

        torch.manual_seed(graine)
        torch.use_deterministic_algorithms(True, warn_only=True)
    except ImportError:
        pass


def _versions() -> dict[str, str]:
    """Versions des paquets qui influencent un résultat."""
    versions = {"python": platform.python_version()}
    for nom in ("numpy", "torch", "gymnasium", "stable_baselines3", "onnx", "onnxruntime"):
        try:
            module = __import__(nom)
            versions[nom] = getattr(module, "__version__", "inconnu")
        except ImportError:
            versions[nom] = "absent"
    return versions


class Run:
    """Un entraînement, son dossier, ses métadonnées et ses courbes."""

    def __init__(
        self,
        pilote: str,
        algo: str = "ppo",
        config: dict[str, Any] | None = None,
        graine: int | None = None,
        circuits: list[str] | None = None,
        racine: Path | None = None,
    ) -> None:
        self.pilote = pilote
        self.algo = algo
        self.config = dict(config or {})
        self.graine = graine if graine is not None else int(self.config.get("graine", 0))
        self.circuits = list(circuits or self.config.get("circuits", []))

        horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.nom = f"{pilote}-{horodatage}-{algo}"
        self.dossier = (racine or RACINE_RUNS) / self.nom
        self.dossier.mkdir(parents=True, exist_ok=True)

        fixer_graine(self.graine)
        self._ecrire_meta()
        self._writer = None

    @property
    def writer(self):
        """SummaryWriter TensorBoard, ouvert à la première utilisation."""
        if self._writer is None:
            from torch.utils.tensorboard import SummaryWriter

            self._writer = SummaryWriter(log_dir=str(self.dossier))
        return self._writer

    def _ecrire_meta(self) -> None:
        meta = {
            "nom": self.nom,
            "pilote": self.pilote,
            "algo": self.algo,
            "graine": self.graine,
            "circuits": self.circuits,
            "date": datetime.now().isoformat(timespec="seconds"),
            "git": {
                "commit": os.environ.get("GIT_SHA", "inconnu"),
                "modifie": os.environ.get("GIT_DIRTY", "inconnu") == "1",
            },
            "versions": _versions(),
            "commande": " ".join(sys.argv),
            "config": self.config,
        }
        chemin = self.dossier / "meta.json"
        chemin.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

        if meta["git"]["commit"] == "inconnu":
            print(f"  [run] GIT_SHA absent — {self.nom} ne sera pas rattachable à un commit.")
        elif meta["git"]["modifie"]:
            print(f"  [run] dépôt modifié — {self.nom} n'est pas exactement reproductible.")

    def mesurer(self, mesures: dict[str, float], pas: int) -> None:
        """Envoie des métriques à TensorBoard."""
        for cle, valeur in mesures.items():
            self.writer.add_scalar(cle, valeur, pas)

    def enregistrer_bilan(self, bilan: dict[str, float]) -> None:
        """Écrit le résumé final à côté des courbes.

        Les scalaires TensorBoard servent aux tendances épisode par épisode.
        Un bilan est une valeur unique : le dupliquer en courbe plate n'apprend
        rien et double le nombre de cartes à l'écran.
        """
        chemin = self.dossier / "bilan.json"
        chemin.write_text(json.dumps(bilan, indent=2, ensure_ascii=False) + "\n")

    def fermer(self) -> None:
        if self._writer is not None:
            self._writer.flush()
            self._writer.close()
            self._writer = None

    def __enter__(self) -> Run:
        return self

    def __exit__(self, *_exc) -> None:
        self.fermer()

    def __repr__(self) -> str:
        return f"<Run {self.nom} graine={self.graine}>"
