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
from f110_gym.envs import laser_models
from training import features
from training.metrics import ACTIF, ARRIVE, DNF


def _get_dt_memorise(get_dt):
    """`sim.reset()` reconstruit le simulateur et recalcule à chaque fois la carte
    des distances aux murs : 0,19 s sur 0,23 s de reset, 80 % du temps
    d'entraînement au début, quand les épisodes durent quelques dizaines de pas.
    Elle ne dépend que du circuit chargé : on garde la dernière, ce qui suffit
    puisqu'un environnement reste plusieurs épisodes sur le même circuit. Le
    résultat est identique, on ne touche à aucun fichier d'Epitech."""
    derniere = {}

    def get_dt_memorise(bitmap, resolution):
        cle = (sim.get_current_map(), bitmap.shape, resolution)
        if derniere.get("cle") != cle:
            derniere.update(cle=cle, dt=get_dt(bitmap, resolution))
        return derniere["dt"]

    return get_dt_memorise


laser_models.get_dt = _get_dt_memorise(laser_models.get_dt)

COUT_TEMPS = 0.01       # par pas : la lenteur coûte
POIDS_DOUCEUR = 0.05     # × variation de braquage, secondaire devant la progression
PENALITE_CHOC = 2.0
PENALITE_DNF = 10.0

# Séparation des circuits, figée une fois pour toutes (protocole d'entraînement) :
# la généralisation se mesure sur VALIDATION, et on ne règle jamais rien sur TEST.
# Validation et test couvrent un court (Oschersleben, 261 m), un long (Spa, 554 m)
# et des largeurs de 2,0 à 2,6 m. Montreal, le plus étroit (1,39 m), reste à
# l'entraînement : sans lui, rien n'apprend les pistes à moins de 2 m.
# `example` est réservé au débogage.
VALIDATION = ("Oschersleben", "Zandvoort", "MexicoCity")
TEST = ("Spa", "Budapest", "Sochi")
# Changer de circuit reconstruit le simulateur (~0,4 s). Au début, un épisode
# dure 2 à 3 s de simulation : changer à chaque épisode divisait la vitesse
# d'entraînement par 6. Chaque environnement garde donc son circuit plusieurs
# épisodes ; la variété vient des 8 environnements en parallèle.
EPISODES_PAR_CIRCUIT = 20

ENTRAINEMENT = tuple(sorted(set(sim.get_available_maps()) - set(VALIDATION) - set(TEST) - {"example"}))


class CourseSolo(gym.Env):
    """Une voiture, un circuit tiré au hasard parmi `circuits` tous les
    `EPISODES_PAR_CIRCUIT` épisodes,
    sauf si `reset(options={"circuit": ...})` l'impose (évaluation)."""

    _instances = 0

    def __init__(self, circuits: list[str] | tuple[str, ...] = ("example",),
                 pas_max: int = 3000, fin_sur_choc: bool = True):
        CourseSolo._instances += 1
        if CourseSolo._instances > 1:
            raise RuntimeError("un seul CourseSolo par processus : utiliser SubprocVecEnv")

        self.circuits = list(circuits)
        self.pas_max = pas_max
        # Terminer sur un choc rend le mur très coûteux : la politique apprend à
        # ne jamais le toucher. Sans ça (essayé sur 1M de pas, 17 circuits), un
        # choc ne coûte que -2 : elle fonce à 8 m/s, finit collée à un mur sans
        # marche arrière pour s'en dégager, et se fait éliminer pour stagnation.
        # Prix : plus de reset(), 376 pas/s au lieu de 758 sur 8 environnements.
        self.fin_sur_choc = fin_sur_choc
        self._episodes = 0

        self.observation_space = gym.spaces.Box(-1.5, 1.5, (features.TAILLE_OBSERVATION,), np.float32)
        self.action_space = gym.spaces.Box(-1.0, 1.0, (2,), np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        circuit = (options or {}).get("circuit")
        if circuit is None:
            if self._episodes % EPISODES_PAR_CIRCUIT == 0:
                self._circuit = self.circuits[self.np_random.integers(len(self.circuits))]
            self._episodes += 1
            circuit = self._circuit
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
