export interface Mesure {
  readonly titre: string
  readonly format: (valeur: number) => string
}

const pourcent = (v: number): string => `${(v * 100).toFixed(0)} %`
const secondes = (v: number): string => `${v.toFixed(2)} s`
const nombre = (v: number): string => v.toFixed(2).replace(/\.?0+$/, '')

export const BILAN: Readonly<Record<string, Mesure>> = {
  'course/taux_completion': { titre: 'Courses terminées', format: pourcent },
  'tour/meilleur': { titre: 'Meilleur tour', format: secondes },
  'tour/temps_moyen': { titre: 'Tour moyen', format: secondes },
  'course/tours_moyens': { titre: 'Tours par course', format: nombre },
  'chocs/mur_par_voiture': { titre: 'Chocs contre un mur, par voiture', format: nombre },
  'chocs/voiture_par_voiture': { titre: 'Contacts entre voitures, par voiture', format: nombre },
  'course/taux_abandon': { titre: 'Abandons', format: pourcent },
  'abandon/stagnation': { titre: 'Abandons sur blocage', format: pourcent },
  'abandon/sortie_de_piste': { titre: 'Abandons sur sortie de piste', format: pourcent },
  'abandon/inconnue': { titre: 'Abandons de cause inconnue', format: pourcent },
  'course/progression_max_moyenne': { titre: 'Progression maximale moyenne, en tours', format: nombre },
}

export const mesure = (cle: string): Mesure => BILAN[cle] ?? { titre: cle, format: nombre }

export const COURBES: Readonly<Record<string, { readonly titre: string; readonly aide: string }>> = {
  'rollout/ep_rew_mean': {
    titre: 'Récompense moyenne par épisode',
    aide: 'Somme des récompenses d’un épisode, moyennée sur les derniers épisodes joués. Elle monte quand le pilote progresse.',
  },
  'rollout/ep_len_mean': {
    titre: 'Durée moyenne d’un épisode, en pas',
    aide: 'Un épisode s’arrête sur un choc, une élimination, une arrivée ou la durée maximale. Un pas dure 0,05 s.',
  },
}

export const SECTIONS: readonly { readonly cle: string; readonly titre: string }[] = [
  { cle: '', titre: 'Entraînement' },
  { cle: 'ppo', titre: 'Algorithme PPO' },
  { cle: 'env', titre: 'Environnement' },
  { cle: 'recompense', titre: 'Poids de la récompense' },
]

export const REGLAGES: Readonly<Record<string, string>> = {
  pas: 'Nombre total de pas de simulation joués pendant l’entraînement.',
  envs: 'Simulateurs lancés en parallèle pour collecter l’expérience.',
  graine: 'Valeur qui fixe le hasard : même graine et même code, même entraînement.',
  eval_episodes: 'Courses d’évaluation par circuit de validation, à la fin.',
  depuis: 'Run dont le modèle sert de point de départ.',
  fichier: 'Fichier de configuration lu au lancement.',
  episodes: 'Nombre de courses jouées.',
  pas_max: 'Durée maximale d’un épisode, en pas de 0,05 s.',
  vitesse_cible: 'Vitesse visée par le pilote écrit à la main, en m/s.',
  'ppo.n_steps': 'Pas joués par simulateur avant chaque mise à jour du réseau.',
  'ppo.batch_size': 'Taille des paquets d’expériences utilisés à chaque correction du réseau.',
  'ppo.gamma': 'Poids du futur : proche de 1, le pilote valorise les récompenses lointaines.',
  'ppo.learning_rate': 'Taille de chaque correction du réseau. Trop grande, l’apprentissage devient instable.',
  'env.pas_max': 'Durée maximale d’un épisode, en pas de 0,05 s.',
  'env.fin_sur_choc': 'Un choc contre un mur termine l’épisode.',
  'env.meteo': 'Adhérence et bruit du LiDAR tirés au hasard pendant l’épisode.',
  'env.adversaires': 'Pilotes adverses présents sur la piste.',
  'recompense.cout_temps': 'Retiré à chaque pas : pousse à finir vite.',
  'recompense.poids_douceur': 'Multiplie l’écart de braquage entre deux pas : pénalise les à-coups.',
  'recompense.penalite_choc': 'Retirée à chaque choc contre un mur.',
  'recompense.penalite_contact': 'Retirée à chaque contact avec une autre voiture.',
  'recompense.penalite_dnf': 'Retirée quand la voiture est éliminée.',
}

export const FORMULE_RECOMPENSE =
  'Récompense d’un pas = mètres gagnés sur la piste − cout_temps − poids_douceur × |écart de braquage| − pénalités'
