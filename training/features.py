"""Prétraitement partagé entre l'entraînement (`env.py`) et la course (`agent.py`).

C'est le contrat du MDP v2 (document Linear « Formalisme MDP et fonction de
récompense ») : ce qui entre dans le réseau et ce qui en sort. Si ce calcul
diffère d'un côté à l'autre, l'agent se dégrade au tournoi sans aucune erreur.
Il n'existe donc qu'ici.

Contraintes, parce que ce fichier part tel quel dans `submission/<pilote>/` :

* **numpy seulement.** Rien d'autre, pas même un module du dépôt.
* **Pas de `import features` dans `agent.py`** : `verify_submission.py` refuse
  tout import hors de `onnxruntime`, `numpy` et `os`, et les agents de toutes
  les équipes partagent un seul `sys.modules`. `agent.py` exécute ce fichier
  depuis son propre dossier.

Les rayons LiDAR balaient dans le sens trigonométrique à partir de l'arrière :
rayon `i` à `-178,2° + 3,6° × i` du cap, donc l'avant est entre les rayons 49
et 50, et les indices au-dessus de 50 regardent à gauche
(`laser_models.get_scan`). Le LiDAR ne voit que les murs : les autres voitures
n'apparaissent que dans `obs["opponents"]`.

Un seul format pour les pilotes solo et le champion : seul, une voiture ne voit
aucun adversaire et ces entrées restent à zéro.
"""

import numpy as np

RAYONS_AVANT = slice(23, 77)   # 54 rayons, ±95,4° autour du cap
RAYONS_PAR_SECTEUR = 3         # 18 secteurs de 10,8°
LIDAR_MIN = 0.1                # m, troncature du simulateur
LIDAR_MAX = 15.0
VITESSE_MIN = -2.0             # m/s, bornes de la commande du simulateur :
VITESSE_MAX = 10.0             # la marche arrière sert à se dégager d'un mur
BRAQUAGE_MAX = 0.4189          # rad, borne de la commande
FRICTION_SEC, FRICTION_PLUIE = 1.0, 0.5   # adhérence : 1 au sec, 0,5 sous forte pluie

ADVERSAIRES = 3                # les trois autres voitures au plus
PORTEE_ADVERSAIRE = 10.0       # m : au-delà, un adversaire est à la limite de l'entrée
PAR_ADVERSAIRE = 5             # présent, x, y, cap relatif, vitesse

TAILLE_OBSERVATION = 54 // RAYONS_PAR_SECTEUR + 5 + ADVERSAIRES * PAR_ADVERSAIRE   # 38


def adversaires(obs: dict) -> np.ndarray:
    """Les adversaires actifs, du plus proche au plus loin, dans le repère de la
    voiture (x vers l'avant, y vers la gauche). Absents : des zéros."""
    vus = []
    for adv in (obs.get("opponents") or {}).values():
        if adv["status"] != 1:      # la voiture elle-même, un absent ou un abandon
            continue
        x, y = adv["x_rel"], adv["y_rel"]
        vus.append((x * x + y * y, [1.0,
                                     np.clip(x / PORTEE_ADVERSAIRE, -1.0, 1.0),
                                     np.clip(y / PORTEE_ADVERSAIRE, -1.0, 1.0),
                                     adv["yaw_rel"] / np.pi,
                                     adv["speed"] / VITESSE_MAX]))
    vus.sort(key=lambda v: v[0])
    sortie = np.zeros((ADVERSAIRES, PAR_ADVERSAIRE), dtype=np.float32)
    for i, (_, valeurs) in enumerate(vus[:ADVERSAIRES]):
        sortie[i] = valeurs
    return sortie.ravel()


def observation(obs: dict, info: dict, action_precedente: np.ndarray) -> np.ndarray:
    """Observation brute de `get_obs()` et `get_step_info()` vers le vecteur
    d'entrée du réseau (38 valeurs, toutes dans [-1,5 ; 1,5]).

    `action_precedente` est la sortie du réseau au pas d'avant, déjà écrêtée à
    [-1, 1] — des zéros au premier pas.
    """
    rayons = np.asarray(obs["lidar"], dtype=np.float32)[RAYONS_AVANT]
    secteurs = rayons.reshape(-1, RAYONS_PAR_SECTEUR).min(axis=1)
    # Logarithme : en linéaire sur 15 m, tout ce qui compte (0,1 à 2 m) tiendrait
    # dans [0 ; 0,13]. Ici 1 m vaut 0,46.
    secteurs = np.log(np.clip(secteurs, LIDAR_MIN, LIDAR_MAX) / LIDAR_MIN) / np.log(LIDAR_MAX / LIDAR_MIN)

    # L'adhérence est donnée par le simulateur : la pluie se voit, au lieu de se deviner.
    friction = float(info.get("friction_current", FRICTION_SEC))
    pluie = np.clip((FRICTION_SEC - friction) / (FRICTION_SEC - FRICTION_PLUIE), 0.0, 1.0)

    etat = [obs["velocity"] / VITESSE_MAX, obs["steering"] / BRAQUAGE_MAX, pluie]
    return np.concatenate([secteurs, etat, action_precedente, adversaires(obs)]).astype(np.float32)


def commande(action: np.ndarray) -> tuple[float, float]:
    """Sortie du réseau, écrêtée à [-1, 1], vers `(target_speed, steering)`.

    -1 donne -2 m/s (marche arrière), 1 donne 10 m/s.
    """
    a = np.clip(action, -1.0, 1.0)
    vitesse = VITESSE_MIN + (a[0] + 1.0) / 2.0 * (VITESSE_MAX - VITESSE_MIN)
    return float(vitesse), float(a[1] * BRAQUAGE_MAX)
