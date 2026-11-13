import { Color, Fog, Vector3 } from 'three'
import type { Scene, WebGLRenderer } from 'three'
import type { Carte } from '../types.ts'
import { installerCiel } from './ciel.ts'
import type { Eclairer } from './ciel.ts'
import { installerArbres, installerDepart, installerSol } from './environs.ts'
import { installerPiste } from './piste.ts'

export interface Decor {
  readonly eclairer: Eclairer
  readonly camerasTv: readonly number[]
}

export function construireDecor(scene: Scene, renderer: WebGLRenderer, carte: Carte): Decor {
  let xMin = Infinity
  let xMax = -Infinity
  let yMin = Infinity
  let yMax = -Infinity
  for (const bord of carte.bords) {
    for (let i = 0; i < bord.length; i += 2) {
      xMin = Math.min(xMin, bord[i]!)
      xMax = Math.max(xMax, bord[i]!)
      yMin = Math.min(yMin, bord[i + 1]!)
      yMax = Math.max(yMax, bord[i + 1]!)
    }
  }
  const centre = new Vector3((xMin + xMax) / 2, 0, -(yMin + yMax) / 2)
  const rayon = Math.max(xMax - xMin, yMax - yMin) / 2

  scene.background = new Color(0xa9c8e8)
  scene.fog = new Fog(0xb8d0e6, rayon * 1.2, rayon * 4 + 100)
  const eclairer = installerCiel(scene, renderer)
  installerSol(scene, centre, rayon)
  installerPiste(scene, carte.bords)
  installerDepart(scene, carte.depart)
  installerArbres(scene, carte.arbres)
  return { eclairer, camerasTv: carte.cameras_tv }
}
