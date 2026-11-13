import { miniature } from '../miniature.ts'
import { echapper, element, formatDate, formatEntier } from '../outils.ts'
import type { Entrainement, Entrainements, Reglages } from '../types.ts'
import { dessinerCourbe } from './courbe.ts'
import { COURBES, FORMULE_RECOMPENSE, REGLAGES, SECTIONS, mesure } from './glossaire.ts'

const COULEUR_RUN = '#3987e5'
const COULEUR_COMPARE = '#d95926'
const LONGUEUR_COURTE = 16
const CLES_MASQUEES = new Set(['circuits', 'circuits_eval', 'ppo', 'env', 'recompense'])

function afficherValeur(valeur: unknown): string {
  if (valeur === undefined) return '—'
  if (typeof valeur === 'boolean') return valeur ? 'oui' : 'non'
  if (typeof valeur === 'number') return Number.isInteger(valeur) && Math.abs(valeur) >= 10000 ? formatEntier(valeur) : String(valeur)
  if (Array.isArray(valeur)) return valeur.length ? valeur.join(', ') : 'aucun'
  return String(valeur)
}

function reglagesDe(config: Reglages, section: string): Reglages {
  if (section === '') return Object.fromEntries(Object.entries(config).filter(([cle]) => !CLES_MASQUEES.has(cle)))
  const bloc = config[section]
  return typeof bloc === 'object' && bloc !== null ? (bloc as Reglages) : {}
}

function tableauDesReglages(run: Entrainement, autre: Entrainement | undefined): string {
  return SECTIONS.map(({ cle: section, titre }) => {
    const a = reglagesDe(run.config, section)
    const b = autre ? reglagesDe(autre.config, section) : {}
    const cles = [...new Set([...Object.keys(a), ...Object.keys(b)])]
    if (cles.length === 0) return ''
    const lignes = cles
      .map((cle) => {
        const gauche = afficherValeur(a[cle])
        const droite = afficherValeur(b[cle])
        const aide = REGLAGES[section ? `${section}.${cle}` : cle]
        return `<tr class="${autre && gauche !== droite ? 'ecart' : ''}">
          <th scope="row"><code>${echapper(cle)}</code>${aide ? `<span>${echapper(aide)}</span>` : ''}</th>
          <td class="chiffres${gauche.length > LONGUEUR_COURTE ? ' long' : ''}">${echapper(gauche)}</td>
          ${autre ? `<td class="chiffres${droite.length > LONGUEUR_COURTE ? ' long' : ''}">${echapper(droite)}</td>` : ''}
        </tr>`
      })
      .join('')
    const formule = section === 'recompense' ? `<p class="formule">${echapper(FORMULE_RECOMPENSE)}</p>` : ''
    return `<section class="bloc"><h3>${echapper(titre)}</h3>${formule}<table class="reglages">${lignes}</table></section>`
  }).join('')
}

function tuiles(run: Entrainement, autre: Entrainement | undefined): string {
  const cles = [...new Set([...Object.keys(run.bilan), ...Object.keys(autre?.bilan ?? {})])]
  if (cles.length === 0) return '<p class="vide">Ce run n’a pas écrit de bilan.</p>'
  return `<div class="tuiles">${cles
    .map((cle) => {
      const { titre, format } = mesure(cle)
      const a = run.bilan[cle]
      const b = autre?.bilan[cle]
      return `<div class="tuile">
        <div class="etiquette">${echapper(titre)}</div>
        <div class="valeur chiffres">${a === undefined ? '—' : format(a)}</div>
        ${autre ? `<div class="compare chiffres"><i style="background:${COULEUR_COMPARE}"></i>${b === undefined ? '—' : format(b)}</div>` : ''}
      </div>`
    })
    .join('')}</div>`
}

function circuits(titre: string, noms: readonly string[], traces: Entrainements['circuits']): string {
  if (noms.length === 0) return ''
  return `<section class="bloc"><h3>${echapper(titre)} <span class="compte">${noms.length}</span></h3>
    <div class="circuits">${noms
      .map((nom) => `<figure>${traces[nom] ? miniature(traces[nom]) : ''}<figcaption>${echapper(nom)}</figcaption></figure>`)
      .join('')}</div></section>`
}

