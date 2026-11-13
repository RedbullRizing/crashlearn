const MARGE = 8

export function miniature(trace: readonly number[]): string {
  let xMin = Infinity
  let xMax = -Infinity
  let yMin = Infinity
  let yMax = -Infinity
  for (let i = 0; i < trace.length; i += 2) {
    const x = trace[i]!
    const y = -trace[i + 1]!
    if (x < xMin) xMin = x
    if (x > xMax) xMax = x
    if (y < yMin) yMin = y
    if (y > yMax) yMax = y
  }
  let points = ''
  for (let i = 0; i < trace.length; i += 2) {
    points += `${(trace[i]! - xMin).toFixed(1)},${(-trace[i + 1]! - yMin).toFixed(1)} `
  }
  const largeur = xMax - xMin
  const hauteur = yMax - yMin
  const rayon = Math.max(largeur, hauteur) / 45
  return `<svg viewBox="${-MARGE} ${-MARGE} ${largeur + 2 * MARGE} ${hauteur + 2 * MARGE}" aria-hidden="true">
    <polygon class="trace" points="${points}" />
    <circle class="depart" cx="${(trace[0]! - xMin).toFixed(1)}" cy="${(-trace[1]! - yMin).toFixed(1)}" r="${rayon.toFixed(1)}" />
  </svg>`
}
