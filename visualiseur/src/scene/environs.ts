import {
  BoxGeometry, Color, ConeGeometry, CylinderGeometry, Group, InstancedMesh, Matrix4, Mesh, MeshStandardMaterial,
  PlaneGeometry, Quaternion, RepeatWrapping, Vector3,
} from 'three'
import type { Scene } from 'three'
import type { Depart } from '../types.ts'
import { grain, texture } from './textures.ts'

const MARGE_DU_SOL = 400
const METRES_PAR_MOTIF_HERBE = 8
const AXE_VERTICAL = new Vector3(0, 1, 0)

export function installerSol(scene: Scene, centre: Vector3, rayon: number): void {
  const herbe = texture(256, 256, (ctx, l, h) => {
    grain(ctx, l, h, '#4f7a2c', 6000)
    ctx.fillStyle = 'rgba(255,255,255,0.04)'
    ctx.fillRect(0, 0, l / 2, h)
  })
  const cote = rayon * 2 + MARGE_DU_SOL
  herbe.repeat.set(cote / METRES_PAR_MOTIF_HERBE, cote / METRES_PAR_MOTIF_HERBE)
  const plan = new Mesh(new PlaneGeometry(cote, cote), new MeshStandardMaterial({ map: herbe, roughness: 1 }))
  plan.rotation.x = -Math.PI / 2
  plan.position.set(centre.x, 0, centre.z)
  plan.receiveShadow = true
  plan.matrixAutoUpdate = false
  plan.updateMatrix()
  scene.add(plan)
}

export function installerDepart(scene: Scene, { x, y, angle, largeur }: Depart): void {
  const damier = texture(64, 512, (ctx, l, h) => {
    const c = l / 2
    for (let i = 0; i < h / c; i++) {
      for (let j = 0; j < 2; j++) {
        ctx.fillStyle = (i + j) % 2 ? '#111' : '#fff'
        ctx.fillRect(j * c, i * c, c, c)
      }
    }
  }, false)
  const groupe = new Group()
  const ligne = new Mesh(
    new PlaneGeometry(0.25, largeur),
    new MeshStandardMaterial({ map: damier, polygonOffset: true, polygonOffsetFactor: -4 }),
  )
  ligne.rotation.x = -Math.PI / 2
  ligne.position.y = 0.012
  ligne.receiveShadow = true
  groupe.add(ligne)

  const metal = new MeshStandardMaterial({ color: 0x2b2f38, metalness: 0.6, roughness: 0.4 })
  const poteau = new BoxGeometry(0.12, 1.8, 0.12)
  for (const cote of [-1, 1]) {
    const mat = new Mesh(poteau, metal)
    mat.position.set(0, 0.9, cote * (largeur / 2 + 0.35))
    mat.castShadow = true
    groupe.add(mat)
  }
  const banniere = texture(1024, 128, (ctx, l, h) => {
    ctx.fillStyle = '#d62828'
    ctx.fillRect(0, 0, l, h)
    ctx.fillStyle = '#fff'
    ctx.font = 'italic 900 84px system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('CRASH & LEARN', l / 2, h / 2 + 4)
  }, false)
  const banniereInversee = banniere.clone()
  banniereInversee.wrapS = RepeatWrapping
  banniereInversee.repeat.x = -1
  const portique = new Mesh(new BoxGeometry(0.12, 0.35, largeur + 0.82), [
    new MeshStandardMaterial({ map: banniere }),
    new MeshStandardMaterial({ map: banniereInversee }),
    metal, metal, metal, metal,
  ])
  portique.position.y = 1.75
  portique.castShadow = true
  groupe.add(portique)

  groupe.position.set(x, 0, -y)
  groupe.rotation.y = angle
  scene.add(groupe)
}

export function installerArbres(scene: Scene, positions: readonly number[]): void {
  const nombre = positions.length / 2
  if (nombre === 0) return
  const feuillage = new InstancedMesh(
    new ConeGeometry(0.9, 2.4, 7).translate(0, 1.9, 0),
    new MeshStandardMaterial({ roughness: 0.9, flatShading: true }),
    nombre,
  )
  const troncs = new InstancedMesh(
    new CylinderGeometry(0.12, 0.16, 0.7, 5).translate(0, 0.35, 0),
    new MeshStandardMaterial({ color: 0x5b3a1e, roughness: 1 }),
    nombre,
  )
  const matrice = new Matrix4()
  const position = new Vector3()
  const rotation = new Quaternion()
  const echelle = new Vector3()
  const couleur = new Color()
  for (let i = 0; i < nombre; i++) {
    const x = positions[2 * i]!
    const y = positions[2 * i + 1]!
    const hasard = Math.abs(Math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1
    matrice.compose(
      position.set(x, 0, -y),
      rotation.setFromAxisAngle(AXE_VERTICAL, hasard * 6.28),
      echelle.setScalar(0.7 + hasard),
    )
    feuillage.setMatrixAt(i, matrice)
    troncs.setMatrixAt(i, matrice)
    feuillage.setColorAt(i, couleur.setHSL(0.27 + hasard * 0.08, 0.5, 0.22 + hasard * 0.1))
  }
  feuillage.castShadow = troncs.castShadow = true
  feuillage.matrixAutoUpdate = troncs.matrixAutoUpdate = false
  scene.add(feuillage, troncs)
}
