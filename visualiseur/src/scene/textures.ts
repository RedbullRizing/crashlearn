import { CanvasTexture, RepeatWrapping, SRGBColorSpace } from 'three'

type Dessin = (ctx: CanvasRenderingContext2D, largeur: number, hauteur: number) => void

export function texture(largeur: number, hauteur: number, dessiner: Dessin, repetee = true): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = largeur
  canvas.height = hauteur
  dessiner(canvas.getContext('2d')!, largeur, hauteur)
  const t = new CanvasTexture(canvas)
  t.colorSpace = SRGBColorSpace
  t.anisotropy = 8
  if (repetee) t.wrapS = t.wrapT = RepeatWrapping
  return t
}

export function grain(ctx: CanvasRenderingContext2D, l: number, h: number, base: string, nombre: number): void {
  ctx.fillStyle = base
  ctx.fillRect(0, 0, l, h)
  for (let i = 0; i < nombre; i++) {
    ctx.fillStyle = `rgba(${Math.random() > 0.5 ? '255,255,255' : '0,0,0'},${Math.random() * 0.08})`
    ctx.fillRect(Math.random() * l, Math.random() * h, 2, 2)
  }
}

export const bandes = (a: string, b: string): CanvasTexture =>
  texture(64, 8, (ctx, l, h) => {
    ctx.fillStyle = a
    ctx.fillRect(0, 0, l / 2, h)
    ctx.fillStyle = b
    ctx.fillRect(l / 2, 0, l / 2, h)
  })
