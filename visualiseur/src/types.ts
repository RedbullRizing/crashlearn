export interface Depart {
  readonly x: number
  readonly y: number
  readonly angle: number
  readonly largeur: number
}

export interface Carte {
  readonly bords: readonly (readonly number[])[]
  readonly ligne_centrale: readonly number[]
  readonly arbres: readonly number[]
  readonly cameras_tv: readonly number[]
  readonly depart: Depart
}

export interface VoitureEnregistree {
  readonly nom: string
  readonly poses: readonly number[]
  readonly vitesse: readonly number[]
  readonly braquage: readonly number[]
  readonly statut: readonly number[]
  readonly rang: readonly number[]
  readonly tours: readonly number[]
  readonly progression: readonly number[]
}

export interface Course {
  readonly nom: string
  readonly circuit: string
  readonly dt: number
  readonly pas: number
  readonly carte: Carte
  readonly adherence: readonly number[]
  readonly voitures: readonly VoitureEnregistree[]
}

export interface Fiche {
  readonly nom: string
  readonly circuit: string
  readonly pilotes: readonly string[]
  readonly duree: number
  readonly trace: readonly number[]
}

export const SORTI = 0
export const ARRIVE = 2

export interface Courbe {
  readonly pas: readonly number[]
  readonly valeurs: readonly number[]
}

export type Reglages = Readonly<Record<string, unknown>>

export interface Entrainement {
  readonly nom: string
  readonly origine: 'archive' | 'local'
  readonly pilote: string
  readonly algo: string
  readonly date: string
  readonly git: { readonly commit?: string; readonly modifie?: boolean }
  readonly versions: Readonly<Record<string, string>>
  readonly config: Reglages
  readonly circuits: readonly string[]
  readonly circuits_eval: readonly string[]
  readonly bilan: Readonly<Record<string, number>>
  readonly note: string
  readonly sauvegardes: readonly number[]
  readonly courbes: Readonly<Record<string, Courbe>>
}

export interface Entrainements {
  readonly runs: readonly Entrainement[]
  readonly circuits: Readonly<Record<string, readonly number[]>>
}
