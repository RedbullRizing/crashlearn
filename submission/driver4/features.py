"""Prétraitement partagé entre l'entraînement (`env.py`) et la course (`agent.py`).

C'est le contrat du MDP v1 (CRA-68, document Linear « Formalisme MDP et
fonction de récompense ») : ce qui entre dans le réseau et ce qui en sort. Si ce
calcul diffère d'un côté à l'autre, l'agent se dégrade au tournoi sans aucune
erreur. Il n'existe donc qu'ici.

Contraintes, parce que ce fichier part tel quel dans `submission/driverN/` :

* **numpy seulement.** Rien d'autre, pas même un module du dépôt.
* **Pas de `import features` dans `agent.py`** : `verify_submission.py` refuse
  tout import hors de `onnxruntime`, `numpy` et `os`, et les agents de toutes
  les équipes partagent un seul `sys.modules`. `agent.py` exécute ce fichier
  depuis son propre dossier (CRA-74).

Les rayons LiDAR balaient dans le sens trigonométrique à partir de l'arrière :
rayon `i` à `-178,2° + 3,6° × i` du cap, donc l'avant est entre les rayons 49
et 50, et les indices au-dessus de 50 regardent à gauche
(`laser_models.get_scan`).
"""

import numpy as np

RAYONS_AVANT = slice(23, 77)   # 54 rayons, ±95,4° autour du cap
RAYONS_PAR_SECTEUR = 3         # 18 secteurs de 10,8°
LIDAR_MIN = 0.1                # m, troncature du simulateur
LIDAR_MAX = 15.0
VITESSE_MAX = 10.0             # m/s, borne haute de la commande
BRAQUAGE_MAX = 0.4189          # rad, borne de la commande

TAILLE_OBSERVATION = 54 // RAYONS_PAR_SECTEUR + 4   # 18 secteurs, vitesse, braquage, action précédente


def observation(obs: dict, action_precedente: np.ndarray) -> np.ndarray:
    """Observation brute de `get_obs()` vers le vecteur d'entrée du réseau (22 valeurs).

    `action_precedente` est la sortie du réseau au pas d'avant, déjà écrêtée à
    [-1, 1] — des zéros au premier pas.
    """
    rayons = np.asarray(obs["lidar"], dtype=np.float32)[RAYONS_AVANT]
    secteurs = rayons.reshape(-1, RAYONS_PAR_SECTEUR).min(axis=1)
    # Logarithme : en linéaire sur 15 m, tout ce qui compte (0,1 à 2 m) tiendrait
    # dans [0 ; 0,13]. Ici 1 m vaut 0,46.
    secteurs = np.log(np.clip(secteurs, LIDAR_MIN, LIDAR_MAX) / LIDAR_MIN) / np.log(LIDAR_MAX / LIDAR_MIN)

    etat = [obs["velocity"] / VITESSE_MAX, obs["steering"] / BRAQUAGE_MAX]
    return np.concatenate([secteurs, etat, action_precedente]).astype(np.float32)


def commande(action: np.ndarray) -> tuple[float, float]:
    """Sortie du réseau, écrêtée à [-1, 1], vers `(target_speed, steering)`.

    Vitesse dans [0, 10] m/s : pas de marche arrière en v1.
    """
    a = np.clip(action, -1.0, 1.0)
    return float((a[0] + 1.0) / 2.0 * VITESSE_MAX), float(a[1] * BRAQUAGE_MAX)
