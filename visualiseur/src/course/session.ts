import { PerspectiveCamera, Scene, WebGLRenderer } from 'three'
import { couleurDe } from '../outils.ts'
import { Realisateur } from '../scene/cameras.ts'
import { construireDecor } from '../scene/decor.ts'
import { Voiture } from '../scene/voiture.ts'
import type { Course } from '../types.ts'
import { Hud } from './hud.ts'
import { Lecture } from './lecture.ts'

const PIXELS_MAX = 2
const IMAGE_LA_PLUS_LONGUE = 0.1
const CHAMP_DE_REFERENCE = Math.tan(Math.PI / 6)
const DEMI_DEGRE = Math.PI / 360

export function lancerCourse(course: Course): void {
  document.body.classList.add('en-course')
  const renderer = new WebGLRenderer({ antialias: true, powerPreference: 'high-performance' })
  renderer.setPixelRatio(Math.min(devicePixelRatio, PIXELS_MAX))
  renderer.setSize(innerWidth, innerHeight)
  document.body.prepend(renderer.domElement)
  const scene = new Scene()
  const camera = new PerspectiveCamera(60, innerWidth / innerHeight, 0.05, 20000)

  const decor = construireDecor(scene, renderer, course.carte)
  const voitures = course.voitures.map((v, n) => new Voiture(couleurDe(n), v.nom))
  for (const voiture of voitures) scene.add(voiture.groupe)
  const realisateur = new Realisateur(camera, renderer.domElement, decor.camerasTv)
  const lecture = new Lecture(course)

  let suivie = 0
  let pasAffiche = -1
  const rafraichir = (): void => {
    pasAffiche = -1
  }
  const suivreVoiture = (n: number): void => {
    suivie = (n + voitures.length) % voitures.length
    rafraichir()
  }
  const basculerLecture = (): void => {
    lecture.basculer()
    rafraichir()
  }
  const deplacer = (secondes: number): void => {
    lecture.deplacer(secondes)
    rafraichir()
  }

  const hud = new Hud(course, {
    basculerLecture,
    suivreVoiture,
    allerAuPas: (pas) => {
      lecture.temps = pas * lecture.dt
      rafraichir()
    },
    choisirCadence: (cadence) => {
      lecture.cadence = cadence
    },
    choisirVue: (indice) => {
      realisateur.choisirVue(indice)
      rafraichir()
    },
  })

  addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return
    const sens = e.shiftKey ? -1 : 1
    switch (e.code) {
      case 'Space':
        basculerLecture()
        break
      case 'ArrowLeft':
        deplacer(e.shiftKey ? -10 : -1)
        break
      case 'ArrowRight':
        deplacer(e.shiftKey ? 10 : 1)
        break
      case 'KeyC':
        realisateur.changerVue(sens)
        rafraichir()
        break
      case 'Tab':
        suivreVoiture(suivie + sens)
        break
      case 'Escape':
        location.href = './'
        break
      case 'Digit1':
      case 'Digit2':
      case 'Digit3':
      case 'Digit4': {
        const n = Number(e.code.at(-1)) - 1
        if (n >= voitures.length) return
        suivreVoiture(n)
        break
      }
      default:
        return
    }
    e.preventDefault()
  })

  addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(innerWidth, innerHeight)
  })

  let instantPrecedent = performance.now()
  renderer.setAnimationLoop((instant: number) => {
    const ecoule = Math.min(Math.max((instant - instantPrecedent) / 1000, 0), IMAGE_LA_PLUS_LONGUE)
    instantPrecedent = instant
    if (lecture.avancer(ecoule)) rafraichir()

    const pas = lecture.poser(voitures)
    const suivieMaintenant = voitures[suivie]!
    realisateur.suivre(suivieMaintenant, ecoule)
    decor.eclairer(suivieMaintenant.groupe.position)
    const zoom = Math.tan(camera.fov * DEMI_DEGRE) / CHAMP_DE_REFERENCE
    for (let n = 0; n < voitures.length; n++) voitures[n]!.etiqueter(n !== suivie, zoom)

    if (pas !== pasAffiche) {
      pasAffiche = pas
      hud.afficher({ pas, suivie, vue: realisateur.indice, enLecture: lecture.enLecture })
    }
    renderer.render(scene, camera)
  })
}
