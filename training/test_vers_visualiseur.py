"""Vérifie la conversion pour le visualiseur : `python -m training.test_vers_visualiseur` (`make test`).

Une erreur de repère (axe y inversé, mauvaise origine) poserait les voitures
dans les murs du visualiseur : ces tests la détectent sans ouvrir de navigateur.
"""

import json
import tempfile
from pathlib import Path

import numpy as np

from training import entrainements_vers_visualiseur as ev
from training import vers_visualiseur as vv

CIRCUITS = ("example", "Spa")


def test_aller_retour_pixels_monde():
    carte = vv.lire_carte("example")
    lignes, colonnes = np.array([0, 17, 800]), np.array([5, 400, 1200])
    x, y = vv.vers_monde(lignes, colonnes, carte)
    retour = vv.vers_pixels(x, y, carte)
    assert np.array_equal(retour[0], lignes) and np.array_equal(retour[1], colonnes)


def test_piste_fermee_autour_de_la_ligne_centrale():
    for circuit in CIRCUITS:
        carte = vv.lire_carte(circuit)
        piste = vv.masque_piste(carte)
        centre = carte["ligne_centrale"]
        lignes, colonnes = vv.vers_pixels(centre[:, 0], centre[:, 1], carte)
        assert piste[lignes, colonnes].mean() > 0.99, circuit
        assert piste.mean() < 0.2, f"{circuit} : la piste fuit hors des murs"


def test_bords_longent_les_murs():
    for circuit in CIRCUITS:
        carte = vv.lire_carte(circuit)
        bords = vv.bords(vv.masque_piste(carte), carte)
        assert len(bords) >= 2, circuit
        murs_proches = carte["murs"].copy()
        for decalage in ((0, 1), (0, -1), (1, 0), (-1, 0), (0, 2), (0, -2), (2, 0), (-2, 0)):
            murs_proches |= np.roll(carte["murs"], decalage, axis=(0, 1))
        for bord in bords:
            points = np.array(bord).reshape(-1, 2)
            lignes, colonnes = vv.vers_pixels(points[:, 0], points[:, 1], carte)
            assert murs_proches[lignes, colonnes].all(), circuit


def test_conversion_plusieurs_voitures():
    carte = vv.lire_carte("example")
    centre = carte["ligne_centrale"]
    pas, nb_voitures = 30, 3
    poses = np.zeros((pas, nb_voitures, 3), np.float32)
    for v in range(nb_voitures):
        poses[:, v, :2] = centre[v * 5:v * 5 + pas, :2]
    with tempfile.TemporaryDirectory() as dossier:
        npz = Path(dossier) / "factice.npz"
        np.savez(
            npz, poses=poses,
            velocity=np.ones((pas, nb_voitures)), steering=np.zeros((pas, nb_voitures)),
            status=np.ones((pas, nb_voitures), np.int32), ranks=np.ones((pas, nb_voitures), np.int32),
            lap_count=np.zeros((pas, nb_voitures), np.int32), progress=np.zeros((pas, nb_voitures)),
            friction=np.ones(pas), sim_dt=np.float32(0.05), num_cars=np.int32(nb_voitures),
            map_name=np.str_("example"), team_names=np.array(["a", "b", "c"], dtype="U10"),
        )
        course = json.loads(json.dumps(vv.convertir(npz)))
        Path(dossier, "factice.json").write_text("{}")
        Path(dossier, vv.LISTE_DES_COURSES).write_text(json.dumps([{"nom": "supprimee"}, "ancien format"]))
        fiches = vv.mettre_a_jour_la_liste(Path(dossier), course)
        assert [f["nom"] for f in fiches] == ["factice"]
        assert fiches[0]["circuit"] == "example" and fiches[0]["pilotes"] == ["a", "b", "c"]
        assert fiches[0]["duree"] == 1.5 and len(fiches[0]["trace"]) >= 6
    assert course["pas"] == pas and [v["nom"] for v in course["voitures"]] == ["a", "b", "c"]
    for voiture in course["voitures"]:
        assert len(voiture["poses"]) == 3 * pas and len(voiture["vitesse"]) == pas
    assert course["carte"]["arbres"] and course["carte"]["cameras_tv"]


def test_fiches_des_entrainements():
    config = {"pas": 1000, "ppo": {"gamma": 0.99}, "recompense": {"cout_temps": 0.01}, "circuits_eval": ["example"]}
    bilan = {"course/taux_completion": 0.5, "tour/meilleur": 31.9}
    with tempfile.TemporaryDirectory() as racine:
        archives, brouillon = Path(racine, "archives"), Path(racine, "runs")
        for dossier, date in ((archives / "driver1-a-ppo", "2026-11-01T10:00:00"), (brouillon / "driver1-b-ppo", "2026-11-02T10:00:00")):
            (dossier / "sauvegardes").mkdir(parents=True)
            meta = {"pilote": "driver1", "algo": "ppo", "date": date, "circuits": ["Spa", "inconnu"], "config": config}
            (dossier / "meta.json").write_text(json.dumps(meta))
            (dossier / "bilan.json").write_text(json.dumps(bilan))
        (archives / "driver1-a-ppo" / "note.md").write_text("# driver1-a-ppo\n\nPremier tour bouclé.\n")
        for pas in (200000, 100000):
            (brouillon / "driver1-b-ppo" / "sauvegardes" / f"model_{pas}_steps.zip").write_text("")
        (brouillon / "sans-meta").mkdir()
        donnees = json.loads(json.dumps(ev.exporter((("archive", archives), ("local", brouillon)))))
    recent, ancien = donnees["runs"]
    assert [recent["nom"], ancien["nom"]] == ["driver1-b-ppo", "driver1-a-ppo"]
    assert [recent["origine"], ancien["origine"]] == ["local", "archive"]
    assert recent["config"] == config and recent["bilan"] == bilan
    assert recent["sauvegardes"] == [100000, 200000] and ancien["sauvegardes"] == []
    assert ancien["note"] == "Premier tour bouclé." and recent["note"] == ""
    assert recent["courbes"] == {} and recent["circuits_eval"] == ["example"]
    assert sorted(donnees["circuits"]) == ["Spa", "example"]


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
            print(f"  PASS  {nom}")
