"""Environnement Gymnasium autour du simulateur (MDP v2).

Le simulateur n'a ni `done` ni récompense : tout ce qui fait un MDP est décidé
ici, selon le document Linear « Formalisme MDP et fonction de récompense ». Le
prétraitement, lui, vit dans `features.py`, partagé avec `agent.py`.

Une voiture apprend (`ego`). Elle roule seule (pilotes driver1 à driver4) ou
avec jusqu'à trois adversaires figés (champion), pilotés par des dossiers de
`submission/` chargés comme au tournoi.

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


# --- météo -------------------------------------------------------------------
# Le sujet annonce de la pluie au tournoi : adhérence instable et LiDAR bruité.
# Le simulateur fourni les laisse figés (deux TODO dans `_update_friction` et
# `_update_lidar_noise`) : au sec, μ = 1 et bruit ±0,1 %. Ses constantes donnent
# les bornes : μ de 1 (sec) à 0,5 (forte pluie), bruit de ±0,1 % à ±10 %, un
# changement toutes les 20 s. On remplace ces deux méthodes dans le processus
# d'entraînement seulement, sans toucher à aucun fichier d'Epitech : le pilote
# apprend sous un ciel changeant, et lit l'adhérence dans `friction_current`.
BRUIT_SEC, BRUIT_PLUIE = sim._LIDAR_NOISE, 0.1


def _changer_temps(s) -> None:
    """Nouveau temps : une adhérence et un bruit LiDAR liés, de sec à forte pluie."""
    pluie = float(s._rng.uniform()) ** 2 if s._rng.uniform() < 0.7 else 0.0   # sec 30 % du temps
    s._friction = features.FRICTION_SEC - pluie * (features.FRICTION_SEC - features.FRICTION_PLUIE)
    s._bruit = BRUIT_SEC + pluie * (BRUIT_PLUIE - BRUIT_SEC)
    s._pluie = pluie
    p = dict(sim._PARAMS)
    p["mu"] = s._friction
    s._sim.update_params(p, agent_idx=-1)


def _update_friction(s) -> None:
    if not getattr(s, "meteo", False):
        return
    s._friction_countdown -= 1
    if s._friction_countdown <= 0 or s._step_count == 1:   # dès le départ, pas seulement après 20 s
        _changer_temps(s)
        s._friction_countdown = s._next_friction_steps()


def _update_lidar_noise(s) -> None:
    if not getattr(s, "meteo", False) or not hasattr(s, "_bruit"):
        s._last_scan_noise = s._rng.uniform(-BRUIT_SEC, BRUIT_SEC, size=sim._LIDAR_RAYS)
        return
    bruit = s._rng.uniform(-s._bruit, s._bruit, size=sim._LIDAR_RAYS)
    # « Rayons LiDAR corrompus » : sous forte pluie, jusqu'à 5 % des rayons
    # décrochent à chaque pas, à la portée minimale ou maximale (après écrêtage).
    casses = s._rng.uniform(size=sim._LIDAR_RAYS) < 0.05 * s._pluie
    bruit[casses] = np.where(s._rng.uniform(size=int(casses.sum())) < 0.5, -1.0, 1e3)
    s._last_scan_noise = bruit


sim._Sim._update_friction = _update_friction
sim._Sim._update_lidar_noise = _update_lidar_noise


# --- récompense --------------------------------------------------------------
# Valeurs du MDP v2, et clés que `training/configs/<pilote>.yaml` peut surcharger.
RECOMPENSE_DEFAUT = {
    "cout_temps": 0.01,        # par pas : la lenteur coûte
    "poids_douceur": 0.05,     # × variation de braquage, secondaire devant la progression
    "penalite_choc": 2.0,      # contre un mur
    "penalite_contact": 1.0,   # contre une autre voiture
    "penalite_dnf": 10.0,
}


def parametres_recompense(surcharges: dict | None = None) -> dict:
    """Poids de la récompense : ceux du MDP v2, surchargés clé par clé.

    Une clé inconnue est une faute de frappe dans un fichier de configuration :
    elle lèverait sinon aucune erreur, et le run partirait avec le poids par défaut."""
    inconnues = set(surcharges or {}) - set(RECOMPENSE_DEFAUT)
    if inconnues:
        raise ValueError(f"poids de récompense inconnus : {sorted(inconnues)} "
                         f"(attendus : {sorted(RECOMPENSE_DEFAUT)})")
    return {**RECOMPENSE_DEFAUT, **(surcharges or {})}


# --- circuits ----------------------------------------------------------------
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


class Course(gym.Env):
    """Une voiture qui apprend, un circuit tiré au hasard parmi `circuits` tous
    les `EPISODES_PAR_CIRCUIT` épisodes, sauf si `reset(options={"circuit": ...})`
    l'impose (évaluation).

    `adversaires` : dossiers pilotes (`submission/driverN`). À chaque épisode,
    de 0 à `len(adversaires)` d'entre eux prennent le départ, et la voiture qui
    apprend tire sa place sur la grille."""

    _instances = 0

    def __init__(self, circuits: list[str] | tuple[str, ...] = ("example",),
                 pas_max: int = 3000, fin_sur_choc: bool = True, meteo: bool = True,
                 adversaires: list[str] | tuple[str, ...] = (), recompense: dict | None = None):
        Course._instances += 1
        if Course._instances > 1:
            raise RuntimeError("un seul Course par processus : utiliser SubprocVecEnv")

        self.circuits = list(circuits)
        self.pas_max = pas_max
        self.recompense = parametres_recompense(recompense)
        # Terminer sur un choc rend le mur très coûteux : la politique apprend à
        # ne jamais le toucher. Sans ça (essayé sur 1M de pas, 17 circuits, sans
        # marche arrière), un choc ne coûte que -2 : elle fonce, finit collée à un
        # mur, et se fait éliminer pour stagnation.
        self.fin_sur_choc = fin_sur_choc
        self.meteo = meteo
        self._episodes = 0
        self._adversaires = []
        if adversaires:
            from agent_loader import validate_and_load_agent   # outil d'Epitech, chargé comme au tournoi
            self._adversaires = [validate_and_load_agent(d)[1] for d in adversaires]

        self.observation_space = gym.spaces.Box(-1.5, 1.5, (features.TAILLE_OBSERVATION,), np.float32)
        self.action_space = gym.spaces.Box(-1.0, 1.0, (2,), np.float32)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        options = options or {}
        circuit = options.get("circuit")
        if circuit is None:
            if self._episodes % EPISODES_PAR_CIRCUIT == 0:
                self._circuit = self.circuits[self.np_random.integers(len(self.circuits))]
            self._episodes += 1
            circuit = self._circuit
        if circuit != (sim.get_current_map() or "example"):
            sim.set_map(circuit)   # reconstruit le simulateur : seulement si le circuit change

        nb_adv = options.get("adversaires",
                             int(self.np_random.integers(len(self._adversaires) + 1)))
        voitures = 1 + nb_adv
        self._ego = int(self.np_random.integers(voitures))
        autres = [s for s in range(voitures) if s != self._ego]
        ordre = self.np_random.permutation(len(self._adversaires))[:nb_adv]
        self._pilotes = {slot: self._adversaires[i] for slot, i in zip(autres, ordre)}

        sim.reset(num_cars=voitures, seed=int(self.np_random.integers(2**31)))
        sim._get_sim().meteo = options.get("meteo", self.meteo)

        # Longueur exacte utilisée par le moteur pour `progress_delta`, qu'on
        # convertit en mètres : sans ça, un mètre vaudrait deux fois moins sur
        # Spa (554 m) que sur Oschersleben (261 m).
        self._longueur = sim._get_sim()._total_arc
        self._pas = 0
        self._info = sim.get_step_info()
        for pilote in self._pilotes.values():
            pilote.action_precedente = np.zeros(2, dtype=np.float32)
        self._action_precedente = np.zeros(2, dtype=np.float32)
        self._obs = features.observation(sim.get_obs(self._ego), self._info, self._action_precedente)
        return self._obs, {"circuit": circuit, "ego": self._ego, "adversaires": nb_adv}

    def step(self, action):
        action = np.clip(action, -1.0, 1.0).astype(np.float32)
        sim.apply_action(self._ego, *features.commande(action))
        for slot, pilote in self._pilotes.items():
            if self._info["agent_status"][slot] == ACTIF:
                sim.apply_action(slot, *pilote.predict(sim.get_obs(slot), self._info))
        sim.simulation_step()
        info = self._info = sim.get_step_info()
        ego = self._ego
        statut = info["agent_status"][ego]
        choc = bool(info["collisions"]["wall"][ego])
        contact = bool(info["collisions"]["vehicle"][ego])

        poids = self.recompense
        recompense = (info["progress_delta"][ego] * self._longueur
                      - poids["cout_temps"]
                      - poids["poids_douceur"] * abs(action[1] - self._action_precedente[1]))
        if choc:
            recompense -= poids["penalite_choc"]
        if contact:
            recompense -= poids["penalite_contact"]
        if statut == DNF:
            recompense -= poids["penalite_dnf"]

        self._pas += 1
        terminated = statut != ACTIF or (choc and self.fin_sur_choc)
        truncated = not terminated and self._pas >= self.pas_max

        # Jamais de get_obs() sur une voiture gelée : sa pose devient le sentinel
        # hors piste (~10 000 m) et l'observation n'a plus de sens. On garde la
        # dernière, que la fin d'épisode rend sans importance.
        self._action_precedente = action
        if statut == ACTIF:
            self._obs = features.observation(sim.get_obs(ego), info, action)

        return self._obs, float(recompense), terminated, truncated, {
            "statut": statut,
            "choc": choc,
            "contact": contact,
            "arrivee": statut == ARRIVE,
            "stagnation": bool(info["stagnation"][ego]),
        }
