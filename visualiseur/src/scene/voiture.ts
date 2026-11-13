import {
  BoxGeometry, CanvasTexture, Color, CylinderGeometry, ExtrudeGeometry, Group, Mesh, MeshPhysicalMaterial,
  MeshStandardMaterial, SRGBColorSpace, Shape, SphereGeometry, Sprite, SpriteMaterial, TorusGeometry, Vector2,
} from 'three'
import type { BufferGeometry, Material } from 'three'
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js'

type Contour = readonly (readonly [number, number])[]

const RAYON_ROUE = 0.055
const ROUES: Contour = [[0.19, 0.13], [0.19, -0.13], [-0.19, 0.13], [-0.19, -0.13]]
const COQUE: Contour = [[0.29, 0.018], [0.2, 0.035], [0.08, 0.06], [-0.2, 0.06], [-0.27, 0.04], [-0.27, -0.04], [-0.2, -0.06], [0.08, -0.06], [0.2, -0.035], [0.29, -0.018]]
const PONTONS: Contour = [[0.06, 0.1], [-0.12, 0.105], [-0.2, 0.07], [-0.2, -0.07], [-0.12, -0.105], [0.06, -0.1], [0.09, -0.06], [0.09, 0.06]]
const CAPOT: Contour = [[0, 0.04], [-0.07, 0.045], [-0.24, 0.02], [-0.24, -0.02], [-0.07, -0.045], [0, -0.04]]
const FOND_PLAT: Contour = [[0.12, 0.11], [-0.24, 0.12], [-0.24, -0.12], [0.12, -0.11]]
const TAILLE_ETIQUETTE = [0.1, 0.025] as const
const ASSOMBRI_SI_SORTIE = 0.25

function profil(contour: Contour, epaisseur: number, arrondi: number, altitude: number): BufferGeometry {
  const forme = new Shape(contour.map(([x, y]) => new Vector2(x, y)))
  return new ExtrudeGeometry(forme, {
    depth: epaisseur, bevelEnabled: true, bevelThickness: arrondi, bevelSize: arrondi, bevelSegments: 2,
  }).rotateX(-Math.PI / 2).translate(0, altitude, 0)
}

const boite = (l: number, h: number, p: number, x: number, y: number, z = 0): BufferGeometry =>
  new BoxGeometry(l, h, p).translate(x, y, z)

function fusion(geometries: BufferGeometry[]): BufferGeometry {
  const fusionnee = mergeGeometries(geometries.map((g) => (g.index ? g.toNonIndexed() : g)))
  for (const g of geometries) g.dispose()
  return fusionnee
}

interface Pieces {
  readonly peinture: BufferGeometry
  readonly carbone: BufferGeometry
  readonly casque: BufferGeometry
  readonly pneu: BufferGeometry
  readonly jante: BufferGeometry
  readonly materiauCarbone: Material
  readonly materiauCasque: Material
  readonly materiauPneu: Material
  readonly materiauJante: Material
}

let piecesCommunes: Pieces | undefined

function pieces(): Pieces {
  piecesCommunes ??= {
    peinture: fusion([
      profil(COQUE, 0.045, 0.012, 0.035),
      profil(PONTONS, 0.035, 0.01, 0.03),
      profil(CAPOT, 0.03, 0.012, 0.09),
      boite(0.012, 0.035, 0.008, 0.3, 0.045, 0.151),
      boite(0.012, 0.035, 0.008, 0.3, 0.045, -0.151),
      boite(0.055, 0.008, 0.27, -0.275, 0.2),
    ]),
    carbone: fusion([
      profil(FOND_PLAT, 0.006, 0.002, 0.018),
      new TorusGeometry(0.045, 0.006, 6, 16, Math.PI).rotateY(Math.PI / 2).translate(-0.02, 0.105, 0),
      boite(0.05, 0.008, 0.31, 0.3, 0.03),
      boite(0.04, 0.008, 0.27, -0.27, 0.165),
      boite(0.05, 0.11, 0.008, -0.272, 0.15, 0.135),
      boite(0.05, 0.11, 0.008, -0.272, 0.15, -0.135),
      boite(0.012, 0.012, 0.27, 0.19, 0.055),
      boite(0.012, 0.012, 0.27, -0.19, 0.055),
    ]),
    casque: new SphereGeometry(0.032, 16, 12).translate(-0.03, 0.125, 0),
    pneu: new CylinderGeometry(RAYON_ROUE, RAYON_ROUE, 0.055, 24).rotateX(Math.PI / 2),
    jante: new CylinderGeometry(RAYON_ROUE * 0.6, RAYON_ROUE * 0.6, 0.057, 10).rotateX(Math.PI / 2),
    materiauCarbone: new MeshStandardMaterial({ color: 0x15171c, metalness: 0.4, roughness: 0.45 }),
    materiauCasque: new MeshStandardMaterial({ color: 0x0a0c10, metalness: 0.9, roughness: 0.1 }),
    materiauPneu: new MeshStandardMaterial({ color: 0x0d0d0d, roughness: 0.95 }),
    materiauJante: new MeshStandardMaterial({ color: 0xc8ccd4, metalness: 0.9, roughness: 0.25 }),
  }
  return piecesCommunes
}

