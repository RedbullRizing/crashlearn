"""Prépare une course enregistrée pour le visualiseur 3D (`visualiseur/`).

    make vue NAME=driver1

Lit `recordings/<nom>.npz`, écrit par `make record`, et la carte de son circuit.
Écrit `recordings/<nom>.json`, que le navigateur lit tel quel, et met à jour
`recordings/courses.json`, la liste des courses converties.

Le visualiseur ne fait que relire ces fichiers : il ne touche jamais au
simulateur, donc il ne ralentit ni ne perturbe un entraînement en cours.

Repère : celui du simulateur, en mètres. Une ligne de pixel `r` et une colonne
`c` de l'image de la carte valent `x = ox + c * res` et `y = oy + (h - 1 - r) * res`,
comme dans `viz_replay.py`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import yaml
from PIL import Image

RECORDINGS = Path("recordings")
CARTES = Path("maps")
LISTE_DES_COURSES = "courses.json"

SEUIL_MUR = 128
TOLERANCE_BORD_PX = 1.0
NB_ARBRES = 450
ARBRES_DISTANCE_MIN_M = 2.5
ARBRES_DISTANCE_MAX_M = 30.0
ECART_CAMERAS_TV_M = 25.0
RECUL_CAMERAS_TV_M = 2.0
DECIMALES = 3
POINTS_DU_TRACE = 160


def chemin_carte(circuit: str) -> Path:
    """Le yaml de la carte, rangé comme le cherche `viz_replay.py`."""
    if circuit == "example":
        return CARTES / "examples" / "example_map.yaml"
    return CARTES / circuit / f"{circuit}_map.yaml"


def lire_carte(circuit: str) -> dict:
    """Image d'occupation, résolution, origine et ligne centrale d'un circuit.

    La ligne centrale a quatre colonnes : x, y, largeur à droite, largeur à gauche.
    """
    yaml_carte = chemin_carte(circuit)
    meta = yaml.safe_load(yaml_carte.read_text())
    image = np.array(Image.open(yaml_carte.with_name(meta["image"])))
    if image.ndim == 3:
        image = image[..., 0]
    centre = yaml_carte.with_name(yaml_carte.name.replace("_map.yaml", "_centerline.csv"))
    return {
        "murs": image <= SEUIL_MUR,
        "resolution": float(meta["resolution"]),
        "origine": (float(meta["origin"][0]), float(meta["origin"][1])),
        "ligne_centrale": np.loadtxt(centre, delimiter=",", comments="#", ndmin=2),
    }


def vers_monde(lignes: np.ndarray, colonnes: np.ndarray, carte: dict) -> tuple[np.ndarray, np.ndarray]:
    """Pixels de la carte vers mètres du simulateur."""
    res, (ox, oy) = carte["resolution"], carte["origine"]
    hauteur = carte["murs"].shape[0]
    return ox + colonnes * res, oy + (hauteur - 1 - lignes) * res


def vers_pixels(x: np.ndarray, y: np.ndarray, carte: dict) -> tuple[np.ndarray, np.ndarray]:
    """Mètres du simulateur vers pixels de la carte, bornés à l'image."""
    res, (ox, oy) = carte["resolution"], carte["origine"]
    hauteur, largeur = carte["murs"].shape
    lignes = np.rint(hauteur - 1 - (np.asarray(y) - oy) / res).astype(int)
    colonnes = np.rint((np.asarray(x) - ox) / res).astype(int)
    return np.clip(lignes, 0, hauteur - 1), np.clip(colonnes, 0, largeur - 1)


def masque_piste(carte: dict) -> np.ndarray:
    """La zone libre fermée par les murs qui contient la ligne centrale."""
    _, etiquettes = cv2.connectedComponents((~carte["murs"]).astype(np.uint8), connectivity=4)
    centre = carte["ligne_centrale"]
    lignes, colonnes = vers_pixels(centre[:, 0], centre[:, 1], carte)
    sous_la_ligne = etiquettes[lignes, colonnes]
    sous_la_ligne = sous_la_ligne[sous_la_ligne > 0]
    return etiquettes == np.bincount(sous_la_ligne).argmax()


def bords(piste: np.ndarray, carte: dict) -> list[list[float]]:
    """Contours de la piste en mètres, à plat (x0, y0, x1, y1…), le plus grand d'abord.

    Le premier est le bord extérieur, les suivants sont les trous (l'intérieur).
    """
    contours, _ = cv2.findContours(piste.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    resultat = []
    for contour in contours:
        points = cv2.approxPolyDP(contour, TOLERANCE_BORD_PX, closed=True)[:, 0, :]
        if len(points) < 3:
            continue
        x, y = vers_monde(points[:, 1], points[:, 0], carte)
        resultat.append(a_plat(np.column_stack([x, y])))
    return resultat


def arbres(piste: np.ndarray, carte: dict) -> list[float]:
    """Positions d'arbres tirées hors piste, ni trop près ni trop loin d'elle."""
    distance = cv2.distanceTransform((~piste).astype(np.uint8), cv2.DIST_L2, 5) * carte["resolution"]
    candidats = np.argwhere(
        ~carte["murs"] & ~piste
        & (distance > ARBRES_DISTANCE_MIN_M) & (distance < ARBRES_DISTANCE_MAX_M)
    )
    if len(candidats) == 0:
        return []
    tirage = np.random.default_rng(0).choice(len(candidats), min(NB_ARBRES, len(candidats)), replace=False)
    x, y = vers_monde(candidats[tirage, 0], candidats[tirage, 1], carte)
    return a_plat(np.column_stack([x, y]))


def cameras_tv(piste: np.ndarray, carte: dict) -> list[float]:
    """Postes de caméra au bord de la piste, un tous les `ECART_CAMERAS_TV_M` mètres.

    Chaque poste est posé sur le côté de la ligne centrale qui tombe hors piste.
    """
    centre = carte["ligne_centrale"]
    points = centre[:, :2]
    tangentes = np.roll(points, -1, axis=0) - points
    tangentes /= np.maximum(np.linalg.norm(tangentes, axis=1, keepdims=True), 1e-9)
    normales_gauche = np.column_stack([-tangentes[:, 1], tangentes[:, 0]])
    abscisse = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))])

    postes = []
    for i in np.searchsorted(abscisse, np.arange(0.0, abscisse[-1], ECART_CAMERAS_TV_M)):
        for cote, largeur in ((1.0, centre[i, 3]), (-1.0, centre[i, 2])):
            poste = points[i] + cote * normales_gauche[i] * (largeur + RECUL_CAMERAS_TV_M)
            ligne, colonne = vers_pixels(poste[0], poste[1], carte)
            if not piste[ligne, colonne] and not carte["murs"][ligne, colonne]:
                postes.append(poste)
                break
    return a_plat(np.array(postes)) if postes else []


