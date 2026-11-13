"""Course à plusieurs voitures entre dossiers pilotes, chargés comme au tournoi.

    make grand-prix PILOTES=driver1,driver2,driver3,driver4 CIRCUITS=Spa,Budapest
    make grand-prix PILOTES=champion,driver1,driver2,driver3

Sert au diagnostic de la partie 2 (des pilotes entraînés seuls, mis ensemble)
et à mesurer le champion de la partie 3 face aux autres. Les places sur la
grille tournent d'une course à l'autre, pour que personne ne parte toujours devant.
"""

from __future__ import annotations

import argparse
from collections import defaultdict

import env_simulation as sim
from agent_loader import validate_and_load_agent
from training.env import TEST, VALIDATION
from training.metrics import ACTIF, SuiviCourse


def course(agents: list, circuit: str, graine: int, pas_max: int = 6000) -> dict:
    sim.set_map(circuit)
    sim.reset(num_cars=len(agents), seed=graine)
    suivi = SuiviCourse(nb_voitures=len(agents))
    info = sim.get_step_info()
    for _ in range(pas_max):
        for slot, agent in enumerate(agents):
            if info["agent_status"][slot] == ACTIF:
                sim.apply_action(slot, *agent.predict(sim.get_obs(slot), info))
        sim.simulation_step()
        info = sim.get_step_info()
        suivi.observer(info)
        if info["race_over"]:
            break
    return suivi.resultats(), info["ranks"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilotes", default="driver1,driver2,driver3,driver4")
    parser.add_argument("--circuits", default=",".join(VALIDATION + TEST))
    parser.add_argument("--courses", type=int, default=2, help="par circuit")
    parser.add_argument("--graine", type=int, default=0)
    args = parser.parse_args()

    noms = args.pilotes.split(",")
    agents = {nom: validate_and_load_agent(f"submission/{nom}")[1] for nom in noms}
    bilan = defaultdict(lambda: defaultdict(float))
    n = 0
    for circuit in args.circuits.split(","):
        for c in range(args.courses):
            ordre = noms[n % len(noms):] + noms[:n % len(noms)]
            resultats, rangs = course([agents[nom] for nom in ordre], circuit, args.graine + n)
            n += 1
            ligne = []
            for slot, nom in enumerate(ordre):
                v = resultats[slot]
                b = bilan[nom]
                b["arrivees"] += v.a_termine
                b["abandons"] += v.a_abandonne
                b["contacts"] += v.chocs_voiture
                b["chocs_mur"] += v.chocs_mur
                b["rang"] += rangs.get(slot, len(ordre))
                b["victoires"] += rangs.get(slot) == 1 and v.a_termine
                etat = "arrivé" if v.a_termine else (v.cause_abandon or "temps écoulé")
                ligne.append(f"{nom} {etat} r{rangs.get(slot, '-')} c{v.chocs_voiture}")
            print(f"  {circuit:<14} " + " | ".join(ligne))

    print(f"\n  {n} courses. Par pilote : arrivées, abandons, victoires, rang moyen, contacts, chocs mur")
    for nom in noms:
        b = bilan[nom]
        print(f"  {nom:<10} {b['arrivees']:>3.0f} {b['abandons']:>3.0f} {b['victoires']:>3.0f} "
              f"{b['rang'] / n:>5.2f} {b['contacts']:>5.0f} {b['chocs_mur']:>5.0f}")


if __name__ == "__main__":
    main()
