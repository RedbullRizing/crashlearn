"""Métriques de course, reconstruites à partir de ce que renvoie le simulateur.

Le simulateur signale qu'une voiture a abandonné — `agent_status` passe à 0 —
mais il ne dit jamais **pourquoi** : `_freeze_dnf()` écrase le statut sans
conserver la cause. On suit donc les signaux de chaque voiture à chaque pas,
pour pouvoir attribuer la cause au moment exact de la bascule.

Les deux causes d'abandon imposées par le moteur :

* **stagnation** — la voiture n'a pas progressé sur une fenêtre glissante de
  4 secondes. C'est la « police » du sujet, elle frappe les politiques trop
  prudentes qui ont appris à survivre en ralentissant.
* **sortie de piste** — signalée par `collisions["wall"]`, qui vaut True quand
  la voiture percute un mur *en mouvement*. Une voiture arrêtée contre un mur
  ne déclenche rien.

Quand aucun des deux signaux n'était actif juste avant la bascule, la cause est
`inconnue` : c'est un cas à regarder de près, pas à ignorer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Valeurs de agent_status telles que le moteur les définit.
DNF = 0
ACTIF = 1
ARRIVE = 2

CAUSE_STAGNATION = "stagnation"
CAUSE_SORTIE = "sortie_de_piste"
CAUSE_INCONNUE = "inconnue"


@dataclass
class ResultatVoiture:
    """Ce qu'on retient d'une voiture à la fin d'un épisode."""

    statut: int = ACTIF
    tours: int = 0
    temps_au_tour: list[float] = field(default_factory=list)
    progression_max: float = 0.0
    cause_abandon: str | None = None
    pas_avant_abandon: int | None = None
    chocs_mur: int = 0
    chocs_voiture: int = 0

    @property
    def a_termine(self) -> bool:
        return self.statut == ARRIVE

    @property
    def a_abandonne(self) -> bool:
        return self.statut == DNF

    @property
    def meilleur_tour(self) -> float | None:
        return min(self.temps_au_tour) if self.temps_au_tour else None


class SuiviCourse:
    """Accumule les infos d'un épisode et en tire les métriques.

    Usage :

        suivi = SuiviCourse(nb_voitures=1)
        while not termine:
            simulation_step()
            suivi.observer(get_step_info())
        resultats = suivi.resultats()
    """

    def __init__(self, nb_voitures: int = 1) -> None:
        self.nb_voitures = nb_voitures
        self._resultats = {i: ResultatVoiture() for i in range(nb_voitures)}
        # Dernier signal connu avant la bascule en abandon.
        self._stagnait = {i: False for i in range(nb_voitures)}
        self._a_tape_mur = {i: False for i in range(nb_voitures)}
        self._pas = 0

    def observer(self, info: dict) -> None:
        """À appeler après chaque `simulation_step()`."""
        self._pas = int(info["step_count"])

        for i in range(self.nb_voitures):
            resultat = self._resultats[i]
            statut_avant = resultat.statut
            statut = int(info["agent_status"][i])

            if bool(info["collisions"]["wall"][i]):
                resultat.chocs_mur += 1
                self._a_tape_mur[i] = True
            if bool(info["collisions"]["vehicle"][i]):
                resultat.chocs_voiture += 1

            stagne = bool(info["stagnation"][i])
            if stagne:
                self._stagnait[i] = True

            # La bascule vers l'abandon est le seul moment où la cause est
            # encore déductible : après, tous les signaux sont remis à zéro.
            if statut_avant == ACTIF and statut == DNF:
                resultat.cause_abandon = self._deduire_cause(i)
                resultat.pas_avant_abandon = self._pas

            resultat.statut = statut
            resultat.temps_au_tour = list(info["lap_times"][i])
            resultat.tours = len(resultat.temps_au_tour)
            resultat.progression_max = float(info["max_progress"][i])

    def _deduire_cause(self, i: int) -> str:
        if self._stagnait[i]:
            return CAUSE_STAGNATION
        if self._a_tape_mur[i]:
            return CAUSE_SORTIE
        return CAUSE_INCONNUE

    def resultats(self) -> dict[int, ResultatVoiture]:
        return dict(self._resultats)


def agreger(episodes: list[dict[int, ResultatVoiture]], tours_requis: int = 3) -> dict[str, float]:
    """Résume plusieurs épisodes en métriques comparables entre politiques.

    C'est ce qui part dans TensorBoard, et ce sur quoi les politiques seront
    comparées. Les taux sont dans [0, 1].
    """
    voitures = [v for episode in episodes for v in episode.values()]
    if not voitures:
        return {}

    total = len(voitures)
    termines = [v for v in voitures if v.a_termine]
    abandons = [v for v in voitures if v.a_abandonne]
    tous_les_tours = [t for v in voitures for t in v.temps_au_tour]

    mesures: dict[str, float] = {
        "course/taux_completion": len(termines) / total,
        "course/taux_abandon": len(abandons) / total,
        "course/tours_moyens": sum(v.tours for v in voitures) / total,
        "course/progression_max_moyenne": sum(v.progression_max for v in voitures) / total,
        "chocs/mur_par_voiture": sum(v.chocs_mur for v in voitures) / total,
        "chocs/voiture_par_voiture": sum(v.chocs_voiture for v in voitures) / total,
    }

    if tous_les_tours:
        mesures["tour/temps_moyen"] = sum(tous_les_tours) / len(tous_les_tours)
        mesures["tour/meilleur"] = min(tous_les_tours)

    # Taux d'abandon par cause, rapporté au nombre total de voitures : c'est ce
    # qui dit s'il faut travailler la prudence ou au contraire l'agressivité.
    for cause in (CAUSE_STAGNATION, CAUSE_SORTIE, CAUSE_INCONNUE):
        n = sum(1 for v in abandons if v.cause_abandon == cause)
        mesures[f"abandon/{cause}"] = n / total

    return mesures
