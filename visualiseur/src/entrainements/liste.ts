import { echapper, element, formatDate, formatEntier } from '../outils.ts'
import type { Entrainement } from '../types.ts'
import { mesure } from './glossaire.ts'

const APERCU = ['course/taux_completion', 'tour/meilleur'] as const

function carte(run: Entrainement, rang: number): string {
  const pas = typeof run.config['pas'] === 'number' ? `${formatEntier(run.config['pas'])} pas` : ''
  const chiffres = APERCU.map((cle) => {
    const valeur = run.bilan[cle]
    return `<div><dt>${echapper(mesure(cle).titre)}</dt><dd class="chiffres">${valeur === undefined ? '—' : mesure(cle).format(valeur)}</dd></div>`
  }).join('')
  return `<a class="carte run" style="--rang:${Math.min(rang, 12)}" href="?run=${encodeURIComponent(run.nom)}">
    <div class="haut">
      <span class="circuit">${echapper(run.algo || 'run')}</span>
      <span class="badge ${run.origine}">${run.origine === 'archive' ? 'Archivé' : 'Local'}</span>
    </div>
    <div class="nom">${echapper(run.pilote || run.nom)}</div>
    <div class="quand">${echapper(formatDate(run.date))}${pas ? ` · ${pas}` : ''}</div>
    <dl>${chiffres}</dl>
  </a>`
}

export function afficherEntrainements(runs: readonly Entrainement[]): void {
  const pilotes = [...new Set(runs.map((r) => r.pilote).filter(Boolean))].sort()
  const filtres = element('filtres')
  const cartes = element('cartes')
  let filtre: string | null = null

  function dessiner(): void {
    filtres.hidden = pilotes.length < 2
    filtres.innerHTML = [null, ...pilotes]
      .map((p) => `<button class="puce" data-pilote="${echapper(p ?? '')}" aria-pressed="${p === filtre}">${echapper(p ?? 'Tous les pilotes')}</button>`)
      .join('')
    const visibles = runs.filter((r) => filtre === null || r.pilote === filtre)
    cartes.innerHTML = visibles.length
      ? visibles.map(carte).join('')
      : '<p class="vide">Aucun entraînement exporté. Lance : <code>make vue-runs</code></p>'
  }

  filtres.onclick = (e) => {
    const puce = (e.target as Element).closest<HTMLElement>('.puce')
    if (!puce) return
    filtre = puce.dataset['pilote'] || null
    dessiner()
  }
  dessiner()
  cartes.classList.add('deja-affiche')
}
