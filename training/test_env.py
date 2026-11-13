"""Vérifie le MDP v2 : `python -m training.test_env` dans le conteneur (`make test`)."""

import os
import tempfile
from pathlib import Path

import numpy as np
import env_simulation as sim
from gymnasium.utils.env_checker import check_env

from training import config, features
from training.env import RECOMPENSE_DEFAUT, Course, parametres_recompense


def test_secteurs_gauche_droite():
    # Mur proche à gauche seulement (rayons > 50) : les secteurs de fin de
    # vecteur doivent être bas, ceux du début hauts.
    lidar = np.full(100, 15.0, dtype=np.float32)
    lidar[60:77] = 0.5
    obs = {"lidar": lidar, "velocity": 0.0, "steering": 0.0}
    secteurs = features.observation(obs, {}, np.zeros(2, np.float32))[:18]
    assert secteurs[-1] < 0.5 and secteurs[0] == 1.0


def test_commande_bornee():
    assert features.commande(np.array([-5.0, -5.0])) == (features.VITESSE_MIN, -features.BRAQUAGE_MAX)
    assert features.commande(np.array([1.0, 1.0])) == (features.VITESSE_MAX, features.BRAQUAGE_MAX)


def test_chargement_comme_agent():
    # agent.py ne peut pas importer features : il l'exécute depuis son dossier.
    # Le résultat doit être identique au module importé.
    espace: dict = {}
    with open(os.path.join(os.path.dirname(features.__file__), "features.py")) as f:
        exec(f.read(), espace)
    obs = {"lidar": np.linspace(0.1, 15, 100), "velocity": 3.0, "steering": 0.2, "opponents": {
        0: {"x_rel": 0.0, "y_rel": 0.0, "yaw_rel": 0.0, "speed": 0.0, "status": 0},
        1: {"x_rel": 30.0, "y_rel": -1.0, "yaw_rel": 0.1, "speed": 5.0, "status": 1},
        2: {"x_rel": 2.0, "y_rel": 0.5, "yaw_rel": -0.2, "speed": 4.0, "status": 1}}}
    info = {"friction_current": 0.7}
    a = np.array([0.3, -0.7], np.float32)
    x = features.observation(obs, info, a)
    assert np.array_equal(espace["observation"](obs, info, a), x)
    assert x.shape == (features.TAILLE_OBSERVATION,) and np.all(np.abs(x) <= 1.5)
    # le plus proche d'abord, x écrêté à la portée, le troisième absent
    adv = x[-15:].reshape(3, 5)
    assert adv[0, 0] == 1 and np.isclose(adv[0, 1], 0.2) and adv[1, 1] == 1.0 and adv[2, 0] == 0


def test_meteo():
    # Sous la pluie, l'adhérence change dès le premier pas et se lit dans step_info.
    Course._instances = 0     # le garde-fou vise deux environnements simultanés, pas ceux-ci
    env = Course(circuits=("example",), pas_max=50)
    frictions = set()
    for graine in range(6):
        env.reset(seed=graine, options={"circuit": "example", "meteo": True})
        env.step(np.zeros(2, np.float32))
        frictions.add(round(sim.get_step_info()["friction_current"], 3))
    assert len(frictions) > 1 and all(0.5 <= f <= 1.0 for f in frictions), frictions
    env.reset(seed=0, options={"circuit": "example", "meteo": False})
    env.step(np.zeros(2, np.float32))
    assert sim.get_step_info()["friction_current"] == 1.0


def test_episodes():
    Course._instances = 0
    env = Course(circuits=("example", "Montreal"), pas_max=300)
    check_env(env, skip_render_check=True)

    rng = np.random.default_rng(0)
    fins = set()
    for graine, circuit in enumerate(["example", "Montreal", "Montreal", "example"]):
        obs, info = env.reset(seed=graine, options={"circuit": circuit})
        fins.add(info["circuit"])
        termine = tronque = False
        while not (termine or tronque):
            obs, r, termine, tronque, _ = env.step(rng.uniform(-1, 1, 2).astype(np.float32))
            assert env.observation_space.contains(obs), obs
            assert np.isfinite(r)
    assert fins == {"example", "Montreal"}, fins


def test_recompense_par_defaut():
    assert parametres_recompense() == {"cout_temps": 0.01, "poids_douceur": 0.05, "penalite_choc": 2.0,
                                       "penalite_contact": 1.0, "penalite_dnf": 10.0}
    assert parametres_recompense({"penalite_choc": 5.0}) == {**RECOMPENSE_DEFAUT, "penalite_choc": 5.0}
    try:
        parametres_recompense({"penalite_chocs": 5.0})      # faute de frappe
    except ValueError:
        pass
    else:
        raise AssertionError("une clé inconnue doit être refusée")


def test_recompense_parametree():
    # Un poids surchargé change la récompense de son seul montant.
    def recompenses(poids):
        Course._instances = 0     # le garde-fou vise deux environnements simultanés, pas ceux-ci
        env = Course(circuits=("example",), pas_max=50, recompense=poids)
        env.reset(seed=0, options={"circuit": "example", "meteo": False})
        sortie = []
        for _ in range(5):
            _, r, termine, tronque, _ = env.step(np.zeros(2, np.float32))
            assert not (termine or tronque)
            sortie.append(r)
        return np.array(sortie)

    assert np.allclose(recompenses(None) - recompenses({"cout_temps": 0.51}), 0.5, atol=1e-6)


def test_config_priorite():
    with tempfile.TemporaryDirectory() as dossier:
        fichier = Path(dossier) / "pilote.yaml"
        fichier.write_text("graine: 7\nppo:\n  gamma: 0.9\nrecompense:\n  penalite_choc: 3.0\n")
        cfg, lu = config.charger("x", fichier)
        assert lu == fichier and cfg["graine"] == 7 and cfg["pas"] == config.DEFAUTS["pas"]
        assert cfg["ppo"] == {**config.DEFAUTS["ppo"], "gamma": 0.9}
        assert cfg["recompense"] == {"penalite_choc": 3.0}
        # la ligne de commande l'emporte, une option non donnée (None) laisse la main au fichier
        cfg, _ = config.charger("x", fichier, {"graine": 9, "pas": None})
        assert cfg["graine"] == 9 and cfg["pas"] == config.DEFAUTS["pas"]
    cfg, lu = config.charger("pilote-sans-fichier")
    assert lu is None and cfg == config.DEFAUTS


def test_config_refuse_les_fautes():
    with tempfile.TemporaryDirectory() as dossier:
        for texte in ("pas_total: 5\n", "graine: abc\n", "pas: 1.5\n", "env:\n  pas_maxi: 3\n", "- 1\n- 2\n"):
            fichier = Path(dossier) / "mauvais.yaml"
            fichier.write_text(texte)
            try:
                config.charger("x", fichier)
            except ValueError:
                continue
            raise AssertionError(f"à refuser : {texte!r}")
    try:
        config.charger("x", "introuvable.yaml")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("un --config introuvable doit être refusé")


def test_configs_des_pilotes():
    # Les fichiers livrés se chargent, sans clé inconnue ; chacun est libre de ses réglages.
    for pilote in ("driver1", "driver2", "driver3", "driver4", "champion"):
        cfg, fichier = config.charger(pilote)
        assert fichier is not None, pilote
        parametres_recompense(cfg["recompense"])


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
            print(f"  PASS  {nom}")
