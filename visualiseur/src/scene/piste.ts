import { DoubleSide, Mesh, MeshBasicMaterial, MeshStandardMaterial, Path, Shape, ShapeGeometry, Vector2 } from 'three'
import type { Scene } from 'three'
import { rubanLeLongDuContour } from './ruban.ts'
import { bandes, grain, texture } from './textures.ts'

const HAUTEUR_MUR = 0.25
const LARGEUR_VIBREUR = 0.18

function sommets(contour: readonly number[]): Vector2[] {
  const liste: Vector2[] = []
  for (let i = 0; i < contour.length; i += 2) liste.push(new Vector2(contour[i]!, contour[i + 1]!))
  return liste
}

export function installerPiste(scene: Scene, bords: readonly (readonly number[])[]): void {
  const [exterieur, ...trous] = bords
  if (!exterieur) return
  const forme = new Shape(sommets(exterieur))
  for (const trou of trous) forme.holes.push(new Path(sommets(trou)))

  const asphalte = texture(256, 256, (ctx, l, h) => grain(ctx, l, h, '#5a5d63', 5000))
  asphalte.repeat.set(0.5, 0.5)
  const sol = new Mesh(new ShapeGeometry(forme), new MeshStandardMaterial({ map: asphalte, roughness: 0.95 }))
  sol.rotation.x = -Math.PI / 2
  sol.position.y = 0.005
  sol.receiveShadow = true
  sol.matrixAutoUpdate = false
  sol.updateMatrix()
  scene.add(sol)

  const mur = new MeshBasicMaterial({ map: bandes('#d9d9d9', '#c22525'), side: DoubleSide })
  const vibreur = new MeshStandardMaterial({
    map: bandes('#ffffff', '#d62828'), roughness: 0.8, polygonOffset: true, polygonOffsetFactor: -2,
  })
  for (const contour of bords) {
    const barriere = new Mesh(rubanLeLongDuContour(contour, { hauteur: HAUTEUR_MUR, metresParMotif: 1 }), mur)
    barriere.castShadow = true
    const bordure = new Mesh(
      rubanLeLongDuContour(contour, { largeur: LARGEUR_VIBREUR, altitude: 0.01, metresParMotif: 0.5 }),
      vibreur,
    )
    bordure.receiveShadow = true
    barriere.matrixAutoUpdate = bordure.matrixAutoUpdate = false
    scene.add(barriere, bordure)
  }
}
