"""map_api.py — Relève les bornes réelles de get_obs() / get_step_info() (CRA-6).

Fait tourner plusieurs voitures aux comportements variés (suivi de trajectoire,
volant erratique, fonceur sur adversaire, aléatoire) sur plusieurs circuits, pour
provoquer collisions, sorties de piste et arrivées, et observer les vraies bornes
de chaque clé — pas seulement celles écrites dans les docstrings ou get_space_info().

La boucle respecte l'ordre imposé par le simulateur : apply_action() pour chaque
agent, puis un seul simulation_step(), puis un seul get_step_info(), puis get_obs()
par agent — voir la fonction run_map() plus bas, qui EST la vérification de CRA-6
("un script court" qui vérifie cet ordre).

Usage (depuis la racine du dépôt, dans le conteneur) :
    docker compose run --rm sim python training/tools/map_api.py
    docker compose run --rm sim python training/tools/map_api.py --steps 2000 --maps example,Monza,Montreal

Par défaut les pilotes de test sont commandés entre 2 et 6 m/s : les bornes de vitesse
mesurées sont alors celles de ces pilotes, pas du simulateur. Pour mesurer le vrai
plafond, imposer la même vitesse à toutes les voitures :
    ... map_api.py --speed 10     # plafond annoncé par le simulateur
    ... map_api.py --speed 20     # au-delà : vérifie que l'écrêtage à 10 m/s tient
"""

import argparse
import math
import os
import sys

for _candidate in (os.getcwd(), os.path.join(os.getcwd(), "simulation")):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

import numpy as np

import env_simulation as sim_mod
from env_simulation import (
    _PARAMS,
    apply_action,
    close,
    get_available_maps,
    get_obs,
    get_space_info,
    get_step_info,
    reset,
    set_map,
    simulation_step,
    _get_sim,
)

DEFAULT_MAPS = ["example", "Monza", "Montreal"]

_CONSTANT_NAMES = [
    "_FREQ_HZ", "_DECISION_FREQ_HZ", "_PHYSICS_STEPS",
    "_FRICTION_LO", "_FRICTION_HI", "_FRICTION_INTERVAL_SEC",
    "_DNF_WINDOW_SEC", "_DNF_MIN_GAIN_M", "_OFFTRACK_MARGIN_M", "_DEFAULT_HALF_WIDTH_M",
    "_TARGET_SPEED_MIN", "_TARGET_SPEED_MAX", "_VEL_OBS_MIN", "_VEL_OBS_MAX",
    "_LIDAR_RAYS", "_LIDAR_FOV", "_LIDAR_SCAN_FOV", "_LIDAR_NOISE", "_LIDAR_MIN", "_LIDAR_MAX",
    "_TTC_THRESH", "_MAX_SLOTS", "_REQUIRED_LAPS",
    "_KNOCKBACK_REST", "_KNOCKBACK_MAX_M", "_KNOCKBACK_MIN_SHARE",
    "_WALL_REST", "_WALL_REST_MAX", "_DNF_WINDOW_STEPS",
    "_GRID_LAT_M", "_GRID_ROW_M",
]


class Bounds:
    """Min/max glissants pour une clé scalaire, plus un compteur d'observations."""

    def __init__(self):
        self.lo = math.inf
        self.hi = -math.inf
        self.n = 0

    def see(self, v):
        v = float(v)
        self.lo = min(self.lo, v)
        self.hi = max(self.hi, v)
        self.n += 1

    def __repr__(self):
        if self.n == 0:
            return "(jamais observé)"
        return f"[{self.lo:.5f}, {self.hi:.5f}]  (n={self.n})"


