import type { Course, Entrainements, Fiche } from './types.ts'

export const COULEURS = ['#ff6b35', '#4cc9f0', '#7bf178', '#f72585'] as const

export const couleurDe = (n: number): string => COULEURS[n % COULEURS.length]!

export function element<T extends HTMLElement = HTMLElement>(id: string): T {
  const trouve = document.getElementById(id)
  if (!trouve) throw new Error(`#${id} absent de index.html`)
  return trouve as T
}

export const echapper = (texte: unknown): string =>
  String(texte).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)

export const formatDuree = (s: number): string =>
  `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`

export const formatChrono = (s: number): string =>
  `${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, '0')}`

async function lireJson<T>(chemin: string): Promise<T> {
  const reponse = await fetch(chemin)
  if (!reponse.ok) throw new Error(`${chemin} : ${reponse.status}`)
  return reponse.json() as Promise<T>
}

export const lireCourse = (nom: string): Promise<Course> => lireJson<Course>(`${encodeURIComponent(nom)}.json`)

export async function lireFiches(): Promise<Fiche[]> {
  try {
    const fiches = await lireJson<unknown[]>('courses.json')
    return fiches.filter((f): f is Fiche => typeof f === 'object' && f !== null && 'nom' in f && 'trace' in f)
  } catch {
    return []
  }
}

export async function lireEntrainements(): Promise<Entrainements> {
  try {
    return await lireJson<Entrainements>('entrainements.json')
  } catch {
    return { runs: [], circuits: {} }
  }
}

export const formatEntier = (n: number): string => n.toLocaleString('fr-FR')

export function formatDate(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime())
    ? iso
    : date.toLocaleString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