function entete(run: Entrainement, tous: readonly Entrainement[], autre: Entrainement | undefined): string {
  const commit = run.git.commit ? `commit ${run.git.commit}${run.git.modifie ? ' + modifications non commitées' : ''}` : ''
  const sauvegardes = run.sauvegardes.length ? `${run.sauvegardes.length} sauvegardes` : ''
  const details = [formatDate(run.date), commit, sauvegardes].filter(Boolean).join(' · ')
  const choix = tous
    .filter((r) => r.nom !== run.nom)
    .map((r) => `<option value="${echapper(r.nom)}" ${r.nom === autre?.nom ? 'selected' : ''}>${echapper(r.nom)}</option>`)
    .join('')
  return `<header>
    <a class="retour" href="?onglet=entrainements">← Entraînements</a>
    <p class="surtitre">${echapper(run.pilote)} · ${echapper(run.algo)}
      <span class="badge ${run.origine}">${run.origine === 'archive' ? 'Archivé' : 'Local'}</span></p>
    <h1>${echapper(run.nom)}</h1>
    <p class="sous-titre">${echapper(details)}</p>
    ${run.note ? `<p class="note">${echapper(run.note)}</p>` : ''}
    <label class="comparer">Comparer avec
      <select id="comparer"><option value="">aucun run</option>${choix}</select>
    </label>
    ${autre ? `<p class="legende-compare"><span><i style="background:${COULEUR_RUN}"></i>${echapper(run.nom)}</span><span><i style="background:${COULEUR_COMPARE}"></i>${echapper(autre.nom)}</span></p>` : ''}
  </header>`
}

export function afficherFiche(donnees: Entrainements, nom: string, nomCompare: string | null): boolean {
  const run = donnees.runs.find((r) => r.nom === nom)
  if (!run) return false
  const autre = donnees.runs.find((r) => r.nom === nomCompare && r.nom !== nom)
  const page = element('fiche')
  page.hidden = false
  document.title = `${run.nom} — Crash & Learn`

  const reperes = !autre && run.sauvegardes.length ? ' Les pointillés marquent les sauvegardes du modèle.' : ''
  const courbes = Object.keys(COURBES)
    .filter((cle) => run.courbes[cle] || autre?.courbes[cle])
    .map((cle) => `<section class="bloc"><h3>${echapper(COURBES[cle]!.titre)}</h3>
      <p class="aide">${echapper(COURBES[cle]!.aide)}${reperes}</p><div class="courbe" data-courbe="${echapper(cle)}"></div></section>`)
    .join('')

  page.innerHTML = `${entete(run, donnees.runs, autre)}
    <section class="bloc"><h3>Bilan final</h3>
      <p class="aide">Chiffres écrits par le run dans <code>bilan.json</code>, mesurés sur ses courses d’évaluation.</p>
      ${tuiles(run, autre)}</section>
    ${courbes}
    <div class="colonnes">${tableauDesReglages(run, autre)}</div>
    ${circuits('Circuits d’entraînement', run.circuits, donnees.circuits)}
    ${circuits('Circuits de validation', run.circuits_eval, donnees.circuits)}`

  for (const zone of page.querySelectorAll<HTMLElement>('[data-courbe]')) {
    const cle = zone.dataset['courbe']!
    const series = [{ nom: run.nom, couleur: COULEUR_RUN, courbe: run.courbes[cle] ?? { pas: [], valeurs: [] } }]
    if (autre?.courbes[cle]) series.push({ nom: autre.nom, couleur: COULEUR_COMPARE, courbe: autre.courbes[cle] })
    dessinerCourbe(zone, series, autre ? [] : run.sauvegardes)
  }
  element<HTMLSelectElement>('comparer').addEventListener('change', (e) => {
    const choisi = (e.target as HTMLSelectElement).value
    location.search = `?run=${encodeURIComponent(run.nom)}${choisi ? `&avec=${encodeURIComponent(choisi)}` : ''}`
  })
  return true
}
