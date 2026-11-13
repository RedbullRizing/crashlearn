import type { Voiture } from '../scene/voiture.ts'
import { ARRIVE, SORTI } from '../types.ts'
import type { Course } from '../types.ts'

const SAUT_TELEPORTATION = 3

const ecartAngle = (a: number, b: number): number => Math.atan2(Math.sin(b - a), Math.cos(b - a))

interface Piste {
  readonly poses: Float32Array
  readonly braquage: Float32Array
  readonly distance: Float32Array
  readonly statut: readonly number[]
}

export class Lecture {
  readonly dt: number
  readonly dernierPas: number
  readonly duree: number
  temps = 0
  enLecture = true
  cadence = 1
  private readonly pistes: readonly Piste[]

  constructor(course: Course) {
    this.dt = course.dt
    this.dernierPas = course.pas - 1
    this.duree = this.dernierPas * course.dt
    this.pistes = course.voitures.map((v) => {
      const poses = Float32Array.from(v.poses)
      const distance = new Float32Array(course.pas)
      for (let i = 1; i < course.pas; i++) {
        distance[i] = distance[i - 1]! + Math.hypot(poses[3 * i]! - poses[3 * i - 3]!, poses[3 * i + 1]! - poses[3 * i - 2]!)
      }
      return { poses, distance, braquage: Float32Array.from(v.braquage), statut: v.statut }
    })
  }

  avancer(ecoule: number): boolean {
    if (!this.enLecture) return false
    this.temps += ecoule * this.cadence
    if (this.temps < this.duree) return false
    this.temps = this.duree
    this.enLecture = false
    return true
  }

  deplacer(secondes: number): void {
    this.temps = Math.min(Math.max(this.temps + secondes, 0), this.duree)
  }

  basculer(): void {
    if (!this.enLecture && this.temps >= this.duree) this.temps = 0
    this.enLecture = !this.enLecture
  }

  poser(voitures: readonly Voiture[]): number {
    const position = this.temps / this.dt
    const i = Math.min(Math.max(Math.floor(position), 0), this.dernierPas)
    const j = Math.min(i + 1, this.dernierPas)
    const fraction = position - i
    for (let n = 0; n < voitures.length; n++) {
      const { poses, braquage, distance, statut } = this.pistes[n]!
      const a = 3 * i
      const b = 3 * j
      const x = poses[a]!
      const y = poses[a + 1]!
      const cap = poses[a + 2]!
      const dx = poses[b]! - x
      const dy = poses[b + 1]! - y
      const k = dx * dx + dy * dy > SAUT_TELEPORTATION * SAUT_TELEPORTATION ? 0 : fraction
      const voiture = voitures[n]!
      voiture.placer(
        x + dx * k,
        y + dy * k,
        cap + ecartAngle(cap, poses[b + 2]!) * k,
        braquage[i]! + (braquage[j]! - braquage[i]!) * k,
        distance[i]! + (distance[j]! - distance[i]!) * k,
      )
      voiture.montrer(statut[i] !== ARRIVE, statut[i] === SORTI)
    }
    return i
  }
}
