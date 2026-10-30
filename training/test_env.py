"""Vérifie le MDP v1 : `python -m training.test_env` dans le conteneur (`make test`)."""

import os

import numpy as np
from gymnasium.utils.env_checker import check_env

from training import features
from training.env import CourseSolo


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


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
            print(f"  PASS  {nom}")
