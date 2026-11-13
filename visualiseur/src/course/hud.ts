import { couleurDe, echapper, element, formatChrono, formatDuree } from '../outils.ts'
import { VUES } from '../scene/cameras.ts'
import { ARRIVE, SORTI } from '../types.ts'
import type { Course } from '../types.ts'

const CADENCES = [0.25, 0.5, 1, 2, 4] as const
const BRAQUAGE_MAX = 0.42
const ADHERENCE_GLISSANTE = 0.8
const DEGRES = 180 / Math.PI

export interface Commandes {
  basculerLecture(): void
  allerAuPas(pas: number): void
  choisirCadence(cadence: number): void
  choisirVue(indice: number): void
  suivreVoiture(indice: number): void
}

export interface Etat {
  readonly pas: number
  readonly suivie: number
  readonly vue: number
  readonly enLecture: boolean
}

interface Ligne {
  readonly bouton: HTMLElement
  readonly position: HTMLElement
  readonly etat: HTMLElement
}

function ecrire(cible: HTMLElement, texte: string): void {
  if (cible.textContent !== texte) cible.textContent = texte
}

function segments(conteneur: HTMLElement, libelles: readonly string[], choisir: (n: number) => void): (actif: number) => void {
  conteneur.innerHTML = libelles.map((l, n) => `<button data-n="${n}">${echapper(l)}</button>`).join('')
  conteneur.addEventListener('click', (e) => {
    const bouton = (e.target as Element).closest<HTMLElement>('button')
    if (!bouton) return
    choisir(Number(bouton.dataset['n']))
    bouton.blur()
  })
  const boutons = [...conteneur.children]
  let courant = -1
  return (actif) => {
    if (actif === courant) return
    courant = actif
    boutons.forEach((b, n) => b.setAttribute('aria-pressed', String(n === actif)))
  }
}

export class Hud {
  private readonly course: Course
  private readonly lignes: readonly Ligne[]
  private readonly hauteurLigne: number
  private readonly ordre: number[]
  private readonly marquerVue: (actif: number) => void
  private readonly chrono = element('chrono')
  private readonly tempsCourant = element('temps-courant')
  private readonly infos = element('infos')
  private readonly vitesse = element('vitesse')
  private readonly braquage = element('braquage')
  private readonly braquageTexte = element('braquage-texte')
  private readonly adherence = element('adherence')
  private readonly adherenceTexte = element('adherence-texte')
  private readonly curseur = element<HTMLInputElement>('temps')
  private readonly lecture = element('lecture')

  constructor(course: Course, commandes: Commandes) {
    this.course = course
    element('hud').hidden = false
    element('titre').textContent = `${course.circuit} · ${course.nom}`
    element('temps-total').textContent = formatDuree((course.pas - 1) * course.dt)

    const classement = element('classement')
    classement.innerHTML = course.voitures
      .map(
        (v, n) => `<button class="ligne" data-voiture="${n}">
          <span class="position"></span>
          <span class="pastille" style="background:${couleurDe(n)}"></span>
          <span class="nom">${echapper(v.nom)}</span>
          <span class="etat"></span>
        </button>`,
      )
      .join('')
    this.lignes = [...classement.children].map((bouton) => ({
      bouton: bouton as HTMLElement,
      position: bouton.querySelector<HTMLElement>('.position')!,
      etat: bouton.querySelector<HTMLElement>('.etat')!,
    }))
    this.hauteurLigne = this.lignes[0]?.bouton.offsetHeight ?? 0
    this.ordre = course.voitures.map((_, n) => n)
    classement.addEventListener('click', (e) => {
      const ligne = (e.target as Element).closest<HTMLElement>('[data-voiture]')
      if (!ligne) return
      commandes.suivreVoiture(Number(ligne.dataset['voiture']))
      ligne.blur()
    })

    const marquerCadence = segments(
      element('cadence'),
      CADENCES.map((c) => `×${String(c).replace('.', ',')}`),
      (n) => {
        commandes.choisirCadence(CADENCES[n]!)
        marquerCadence(n)
      },
    )
    marquerCadence(CADENCES.indexOf(1))
    this.marquerVue = segments(element('vues'), VUES, (n) => commandes.choisirVue(n))

    this.curseur.max = String(course.pas - 1)
    this.curseur.addEventListener('input', () => commandes.allerAuPas(Number(this.curseur.value)))
    this.curseur.addEventListener('change', () => this.curseur.blur())
    this.lecture.addEventListener('click', () => {
      commandes.basculerLecture()
      this.lecture.blur()
    })
  }

  afficher({ pas, suivie, vue, enLecture }: Etat): void {
    const { course } = this
    const secondes = pas * course.dt
    const v = course.voitures[suivie]!
    ecrire(this.chrono, formatChrono(secondes))
    ecrire(this.tempsCourant, formatDuree(secondes))
    ecrire(this.infos, `${v.nom} · tour ${v.tours[pas]! + 1} · ${(v.progression[pas]! * 100).toFixed(0)} %`)
    ecrire(this.vitesse, v.vitesse[pas]!.toFixed(1))

    const braquage = v.braquage[pas]!
    ecrire(this.braquageTexte, `${(braquage * DEGRES).toFixed(0)}°`)
    this.braquage.style.transform = `scaleX(${(-Math.sign(braquage) * Math.min(Math.abs(braquage) / BRAQUAGE_MAX, 1)).toFixed(3)})`
    const adherence = course.adherence[pas]!
    ecrire(this.adherenceTexte, adherence.toFixed(2))
    this.adherence.style.transform = `scaleX(${Math.min(adherence, 1).toFixed(3)})`
    this.adherence.style.background = adherence < ADHERENCE_GLISSANTE ? '#4cc9f0' : ''

    this.ordre.sort((a, b) => course.voitures[a]!.rang[pas]! - course.voitures[b]!.rang[pas]! || a - b)
    for (let position = 0; position < this.ordre.length; position++) {
      const n = this.ordre[position]!
      const voiture = course.voitures[n]!
      const ligne = this.lignes[n]!
      const statut = voiture.statut[pas]
      const classe = statut === SORTI ? 'etat sorti' : statut === ARRIVE ? 'etat arrive' : 'etat'
      ligne.bouton.style.transform = `translateY(${(position - n) * this.hauteurLigne}px)`
      ligne.bouton.setAttribute('aria-pressed', String(n === suivie))
      ecrire(ligne.position, String(position + 1))
      ecrire(ligne.etat, statut === SORTI ? 'Sorti' : statut === ARRIVE ? 'Arrivé' : `T${voiture.tours[pas]! + 1}`)
      if (ligne.etat.className !== classe) ligne.etat.className = classe
    }

    if (document.activeElement !== this.curseur) this.curseur.value = String(pas)
    ecrire(this.lecture, enLecture ? '⏸' : '▶')
    this.marquerVue(vue)
  }
}