def _pure_pursuit_steer(x, y, yaw, waypoints, arc, total_arc, lookahead=1.0):
    """Suivi de trajectoire minimal — copie simplifiée de sim_recorder.py, en
    lecture seule sur les waypoints de la _Sim courante."""
    dists = (waypoints[:, 0] - x) ** 2 + (waypoints[:, 1] - y) ** 2
    idx = int(np.argmin(dists))
    n = len(waypoints)
    cum, target_idx = 0.0, idx
    for i in range(1, n):
        wi, wj = (idx + i) % n, (idx + i - 1) % n
        dx_w = waypoints[wi, 0] - waypoints[wj, 0]
        dy_w = waypoints[wi, 1] - waypoints[wj, 1]
        cum += math.hypot(dx_w, dy_w)
        if cum >= lookahead:
            target_idx = wi
            break
    tx, ty = waypoints[target_idx, 0], waypoints[target_idx, 1]
    angle_diff = math.atan2(ty - y, tx - x) - yaw
    angle_diff = math.atan2(math.sin(angle_diff), math.cos(angle_diff))
    return max(_PARAMS["s_min"], min(_PARAMS["s_max"], angle_diff))


def _policy(car_id, step_i, obs, sim_obj):
    """Un comportement différent par voiture, choisi pour provoquer un maximum
    de cas limites (mur, collision, arrivée, stagnation) en peu de pas."""
    state = sim_obj._sim.agents[car_id].state
    x, y, yaw = float(state[0]), float(state[1]), float(state[4])

    if car_id == 0:
        steer = _pure_pursuit_steer(x, y, yaw, sim_obj._waypoints, sim_obj._arc, sim_obj._total_arc)
        return 3.0, steer

    if car_id == 1:
        steer = _pure_pursuit_steer(x, y, yaw, sim_obj._waypoints, sim_obj._arc, sim_obj._total_arc)
        steer += 0.35 * math.sin(step_i * 0.5)
        return 6.0, max(_PARAMS["s_min"], min(_PARAMS["s_max"], steer))

    if car_id == 2:
        opp0 = obs["opponents"][0]
        if opp0["status"] == 1:
            steer = max(_PARAMS["s_min"], min(_PARAMS["s_max"], math.atan2(opp0["y_rel"], opp0["x_rel"])))
        else:
            steer = _pure_pursuit_steer(x, y, yaw, sim_obj._waypoints, sim_obj._arc, sim_obj._total_arc)
        return 4.0, steer

    return 2.0, 0.08 * math.sin(step_i * 0.12)


def run_map(map_name, steps, num_cars, seed, report, speed_override=None):
    set_map(map_name)
    reset(num_cars=num_cars, seed=seed)
    sim_obj = _get_sim()

    obs_list = [get_obs(i) for i in range(num_cars)]
    last_info = None

    for step_i in range(steps):
        for cid in range(num_cars):
            speed, steer = _policy(cid, step_i, obs_list[cid], sim_obj)
            if speed_override is not None:
                speed = speed_override
            if last_info is None or last_info["agent_status"][cid] == 1:
                report.see_command(speed)
            apply_action(cid, speed, steer)
        simulation_step()
        info = get_step_info()
        assert info["step_count"] == step_i + 1, (
            f"ordre de boucle rompu : step_count={info['step_count']} attendu={step_i + 1}"
        )
        obs_list = [get_obs(i) for i in range(num_cars)]

        for cid in range(num_cars):
            prev = 1 if last_info is None else last_info["agent_status"][cid]
            report.see_transition(map_name, cid, prev, info["agent_status"][cid], info, obs_list[cid])
        report.see_step(map_name, obs_list, info, num_cars, step_i)
        last_info = info

        if info["race_over"]:
            break

    close()


