"""Environnement Gymnasium autour du simulateur, pour une voiture seule (MDP v1).

Le simulateur n'a ni `done` ni récompense : tout ce qui fait un MDP est décidé
ici, selon le document Linear « Formalisme MDP et fonction de récompense »
(section « Décisions v1 »). Le prétraitement, lui, vit dans `features.py`,
partagé avec `agent.py`.

Le simulateur est un **état global du module** `env_simulation` : un seul
environnement par processus. Pour en faire tourner plusieurs, passer par
`SubprocVecEnv`, jamais `DummyVecEnv` — les deux instances se partageraient la
même voiture sans erreur.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

import env_simulation as sim
from training import features
from training.metrics import ACTIF, ARRIVE, DNF

COUT_TEMPS = 0.01        # par pas : la lenteur coûte
POIDS_DOUCEUR = 0.05     # × variation de braquage, secondaire devant la progression
PENALITE_CHOC = 2.0
PENALITE_DNF = 10.0


class CourseSolo(gym.Env):
    """Une voiture, un circuit tiré au hasard à chaque `reset()` parmi `circuits`."""

    _instances = 0

    def __init__(self, circuits: list[str] | tuple[str, ...] = ("example",),
                 pas_max: int = 3000, fin_sur_choc: bool = True):
        CourseSolo._instances += 1
        if CourseSolo._instances > 1:
            raise RuntimeError("un seul CourseSolo par processus : utiliser SubprocVecEnv")

        self.circuits = list(circuits)
        self.pas_max = pas_max
        # Terminer sur un choc accélère l'apprentissage au début, mais l'agent
        # n'apprend jamais à se dégager d'un mur : à couper plus tard.
        self.fin_sur_choc = fin_sur_choc

        self.observation_space = gym.spaces.Box(-1.5, 1.5, (features.TAILLE_OBSERVATION,), np.float32)
        self.action_space = gym.spaces.Box(-1.0, 1.0, (2,), np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        circuit = self.circuits[self.np_random.integers(len(self.circuits))]
        if circuit != (sim.get_current_map() or "example"):
            sim.set_map(circuit)   # reconstruit le simulateur : seulement si le circuit change
        sim.reset(num_cars=1, seed=int(self.np_random.integers(2**31)))

        # Longueur exacte utilisée par le moteur pour `progress_delta`, qu'on
        # convertit en mètres : sans ça, un mètre vaudrait deux fois moins sur
        # Spa (554 m) que sur Oschersleben (261 m).
        self._longueur = sim._get_sim()._total_arc
        self._pas = 0
        self._action_precedente = np.zeros(2, dtype=np.float32)
        self._obs = features.observation(sim.get_obs(0), self._action_precedente)
        return self._obs, {"circuit": circuit}

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        sim.apply_action(0, *features.commande(action))
        sim.simulation_step()
        info = sim.get_step_info()
        statut = info["agent_status"][0]
        choc = bool(info["collisions"]["wall"][0])

        recompense = (info["progress_delta"][0] * self._longueur
                      - COUT_TEMPS
                      - POIDS_DOUCEUR * abs(action[1] - self._action_precedente[1]))
        if choc:
            recompense -= PENALITE_CHOC
        if statut == DNF:
            recompense -= PENALITE_DNF

        self._pas += 1
        terminated = statut != ACTIF or (choc and self.fin_sur_choc)
        truncated = not terminated and self._pas >= self.pas_max

        # Jamais de get_obs() sur une voiture gelée : sa pose devient le sentinel
        # hors piste (~10 000 m) et l'observation n'a plus de sens. On garde la
        # dernière, que la fin d'épisode rend sans importance.
        self._action_precedente = action
        if statut == ACTIF:
            self._obs = features.observation(sim.get_obs(0), action)

        return self._obs, float(recompense), terminated, truncated, {
            "statut": statut,
            "choc": choc,
            "arrivee": statut == ARRIVE,
            "stagnation": bool(info["stagnation"][0]),
        }
