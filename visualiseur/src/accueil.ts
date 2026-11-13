import { couleurDe, echapper, element, formatDuree } from './outils.ts'
import { miniature } from './miniature.ts'
import type { Fiche } from './types.ts'

function carte(fiche: Fiche, rang: number): string {
  const pastilles = fiche.pilotes
    .map((_, i) => `<span class="pastille" style="background:${couleurDe(i)}"></span>`)
    .join('')
  const pilotes = fiche.pilotes.length === 1 ? fiche.pilotes[0] : `${fiche.pilotes.length} voitures`
  return `<a class="carte" style="--rang:${rang}" href="?course=${encodeURIComponent(fiche.nom)}">
    ${miniature(fiche.trace)}
    <div class="circuit">${echapper(fiche.circuit)}</div>
    <div class="nom">${echapper(fiche.nom)}</div>
    <div class="details">
      <span class="pilotes">${pastilles}<span class="texte">${echapper(pilotes)}</span></span>
      <span class="chiffres">${formatDuree(fiche.duree)}</span>
    </div>
  </a>`
}

const pluriel = (n: number, mot: string): string => `${n} ${mot}${n > 1 ? 's' : ''}`

export function afficherAccueil(fiches: readonly Fiche[], erreur?: string): void {
  if (erreur) {
    const alerte = element('erreur')
    alerte.hidden = false
    alerte.textContent = erreur
  }
  const circuits = [...new Set(fiches.map((f) => f.circuit))].sort()
  element('resume').textContent = fiches.length
    ? `${pluriel(fiches.length, 'course')} sur ${pluriel(circuits.length, 'circuit')}`
    : 'Aucune course convertie pour l’instant.'

  const demande = new URLSearchParams(location.search).get('circuit')
  let filtre = demande !== null && circuits.includes(demande) ? demande : null
  const filtres = element('filtres')
  const cartes = element('cartes')

  function dessiner(): void {
    filtres.hidden = circuits.length < 2
    filtres.innerHTML = [null, ...circuits]
      .map(
        (c) =>
          `<button class="puce" data-circuit="${echapper(c ?? '')}" aria-pressed="${c === filtre}">${echapper(c ?? 'Tous les circuits')}</button>`,
      )
      .join('')
    cartes.innerHTML = fiches
      .filter((f) => filtre === null || f.circuit === filtre)
      .map(carte)
      .join('')
  }

  filtres.onclick = (e) => {
    const puce = (e.target as Element).closest<HTMLElement>('.puce')
    if (!puce) return
    filtre = puce.dataset['circuit'] || null
    history.replaceState(null, '', filtre ? `?circuit=${encodeURIComponent(filtre)}` : './')
    dessiner()
  }
  dessiner()
  cartes.classList.add('deja-affiche')
}