class Report:
    def __init__(self):
        self.obs_scalar = {
            k: Bounds() for k in ("velocity", "steering", "progress", "lap_count", "rank")
        }
        self.lidar = Bounds()
        self.cmd_raw = Bounds()
        self.cmd_clipped = Bounds()
        self.opp_scalar = {
            k: Bounds() for k in ("x_rel", "y_rel", "yaw_rel", "speed", "progress", "lap_count")
        }
        self.opp_status_seen = set()
        self.opp_inactive_nonzero = 0

        self.info_scalar = {
            k: Bounds() for k in ("step_count", "time_elapsed", "progress_delta", "friction_current", "max_progress")
        }
        self.agent_status_seen = set()
        self.wall_hit_seen = False
        self.vehicle_hit_seen = False
        self.lap_complete_seen = False
        self.stagnation_seen = False
        self.race_over_seen = {True: False, False: False}

        self.obs_keys = set()
        self.info_keys = set()
        self.opponent_keys = set()
        self.anomalies = []

        self.ranks_seen = set()
        self.mask_patterns = set()
        self.causes = {}
        self.finishes = []

    def see_command(self, speed):
        self.cmd_raw.see(speed)
        self.cmd_clipped.see(min(max(speed, sim_mod._TARGET_SPEED_MIN), sim_mod._TARGET_SPEED_MAX))

    def see_transition(self, map_name, cid, prev, now, info, obs):
        """Enregistre la cause d'un changement de statut, au pas où il se produit."""
        if prev == 1 and now == 0:
            cause = "stagnation" if info["stagnation"][cid] else "sortie de piste"
        elif prev == 1 and now == 2:
            cause = "arrivée"
            self.finishes.append({
                "map": map_name, "car": cid, "lap_count": obs["lap_count"],
                "progress": round(obs["progress"], 4), "rank": obs["rank"],
                "lap_times": [round(t, 2) for t in info["lap_times"][cid]],
                "max_progress": round(info["max_progress"][cid], 4),
            })
        else:
            return
        self.causes[cause] = self.causes.get(cause, 0) + 1

    def see_step(self, map_name, obs_list, info, num_cars, step_i=None):
        self.info_keys |= set(info.keys())
        self.ranks_seen |= {(slot < num_cars, r) for slot, r in info["ranks"].items()}
        self.mask_patterns.add(tuple(bool(b) for b in info["opponents_mask"]))
        for cid in range(num_cars):
            obs = obs_list[cid]
            self.obs_keys |= set(obs.keys())
            observer_active = info["agent_status"][cid] == 1

            if not observer_active:
                if len(self.anomalies) < 3:
                    self.anomalies.append({
                        "map": map_name, "step": step_i, "observer": cid,
                        "own_obs": {k: obs[k] for k in ("velocity", "steering", "progress")},
                        "agent_status": dict(info["agent_status"]),
                    })
            else:
                self.obs_scalar["velocity"].see(obs["velocity"])
                self.obs_scalar["steering"].see(obs["steering"])
                self.obs_scalar["progress"].see(obs["progress"])
                self.obs_scalar["lap_count"].see(obs["lap_count"])
                self.obs_scalar["rank"].see(obs["rank"])
                self.lidar.see(float(np.min(obs["lidar"])))
                self.lidar.see(float(np.max(obs["lidar"])))

                for slot, opp in obs["opponents"].items():
                    self.opponent_keys |= set(opp.keys())
                    self.opp_status_seen.add(opp["status"])
                    if opp["status"] == 1:
                        for k in self.opp_scalar:
                            self.opp_scalar[k].see(opp[k])
                    elif any(opp[k] != 0 for k in ("x_rel", "y_rel", "yaw_rel", "speed", "progress", "lap_count")):
                        self.opp_inactive_nonzero += 1

            self.info_scalar["progress_delta"].see(info["progress_delta"][cid])
            self.info_scalar["max_progress"].see(info["max_progress"][cid])
            self.agent_status_seen.add(info["agent_status"][cid])
            self.wall_hit_seen |= bool(info["collisions"]["wall"][cid])
            self.vehicle_hit_seen |= bool(info["collisions"]["vehicle"][cid])
            self.lap_complete_seen |= bool(info["lap_complete"][cid])
            self.stagnation_seen |= bool(info["stagnation"][cid])

        self.info_scalar["step_count"].see(info["step_count"])
        self.info_scalar["time_elapsed"].see(info["time_elapsed"])
        self.info_scalar["friction_current"].see(info["friction_current"])
        self.race_over_seen[bool(info["race_over"])] = True

    def print_all(self):
        print("\n" + "=" * 72)
        print("RELEVÉ — get_obs() (bornes observées, sur tous les épisodes/circuits)")
        print("=" * 72)
        for k, b in self.obs_scalar.items():
            print(f"  obs[{k!r}]".ljust(20), b)
        print(f"  obs['lidar'] min/max".ljust(20), self.lidar)
        print("  Vitesse ordonnée à une voiture active — à lire AVEC obs['velocity'] :")
        print(f"    avant écrêtage   {self.cmd_raw}")
        print(f"    après écrêtage   {self.cmd_clipped}  (plage acceptée : [{sim_mod._TARGET_SPEED_MIN}, {sim_mod._TARGET_SPEED_MAX}])")
        if self.obs_scalar['velocity'].n and self.cmd_clipped.n:
            gap = self.obs_scalar['velocity'].hi - self.cmd_clipped.hi
            print(f"    vitesse observée max − consigne écrêtée max = {gap:+.3f} m/s"
                  "  (≈ 0 : la borne haute observée n'est que celle de la consigne ;"
                  " > 0 : le simulateur dépasse sa consigne)")
        print(f"  clés obs observées : {sorted(self.obs_keys)}")

        print("\n  opponents (status == 1 uniquement) :")
        for k, b in self.opp_scalar.items():
            print(f"    opponents[i][{k!r}]".ljust(28), b)
        print(f"    valeurs de status observées : {sorted(self.opp_status_seen)}")
        print(f"    clés opponents observées : {sorted(self.opponent_keys)}")
        print(f"    emplacements inactifs avec une valeur non nulle (devrait être 0) : {self.opp_inactive_nonzero}")

        print("\n" + "=" * 72)
        print("RELEVÉ — get_step_info()")
        print("=" * 72)
        for k, b in self.info_scalar.items():
            print(f"  info[{k!r}]".ljust(24), b)
        print(f"  agent_status observés : {sorted(self.agent_status_seen)}  (0=DNF, 1=actif, 2=arrivé)")
        print(f"  wall collision observée au moins une fois   : {self.wall_hit_seen}")
        print(f"  vehicle collision observée au moins une fois: {self.vehicle_hit_seen}")
        print(f"  lap_complete observé au moins une fois      : {self.lap_complete_seen}")
        print(f"  stagnation observée au moins une fois       : {self.stagnation_seen}")
        print(f"  race_over observé à True / False            : {self.race_over_seen}")
        print(f"  clés info observées : {sorted(self.info_keys)}")
        print(f"  cause des changements de statut : {self.causes or 'aucun'}")
        actifs = sorted(r for en_piste, r in self.ranks_seen if en_piste)
        absents = sorted(r for en_piste, r in self.ranks_seen if not en_piste)
        print(f"  info['ranks'] : valeurs pour les voitures en piste {sorted(set(actifs))} ; emplacements absents {sorted(set(absents))}")
        print(f"  info['opponents_mask'] : motifs observés {sorted(self.mask_patterns)}")
        if self.finishes:
            print(f"  voitures arrivées : {len(self.finishes)} — lap_count à l'arrivée : {sorted({f['lap_count'] for f in self.finishes})}")
            for f in self.finishes[:30]:
                print(f"    {f['map']:<14} voiture {f['car']}  lap_count={f['lap_count']} progress={f['progress']} "
                      f"rank={f['rank']} max_progress={f['max_progress']}  lap_times={f['lap_times']}")

        print("\n" + "=" * 72)
        print("ÉCARTS avec get_space_info()")
        print("=" * 72)
        space = get_space_info()
        declared_obs_keys = set(space["observations"].keys())
        missing_in_space = self.obs_keys - declared_obs_keys
        missing_in_obs = declared_obs_keys - self.obs_keys
        print(f"  clés dans get_obs() mais absentes de get_space_info() : {sorted(missing_in_space)}")
        print(f"  clés dans get_space_info() mais absentes de get_obs() : {sorted(missing_in_obs)}")
        print(f"  'rel_dist' présent dans opponents ? {'rel_dist' in self.opponent_keys}")
        print(f"  'done' présent dans get_step_info() ? {'done' in self.info_keys}")

        if self.anomalies:
            print("\n" + "=" * 72)
            print(f"PIÈGE — get_obs() appelé pour un agent_id gelé/arrivé (échantillons)")
            print("=" * 72)
            print("  get_obs(agent_id) ne vérifie jamais si agent_id est encore actif : une")
            print("  fois DNF (status 0) ou arrivé (status 2), sa position réelle devient le")
            print("  sentinel hors-piste (~10000, 10000) — ses propres velocity/steering/")
            print("  progress, ET les x_rel/y_rel qu'il calcule pour SES adversaires, perdent")
            print("  tout sens (mesurés depuis 10000 m de la piste), même si ces adversaires")
            print("  sont eux bien actifs et rapportent un status correct. Conséquence pour")
            print("  le wrapper (env.py) : arrêter d'appeler get_obs() pour un agent_id dès")
            print("  que son agent_status quitte 1, comme font demo.py / sim_recorder.py.")
            for a in self.anomalies:
                print(f"  ex: map={a['map']} step={a['step']} observer={a['observer']}"
                      f" own_obs={a['own_obs']} agent_status={a['agent_status']}")

        print("\n" + "=" * 72)
        print("CONSTANTES DE MODULE (env_simulation.py)")
        print("=" * 72)
        for name in _CONSTANT_NAMES:
            print(f"  {name:<24} = {getattr(sim_mod, name)}")

        print("\n" + "=" * 72)
        print("DYNAMIQUE DU VÉHICULE (_PARAMS)")
        print("=" * 72)
        for k, v in _PARAMS.items():
            print(f"  {k:<10} = {v}")
        print(f"  empattement (lf + lr) = {_PARAMS['lf'] + _PARAMS['lr']:.4f} m")


