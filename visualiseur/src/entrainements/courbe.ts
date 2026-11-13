import { echapper, formatEntier } from '../outils.ts'
import type { Courbe } from '../types.ts'

export interface Serie {
  readonly nom: string
  readonly couleur: string
  readonly courbe: Courbe
}

const LARGEUR = 720
const HAUTEUR = 240
const MARGE = { haut: 12, droite: 16, bas: 28, gauche: 52 } as const
const GRADUATIONS = 4

function pasRond(etendue: number): number {
  const brut = etendue / GRADUATIONS
  const ordre = 10 ** Math.floor(Math.log10(brut))
  const mantisse = brut / ordre
  return (mantisse >= 5 ? 5 : mantisse >= 2 ? 2 : 1) * ordre
}

const compact = (v: number): string =>
  Math.abs(v) >= 1e6 ? `${v / 1e6} M` : Math.abs(v) >= 1e3 ? `${v / 1e3} k` : String(Number(v.toFixed(2)))

export function dessinerCourbe(conteneur: HTMLElement, series: readonly Serie[], reperes: readonly number[]): void {
  const pleines = series.filter((s) => s.courbe.pas.length > 1)
  if (pleines.length === 0) {
    conteneur.innerHTML = '<p class="vide">Ce run n’a pas enregistré cette courbe.</p>'
    return
  }
  let xMax = 0
  let yMin = Infinity
  let yMax = -Infinity
  for (const { courbe } of pleines) {
    xMax = Math.max(xMax, courbe.pas.at(-1)!)
    for (const v of courbe.valeurs) {
      yMin = Math.min(yMin, v)
      yMax = Math.max(yMax, v)
    }
  }
  const echelon = pasRond(yMax - yMin || 1)
  yMin = Math.floor(yMin / echelon) * echelon
  yMax = Math.ceil(yMax / echelon) * echelon
  if (yMax === yMin) yMax = yMin + echelon
  const largeurTrace = LARGEUR - MARGE.gauche - MARGE.droite
  const hauteurTrace = HAUTEUR - MARGE.haut - MARGE.bas
  const x = (pas: number): number => MARGE.gauche + (pas / xMax) * largeurTrace
  const y = (v: number): number => MARGE.haut + (1 - (v - yMin) / (yMax - yMin)) * hauteurTrace

  let grille = ''
  for (let v = yMin; v <= yMax + echelon / 2; v += echelon) {
    grille += `<line class="grille" x1="${MARGE.gauche}" x2="${LARGEUR - MARGE.droite}" y1="${y(v)}" y2="${y(v)}" />
      <text class="axe" x="${MARGE.gauche - 8}" y="${y(v) + 4}" text-anchor="end">${compact(v)}</text>`
  }
  const echelonX = pasRond(xMax)
  for (let pas = 0; pas <= xMax; pas += echelonX) {
    grille += `<text class="axe" x="${x(pas)}" y="${HAUTEUR - 8}" text-anchor="middle">${compact(pas)}</text>`
  }
  const marques = reperes
    .filter((pas) => pas <= xMax)
    .map((pas) => `<line class="repere" x1="${x(pas)}" x2="${x(pas)}" y1="${MARGE.haut}" y2="${HAUTEUR - MARGE.bas}" />`)
    .join('')
  const traits = pleines
    .map(({ courbe, couleur }) => {
      const points = courbe.pas.map((pas, i) => `${x(pas).toFixed(1)},${y(courbe.valeurs[i]!).toFixed(1)}`).join(' ')
      return `<polyline class="serie" points="${points}" stroke="${couleur}" />`
    })
    .join('')
  const pastilles = pleines.map(({ couleur }) => `<circle class="point" r="4" fill="${couleur}" />`).join('')
  const legende =
    pleines.length > 1
      ? `<div class="legende-courbe">${pleines
          .map((s) => `<span><i style="background:${s.couleur}"></i>${echapper(s.nom)}</span>`)
          .join('')}</div>`
      : ''

  conteneur.innerHTML = `${legende}
    <div class="trace-courbe">
      <svg viewBox="0 0 ${LARGEUR} ${HAUTEUR}" role="img">
        ${grille}${marques}${traits}
        <line class="viseur" y1="${MARGE.haut}" y2="${HAUTEUR - MARGE.bas}" />
        ${pastilles}
      </svg>
      <div class="bulle" hidden></div>
    </div>`

  const svg = conteneur.querySelector('svg')!
  const viseur = conteneur.querySelector<SVGLineElement>('.viseur')!
  const points = [...conteneur.querySelectorAll<SVGCircleElement>('.point')]
  const bulle = conteneur.querySelector<HTMLElement>('.bulle')!

  function indiceProche(courbe: Courbe, pas: number): number {
    let bas = 0
    let haut = courbe.pas.length - 1
    while (haut - bas > 1) {
      const milieu = (bas + haut) >> 1
      if (courbe.pas[milieu]! < pas) bas = milieu
      else haut = milieu
    }
    return pas - courbe.pas[bas]! < courbe.pas[haut]! - pas ? bas : haut
  }

  function cacher(): void {
    bulle.hidden = true
    svg.classList.remove('survol')
  }

  svg.addEventListener('pointermove', (e) => {
    const cadre = svg.getBoundingClientRect()
    const pas = (((e.clientX - cadre.left) / cadre.width) * LARGEUR - MARGE.gauche) / largeurTrace * xMax
    if (pas < 0 || pas > xMax) return cacher()
    let pasAimante = 0
    let ecart = Infinity
    for (const { courbe } of pleines) {
      const proche = courbe.pas[indiceProche(courbe, pas)]!
      if (Math.abs(proche - pas) < ecart) {
        ecart = Math.abs(proche - pas)
        pasAimante = proche
      }
    }
    viseur.setAttribute('x1', String(x(pasAimante)))
    viseur.setAttribute('x2', String(x(pasAimante)))
    let lignes = ''
    pleines.forEach(({ courbe, couleur, nom }, n) => {
      const termine = pasAimante > courbe.pas.at(-1)!
      const i = indiceProche(courbe, pasAimante)
      points[n]!.style.display = termine ? 'none' : ''
      points[n]!.setAttribute('cx', String(x(courbe.pas[i]!)))
      points[n]!.setAttribute('cy', String(y(courbe.valeurs[i]!)))
      lignes += `<div><i style="background:${couleur}"></i><span>${pleines.length > 1 ? echapper(nom) : 'Valeur'}</span><b>${termine ? '—' : courbe.valeurs[i]!.toFixed(2)}</b></div>`
    })
    bulle.innerHTML = `<div class="entete">${formatEntier(pasAimante)} pas</div>${lignes}`
    bulle.hidden = false
    svg.classList.add('survol')
    const gauche = (x(pasAimante) / LARGEUR) * cadre.width
    bulle.style.transform = `translate(${gauche > cadre.width / 2 ? gauche - bulle.offsetWidth - 12 : gauche + 12}px, 8px)`
  })
  svg.addEventListener('pointerleave', cacher)
}
