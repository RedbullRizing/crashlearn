import { afficherAccueil } from './accueil.ts'
import { element, lireCourse, lireEntrainements, lireFiches } from './outils.ts'

function ouvrirAccueil(onglet: 'courses' | 'entrainements'): void {
  element('accueil').hidden = false
  for (const lien of element('onglets').children) {
    lien.setAttribute('aria-current', String((lien as HTMLElement).dataset['onglet'] === onglet))
  }
  element('ajout-course').hidden = onglet !== 'courses'
  element('ajout-run').hidden = onglet !== 'entrainements'
}

async function accueilDesCourses(erreur?: string): Promise<void> {
  ouvrirAccueil('courses')
  afficherAccueil(await lireFiches(), erreur)
}

async function accueilDesEntrainements(erreur?: string): Promise<void> {
  ouvrirAccueil('entrainements')
  const [{ runs }, { afficherEntrainements }] = await Promise.all([lireEntrainements(), import('./entrainements/liste.ts')])
  element('titre-accueil').textContent = 'Choisir un entraînement'
  element('resume').textContent = `${runs.length} run${runs.length > 1 ? 's' : ''}, dont ${runs.filter((r) => r.origine === 'archive').length} archivé(s)`
  if (erreur) {
    element('erreur').hidden = false
    element('erreur').textContent = erreur
  }
  afficherEntrainements(runs)
}

async function demarrer(): Promise<void> {
  const requete = new URLSearchParams(location.search)
  const course = requete.get('course')
  const run = requete.get('run')
  if (run) {
    const [donnees, { afficherFiche }] = await Promise.all([lireEntrainements(), import('./entrainements/fiche.ts')])
    if (!afficherFiche(donnees, run, requete.get('avec'))) {
      await accueilDesEntrainements(`Entraînement « ${run} » introuvable. Lance : make vue-runs`)
    }
    return
  }
  if (!course) return requete.get('onglet') === 'entrainements' ? accueilDesEntrainements() : accueilDesCourses()
  try {
    const [donnees, { lancerCourse }] = await Promise.all([lireCourse(course), import('./course/session.ts')])
    lancerCourse(donnees)
  } catch (erreur) {
    console.error(erreur)
    await accueilDesCourses(`Course « ${course} » introuvable. Lance : make vue NAME=${course}`)
  }
}

void demarrer()