function etiquette(texte: string, couleur: string): Sprite {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 64
  const ctx = canvas.getContext('2d')!
  ctx.fillStyle = 'rgba(10,12,18,0.75)'
  ctx.beginPath()
  ctx.roundRect(0, 8, 256, 48, 12)
  ctx.fill()
  ctx.fillStyle = couleur
  ctx.fillRect(14, 22, 8, 20)
  ctx.fillStyle = '#fff'
  ctx.font = '700 30px system-ui, sans-serif'
  ctx.textBaseline = 'middle'
  ctx.fillText(texte, 34, 33)
  const image = new CanvasTexture(canvas)
  image.colorSpace = SRGBColorSpace
  const sprite = new Sprite(new SpriteMaterial({ map: image, depthTest: false, sizeAttenuation: false }))
  sprite.position.y = 0.42
  sprite.renderOrder = 10
  return sprite
}

export class Voiture {
  readonly groupe = new Group()
  private readonly nomAffiche: Sprite
  private readonly peinture: MeshPhysicalMaterial
  private readonly couleur: Color
  private readonly roues: Group[] = []
  private readonly pivotsAvant: Group[] = []
  private sortie = false

  constructor(couleur: string, nom: string) {
    const p = pieces()
    this.couleur = new Color(couleur)
    this.peinture = new MeshPhysicalMaterial({
      color: couleur, metalness: 0.2, roughness: 0.35, clearcoat: 1, clearcoatRoughness: 0.08,
    })
    this.groupe.add(
      new Mesh(p.peinture, this.peinture),
      new Mesh(p.carbone, p.materiauCarbone),
      new Mesh(p.casque, p.materiauCasque),
    )
    for (const [x, z] of ROUES) {
      const pivot = new Group()
      pivot.position.set(x, RAYON_ROUE, z)
      const roue = new Group()
      roue.add(new Mesh(p.pneu, p.materiauPneu), new Mesh(p.jante, p.materiauJante))
      pivot.add(roue)
      this.groupe.add(pivot)
      this.roues.push(roue)
      if (x > 0) this.pivotsAvant.push(pivot)
    }
    this.groupe.traverse((objet) => {
      objet.castShadow = objet instanceof Mesh
    })
    this.nomAffiche = etiquette(nom, couleur)
    this.groupe.add(this.nomAffiche)
  }

  placer(x: number, y: number, cap: number, braquage: number, distanceParcourue: number): void {
    this.groupe.position.set(x, 0, -y)
    this.groupe.rotation.y = cap
    for (const pivot of this.pivotsAvant) pivot.rotation.y = braquage
    const tour = -distanceParcourue / RAYON_ROUE
    for (const roue of this.roues) roue.rotation.z = tour
  }

  montrer(visible: boolean, sortie: boolean): void {
    this.groupe.visible = visible
    if (sortie === this.sortie) return
    this.sortie = sortie
    this.peinture.color.copy(this.couleur).multiplyScalar(sortie ? ASSOMBRI_SI_SORTIE : 1)
  }

  etiqueter(visible: boolean, zoom: number): void {
    this.nomAffiche.visible = visible
    this.nomAffiche.scale.set(TAILLE_ETIQUETTE[0] * zoom, TAILLE_ETIQUETTE[1] * zoom, 1)
  }
}