def depart(carte: dict) -> dict:
    """Ligne de départ : premier point de la ligne centrale, sa direction et la largeur de piste."""
    centre = carte["ligne_centrale"]
    direction = centre[1, :2] - centre[0, :2]
    return {
        "x": round(float(centre[0, 0]), DECIMALES),
        "y": round(float(centre[0, 1]), DECIMALES),
        "angle": round(float(np.arctan2(direction[1], direction[0])), DECIMALES),
        "largeur": round(float(centre[0, 2] + centre[0, 3]), DECIMALES),
    }


def a_plat(tableau: np.ndarray) -> list[float]:
    """Un tableau numpy en liste de nombres arrondis, prête pour le JSON."""
    return np.round(np.asarray(tableau, dtype=np.float64), DECIMALES).ravel().tolist()


def voitures(episode) -> list[dict]:
    """Les séries temporelles de chaque voiture, une valeur par pas de simulation."""
    noms = [str(nom).strip() for nom in episode["team_names"]]
    resultat = []
    for i in range(int(episode["num_cars"])):
        resultat.append({
            "nom": noms[i] if i < len(noms) else f"Car_{i}",
            "poses": a_plat(episode["poses"][:, i]),
            "vitesse": a_plat(episode["velocity"][:, i]),
            "braquage": a_plat(episode["steering"][:, i]),
            "statut": episode["status"][:, i].astype(int).tolist(),
            "rang": episode["ranks"][:, i].astype(int).tolist(),
            "tours": episode["lap_count"][:, i].astype(int).tolist(),
            "progression": a_plat(episode["progress"][:, i]),
        })
    return resultat


def convertir(npz: Path) -> dict:
    """Une course `.npz` et sa carte, réunies dans un seul dictionnaire pour le visualiseur."""
    episode = np.load(npz)
    circuit = str(episode["map_name"]).strip()
    carte = lire_carte(circuit)
    piste = masque_piste(carte)
    return {
        "nom": npz.stem,
        "circuit": circuit,
        "dt": float(episode["sim_dt"]),
        "pas": int(episode["poses"].shape[0]),
        "carte": {
            "bords": bords(piste, carte),
            "ligne_centrale": a_plat(carte["ligne_centrale"][:, :2]),
            "arbres": arbres(piste, carte),
            "cameras_tv": cameras_tv(piste, carte),
            "depart": depart(carte),
        },
        "adherence": a_plat(episode["friction"]),
        "voitures": voitures(episode),
    }


def trace_allege(ligne_centrale: np.ndarray) -> list[float]:
    """La ligne centrale réduite à `POINTS_DU_TRACE` points environ, pour dessiner une miniature."""
    centre = np.asarray(ligne_centrale).reshape(-1, 2)
    return a_plat(centre[::max(1, len(centre) // POINTS_DU_TRACE)])


def fiche(course: dict) -> dict:
    """Le résumé d'une course pour l'écran d'accueil : circuit, pilotes, durée et tracé allégé."""
    return {
        "nom": course["nom"],
        "circuit": course["circuit"],
        "pilotes": [voiture["nom"] for voiture in course["voitures"]],
        "duree": round(course["pas"] * course["dt"], 1),
        "trace": trace_allege(course["carte"]["ligne_centrale"]),
    }


def mettre_a_jour_la_liste(dossier: Path, course: dict) -> list[dict]:
    """Ajoute ou remplace la fiche de `course` dans la liste, et retire les courses supprimées."""
    liste = dossier / LISTE_DES_COURSES
    try:
        anciennes = json.loads(liste.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        anciennes = []
    fiches = {
        f["nom"]: f for f in anciennes
        if isinstance(f, dict) and (dossier / f"{f.get('nom')}.json").exists()
    }
    fiches[course["nom"]] = fiche(course)
    resultat = [fiches[nom] for nom in sorted(fiches)]
    liste.write_text(json.dumps(resultat, separators=(",", ":")))
    return resultat


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nom", required=True, help="nom de la course dans recordings/, sans extension")
    args = parser.parse_args()

    course = convertir(RECORDINGS / f"{args.nom}.npz")
    sortie = RECORDINGS / f"{args.nom}.json"
    sortie.write_text(json.dumps(course, separators=(",", ":")))
    mettre_a_jour_la_liste(RECORDINGS, course)
    print(f"  {sortie} : {course['circuit']}, {len(course['voitures'])} voiture(s), {course['pas']} pas")
    print(f"  à voir avec : make visualiseur, puis choisir {args.nom}")


if __name__ == "__main__":
    main()
