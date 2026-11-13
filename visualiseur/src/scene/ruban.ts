import { BufferAttribute, BufferGeometry } from 'three'

export interface Ruban {
  readonly hauteur?: number
  readonly largeur?: number
  readonly altitude?: number
  readonly metresParMotif: number
}

export function rubanLeLongDuContour(contour: readonly number[], ruban: Ruban): BufferGeometry {
  const { hauteur = 0, largeur = 0, altitude = 0, metresParMotif } = ruban
  const n = contour.length / 2
  const positions = new Float32Array((n + 1) * 6)
  const uvs = new Float32Array((n + 1) * 4)
  const indices = new Uint32Array(n * 6)
  let longueur = 0
  for (let i = 0; i <= n; i++) {
    const k = (i % n) * 2
    const x = contour[k]!
    const y = contour[k + 1]!
    const avant = ((i - 1 + n) % n) * 2
    if (i > 0) longueur += Math.hypot(x - contour[avant]!, y - contour[avant + 1]!)
    const p = i * 6
    if (hauteur > 0) {
      positions[p] = positions[p + 3] = x
      positions[p + 1] = 0
      positions[p + 4] = hauteur
      positions[p + 2] = positions[p + 5] = -y
    } else {
      const apres = ((i + 1) % n) * 2
      const dx = contour[apres]! - contour[avant]!
      const dy = contour[apres + 1]! - contour[avant + 1]!
      const demi = largeur / 2 / (Math.hypot(dx, dy) || 1)
      positions[p] = x + dy * demi
      positions[p + 2] = -(y - dx * demi)
      positions[p + 3] = x - dy * demi
      positions[p + 5] = -(y + dx * demi)
      positions[p + 1] = positions[p + 4] = altitude
    }
    const u = longueur / metresParMotif
    uvs[i * 4] = uvs[i * 4 + 2] = u
    uvs[i * 4 + 3] = 1
    if (i < n) {
      const s = i * 2
      indices.set([s, s + 2, s + 1, s + 1, s + 2, s + 3], i * 6)
    }
  }
  const geometrie = new BufferGeometry()
  geometrie.setAttribute('position', new BufferAttribute(positions, 3))
  geometrie.setAttribute('uv', new BufferAttribute(uvs, 2))
  geometrie.setIndex(new BufferAttribute(indices, 1))
  geometrie.computeVertexNormals()
  return geometrie
}