def main():
    parser = argparse.ArgumentParser(description="CRA-6 — relevé de l'API du simulateur")
    parser.add_argument("--steps", type=int, default=1200, help="Pas de décision par circuit (défaut: 1200)")
    parser.add_argument("--num-cars", type=int, default=4, help="Voitures en piste, 1..4 (défaut: 4)")
    parser.add_argument("--maps", type=str, default=",".join(DEFAULT_MAPS),
                         help=f"Circuits séparés par des virgules (défaut: {','.join(DEFAULT_MAPS)})")
    parser.add_argument("--seed", type=int, default=42, help="Graine LiDAR (défaut: 42, pour reproductibilité)")
    parser.add_argument("--speed", type=float, default=None,
                         help="Impose cette vitesse commandée (m/s) à toutes les voitures, pour mesurer "
                              "le vrai plafond du simulateur. Défaut : chaque pilote de test garde la sienne (2 à 6 m/s)")
    args = parser.parse_args()

    num_cars = max(1, min(args.num_cars, 4))
    maps = [m.strip() for m in args.maps.split(",") if m.strip()]

    available = set(get_available_maps())
    unknown = [m for m in maps if m not in available]
    if unknown:
        sys.exit(f"Circuit(s) inconnu(s) : {unknown}. Disponibles : {sorted(available)}")

    report = Report()
    for map_name in maps:
        speed_txt = f", vitesse imposée {args.speed} m/s" if args.speed is not None else ""
        print(f"--- Circuit : {map_name} ({args.steps} pas, {num_cars} voitures{speed_txt}) ---")
        run_map(map_name, args.steps, num_cars, args.seed, report, speed_override=args.speed)

    report.print_all()


if __name__ == "__main__":
    main()
