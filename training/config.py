"""Configuration d'un entraînement : défauts, fichier du pilote, ligne de commande.

Chacun fait diverger son pilote (graine, hyperparamètres, poids de la récompense)
dans son propre `training/configs/<pilote>.yaml`, sans toucher au code partagé.
Priorité croissante :

    DEFAUTS  <  training/configs/<pilote>.yaml  <  options de la ligne de commande

Ce module ne dépend ni du simulateur ni de Stable-Baselines3 : il se charge et se
teste partout. La validité des poids de récompense est vérifiée par
`env.parametres_recompense`, qui les connaît.
"""

from __future__ import annotations

from pathlib import Path

import yaml

DOSSIER = Path(__file__).parent / "configs"

# Valeurs du premier entraînement (CRA-71) : sans fichier, un run se comporte comme avant.
DEFAUTS = {
    "graine": 42,
    "pas": 200_000,
    "envs": 4,
    "eval_episodes": 2,
    "depuis": "",        # run de départ dans runs/ : vide, on part de zéro
    # n_steps = 512 × 4 envs = 2 048 pas par mise à jour, comme le défaut de SB3 à un seul
    # env. Toute autre clé de `PPO(...)` est acceptée ; SB3 refuse celles qu'il ne connaît pas.
    "ppo": {"n_steps": 512, "batch_size": 64, "gamma": 0.99, "learning_rate": 3e-4},
    "env": {"pas_max": 3000, "fin_sur_choc": True, "meteo": True, "adversaires": []},
    "recompense": {},     # surcharges des poids de `env.RECOMPENSE_DEFAUT`
}

_ENTIERS = ("graine", "pas", "envs", "eval_episodes")
_CLES_ENV = {"pas_max", "fin_sur_choc", "meteo", "adversaires"}


def _lire(chemin: Path) -> dict:
    with open(chemin, encoding="utf-8") as f:
        contenu = yaml.safe_load(f) or {}
    if not isinstance(contenu, dict):
        raise ValueError(f"{chemin} : un dictionnaire YAML est attendu")
    return contenu


def _fusionner(base: dict, ajout: dict, origine: str) -> dict:
    """`ajout` par-dessus `base` : clé à clé, et à l'intérieur de ppo/env/recompense."""
    inconnues = set(ajout) - set(base)
    if inconnues:
        raise ValueError(f"{origine} : clés inconnues {sorted(inconnues)} (attendues : {sorted(base)})")
    resultat = {cle: (dict(valeur) if isinstance(valeur, dict) else valeur) for cle, valeur in base.items()}
    for cle, valeur in ajout.items():
        if isinstance(base[cle], dict):
            if valeur is None:      # « ppo: » laissé vide dans le fichier
                continue
            if not isinstance(valeur, dict):
                raise ValueError(f"{origine} : « {cle} » doit être un dictionnaire")
            resultat[cle] = {**base[cle], **valeur}
        else:
            resultat[cle] = valeur
    return resultat


def charger(pilote: str, chemin: str | Path | None = None,
            surcharges: dict | None = None) -> tuple[dict, Path | None]:
    """Configuration effective d'un pilote, et le fichier lu (`None` s'il n'y en a pas).

    `chemin` impose un fichier, qui doit exister ; sinon c'est `configs/<pilote>.yaml`
    quand il existe. `surcharges` vient de la ligne de commande : les valeurs `None`
    (option non donnée) sont ignorées."""
    if chemin is not None:
        fichier = Path(chemin)
        if not fichier.is_file():
            raise FileNotFoundError(f"fichier de configuration introuvable : {fichier}")
    else:
        fichier = DOSSIER / f"{pilote}.yaml"
        fichier = fichier if fichier.is_file() else None

    config = _fusionner(DEFAUTS, _lire(fichier), str(fichier)) if fichier else _fusionner(DEFAUTS, {}, "")
    config = _fusionner(config, {k: v for k, v in (surcharges or {}).items() if v is not None},
                        "ligne de commande")

    for cle in _ENTIERS:
        if isinstance(config[cle], bool) or not isinstance(config[cle], int):
            raise ValueError(f"« {cle} » doit être un entier, pas {config[cle]!r}")
    inconnues = set(config["env"]) - _CLES_ENV
    if inconnues:
        raise ValueError(f"« env » : clés inconnues {sorted(inconnues)} (attendues : {sorted(_CLES_ENV)})")
    return config, fichier
