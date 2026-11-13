import { MathUtils, Vector3 } from 'three'
import type { PerspectiveCamera } from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import type { Voiture } from './voiture.ts'

export const VUES = ['Poursuite', 'Embarquée', 'TV', 'Hélico', 'Libre'] as const

const POURSUITE = 0
const EMBARQUEE = 1
const TV = 2
const HELICO = 3
const LIBRE = 4
const SAUT_MAX = 15
const HAUTEUR_POSTE_TV = 2.2
const CHAMP_NORMAL = 60
const CHAMP_EMBARQUE = 80

const amortiSansDependreDesImages = (raideur: number, dt: number): number => 1 - Math.exp(-raideur * dt)

export class Realisateur {
  indice = POURSUITE
  private readonly orbite: OrbitControls
  private readonly cible = new Vector3()
  private readonly voulue = new Vector3()
  private readonly regard = new Vector3()
  private readonly regardLisse = new Vector3()
  private coupeFranche = true
  private readonly camera: PerspectiveCamera
  private readonly postesTv: readonly number[]

  constructor(camera: PerspectiveCamera, surface: HTMLElement, postesTv: readonly number[]) {
    this.camera = camera
    this.postesTv = postesTv
    this.orbite = new OrbitControls(camera, surface)
    this.orbite.enabled = false
    this.orbite.enableDamping = true
    this.orbite.maxPolarAngle = Math.PI / 2 - 0.05
  }

  changerVue(sens: number): void {
    this.choisirVue((this.indice + sens + VUES.length) % VUES.length)
  }

  choisirVue(indice: number): void {
    this.indice = indice
    this.orbite.enabled = indice === LIBRE
    if (this.orbite.enabled) this.orbite.target.copy(this.regardLisse)
    this.regler(indice === EMBARQUEE ? CHAMP_EMBARQUE : CHAMP_NORMAL)
    this.coupeFranche = true
  }

  suivre(voiture: Voiture, dt: number): void {
    const { camera, cible, voulue, regard } = this
    const g = voiture.groupe
    g.updateMatrixWorld()
    cible.copy(g.position)
    switch (this.indice) {
      case POURSUITE:
        this.placer(g.localToWorld(voulue.set(-1.6, 0.7, 0)), g.localToWorld(regard.set(0.8, 0.15, 0)), dt, 6)
        break
      case EMBARQUEE:
        camera.position.copy(g.localToWorld(voulue.set(0.12, 0.17, 0)))
        camera.lookAt(g.localToWorld(regard.set(2, 0.12, 0)))
        break
      case TV:
        if (!this.posteLePlusProche(cible.x, cible.z)) break
        camera.position.copy(voulue)
        if (this.coupeFranche) this.regardLisse.copy(cible)
        this.regardLisse.lerp(cible, amortiSansDependreDesImages(8, dt))
        camera.lookAt(this.regardLisse)
        this.regler(MathUtils.clamp(MathUtils.radToDeg(2 * Math.atan(1.2 / camera.position.distanceTo(cible))), 6, 50))
        this.coupeFranche = false
        break
      case HELICO:
        this.placer(g.localToWorld(voulue.set(-4, 7, 0)), cible, dt, 3)
        break
      default:
        this.orbite.update()
    }
  }

  private regler(champ: number): void {
    if (Math.abs(this.camera.fov - champ) < 0.01) return
    this.camera.fov = champ
    this.camera.updateProjectionMatrix()
  }

  private placer(position: Vector3, vise: Vector3, dt: number, raideur: number): void {
    const { camera, regardLisse } = this
    if (this.coupeFranche || camera.position.distanceToSquared(position) > SAUT_MAX * SAUT_MAX) {
      camera.position.copy(position)
      regardLisse.copy(vise)
      this.coupeFranche = false
    } else {
      camera.position.lerp(position, amortiSansDependreDesImages(raideur, dt))
      regardLisse.lerp(vise, amortiSansDependreDesImages(raideur * 1.5, dt))
    }
    camera.lookAt(regardLisse)
  }

  private posteLePlusProche(x: number, z: number): boolean {
    const postes = this.postesTv
    let distance = Infinity
    for (let i = 0; i < postes.length; i += 2) {
      const px = postes[i]!
      const pz = -postes[i + 1]!
      const d = (px - x) ** 2 + (pz - z) ** 2
      if (d < distance) {
        distance = d
        this.voulue.set(px, HAUTEUR_POSTE_TV, pz)
      }
    }
    return distance < Infinity
  }
}
