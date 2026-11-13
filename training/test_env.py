"""Vérifie le MDP v1 : `python -m training.test_env` dans le conteneur (`make test`)."""

import os
import tempfile
from pathlib import Path

import numpy as np
from gymnasium.utils.env_checker import check_env

from training import config, features
from training.env import RECOMPENSE_DEFAUT, CourseSolo, parametres_recompense


def test_secteurs_gauche_droite():
    # Mur proche à gauche seulement (rayons > 50) : les secteurs de fin de
    # vecteur doivent être bas, ceux du début hauts.
    lidar = np.full(100, 15.0, dtype=np.float32)
    lidar[60:77] = 0.5
    obs = {"lidar": lidar, "velocity": 0.0, "steering": 0.0}
    secteurs = features.observation(obs, np.zeros(2, np.float32))[:18]
    assert secteurs[-1] < 0.5 and secteurs[0] == 1.0


def test_commande_bornee():
    assert features.commande(np.array([-5.0, -5.0])) == (0.0, -features.BRAQUAGE_MAX)
    assert features.commande(np.array([1.0, 1.0])) == (features.VITESSE_MAX, features.BRAQUAGE_MAX)


def test_chargement_comme_agent():
    # agent.py ne peut pas importer features : il l'exécute depuis son dossier.
    # Le résultat doit être identique au module importé.
    espace: dict = {}
    with open(os.path.join(os.path.dirname(features.__file__), "features.py")) as f:
        exec(f.read(), espace)
    obs = {"lidar": np.linspace(0.1, 15, 100), "velocity": 3.0, "steering": 0.2}
    a = np.array([0.3, -0.7], np.float32)
    assert np.array_equal(espace["observation"](obs, a), features.observation(obs, a))


def test_episodes():
    env = CourseSolo(circuits=("example", "Montreal"), pas_max=300)
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
    # Les poids du MDP v1 : sans surcharge, la récompense n'a pas changé.
    assert parametres_recompense() == {
        "cout_temps": 0.01, "poids_douceur": 0.05, "penalite_choc": 2.0, "penalite_dnf": 10.0}
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
        CourseSolo._instances = 0     # le garde-fou vise deux environnements simultanés, pas ceux-ci
        env = CourseSolo(circuits=("example",), pas_max=50, recompense=poids)
        env.reset(seed=0, options={"circuit": "example"})
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
    # Les quatre fichiers livrés se chargent et laissent le MDP v1 intact : seuls la
    # graine (et le nombre d'environnements du run de référence) les distinguent.
    graines = set()
    for pilote in ("driver1", "driver2", "driver3", "driver4"):
        cfg, fichier = config.charger(pilote)
        assert fichier is not None, pilote
        assert parametres_recompense(cfg["recompense"]) == RECOMPENSE_DEFAUT, pilote
        assert cfg["ppo"] == config.DEFAUTS["ppo"] and cfg["env"] == config.DEFAUTS["env"], pilote
        graines.add(cfg["graine"])
    assert len(graines) == 4, graines


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
            print(f"  PASS  {nom}")
