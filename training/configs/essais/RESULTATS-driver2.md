# Essais driver2, du 13/11 au 21/11/2026 (CRA-100)

Le détail de chaque essai et sa discussion sont dans les commentaires de CRA-100. Les configurations sont à côté de ce fichier (`driver2-*.yaml`), les runs dans `archives/driver2-*` (courbes, `meta.json`, note).

## Méthode

- **Un seul réglage à la fois.** Chaque essai copie le pilote livré à ce moment-là et change une ligne.
- **Deux bancs de mesure**, déterministes, mêmes courses pour tous :
  - `make evaluer` : 12 courses de validation (Oschersleben, Zandvoort, MexicoCity ; 4 par circuit, sec et pluie en alternance) ;
  - les 17 circuits d'entraînement, une course au sec et une sous la pluie par circuit (34 courses), avec `runs/courses_detail.py <run> entrainement`.

  `runs/courses_detail.py` est un script personnel, hors dépôt. Il appelle la même fonction `training.train.evaluer` que `make evaluer` (politique déterministe, pas de fin sur choc, 6 000 pas au plus), sur les 17 circuits d'**entraînement**, avec 2 courses par circuit : une au sec, une sous la pluie. La graine de course vaut 20000 par défaut, ou 30000 en 3e argument. Il écrit le détail de chaque course (résultat, temps au tour, chocs) dans `runs/<run>/courses-entrainement.csv` (`-g30000` pour l'autre graine). Avec `validation` au lieu de `entrainement`, il rejoue les 12 courses de `make evaluer`. Il pourra être intégré à `training/` si l'équipe le valide.

  Le critère est le **total sur 46 courses** (12 + 34), puis le temps : le classement du tournoi se fait à l'arrivée.
- **Les sauvegardes comptent.** Le modèle final et les sauvegardes à 300k et 400k (parfois plus) sont tous mesurés : le meilleur n'est pas toujours le dernier.
- **Deux graines.** Une configuration n'est jugée qu'avec au moins deux graines d'entraînement (7 et 2 dans la série automatique).
- **Deuxième graine de course.** Avant de livrer, le candidat repasse les 46 courses avec d'autres départs et une autre météo : `courses_detail.py <run> <groupe> 30000` au lieu de la graine 20000 par défaut.
- Les circuits de test (Spa, Budapest, Sochi) ne sont jamais utilisés.
- L'évaluation de fin d'entraînement (6 courses) n'est pas utilisée pour choisir : elle s'est révélée trompeuse.

## Essais un par un (meilleur modèle de chaque run)

« Total » : courses finies sur 46 (validation + 17 circuits), quand les 17 circuits ont été mesurés. Tours : meilleurs tours à Oschersleben / Zandvoort / MexicoCity, en secondes.

| Date | Essai | Config (`essais/`) | Graine | Meilleur modèle | Validation /12 | 17 circuits (sec / pluie) | Total /46 | Chocs/course | Tours O / Z / M |
|---|---|---|---|---|---|---|---|---|---|
| 13/11 | Run 1 : choc 5, 500k (**livré**) | — | 2 | final | 8 (6 / 2) | — | — | 6,2 | 34,8 / 50,5 / 46,4 |
| 20/11 | 2M pas | `driver2-2M.yaml` | 2 | 1M (final 3/12) | 5 | — | — | 45,8 | 35,7 / 47,0 / – |
| 20/11 | Run 1, autres graines | — | 7 / 13 | final | 8 / 6 | — | — | — | — |
| 20/11 | Abandon 30 | `driver2-dnf30.yaml` | 2 | 300k à final | 7 | — | — | 21 à 61 | — |
| 20/11 | Lots 512 / 128 | `driver2-lots512.yaml` | 2 | 400k | 8 | — | — | 49 | — |
| 20/11 | Choc 10 | `driver2-choc10.yaml` | 2 | 300k | 10 | — | — | 8 | — |
| 20/11 | Choc 10 (**livré**) | `driver2-choc10.yaml` | 7 | 300k | 11 | 17/34 (13 / 4) | 28 | 0 | 39,2 / – / – |
| 20/11 | Choc 10 | `driver2-choc10.yaml` | 13 | 400k | 4 | — | — | 75 | — |
| 20/11 | B2 : coût du temps 0,02 | `driver2-choc10-temps02.yaml` | 7 | 300k | 4 | — | — | 104 | — |
| 20/11 | B1 : `fin_sur_choc: false` (**livré**) | `driver2-choc10-sansfin.yaml` | 7 | 400k | 12 | 25/34 (14 / 11) | 37 | 4,8 | 41,2 / 59,4 / 54,4 |
| 20/11 | B1 | idem | 7 | final 500k | 10 | 19/34 (17 / 2) | 29 | 5,0 | — |
| 20/11 | C1 : abandon 30 | `driver2-sansfin-dnf30.yaml` | 7 | 300k | 12 | 24/34 (16 / 8) | 36 | 0,1 | 51,8 / 67,8 / 68,0 |
| 20/11 | C2 : coût du temps 0,02 | `driver2-sansfin-temps02.yaml` | 7 | 300k / 400k | 11 / 8 | — | — | 0,0 / 17,2 | 44,9 / 65,0 / 59,8 (300k) ; 39,9 / 55,2 / 52,2 (400k) |
| 20/11 | D1 : gamma 0,995 (**livré**) | `driver2-sansfin-gamma995.yaml` | 7 | 400k | 12 | 25/34 (14 / 11) | 37 | 0,2 | 41,4 / 60,0 / 55,7 |
| 20/11 | D2 : douceur 0,1 | `driver2-gamma995-douceur01.yaml` | 7 | final | 12 | 26/34 (15 / 11) | 38 | 1,2 | 43,9 / 66,3 / 61,0 |
| 20/11 | D3 : D2 sur 1M pas | `driver2-gamma995-douceur01-1M.yaml` | 7 | 700k (final 7/12) | 10 | — | — | 5,2 | 35,6 / 52,2 / 48,1 |
| 21/11 | D4 : D3 + learning rate 0,0002 | `driver2-gamma995-douceur01-1M-lr2e4.yaml` | 7 | — | 0 | — | — | — | immobile dès 350k |
| 21/11 | E1 : coût du temps 0,015 | `driver2-gamma995-temps015.yaml` | 7 | 300k | 11 | — | — | — | 62,2 / 90,2 / 86,0 |
| 21/11 | E2 : choc 7 | `driver2-gamma995-choc7.yaml` | 7 | 300k | 11 | — | — | — | 45,5 / 65,1 / 60,4 |
| 21/11 | E4 : config D1 | `driver2-sansfin-gamma995.yaml` | 2 | — | 0 | — | — | — | ne roule jamais |
| 21/11 | E4 : config D1 | idem | 13 | final | 11 | 22/34 (17 / 5) | 33 | 11 | 39,8 / 56,8 / 52,5 |
| 21/11 | E3 : `ent_coef` 0,005 | `driver2-gamma995-ent005.yaml` | 2 | final | 12 | 23/34 (14 / 9) | 35 | 0,3 | 37,2 / 53,8 / 49,5 |
| 21/11 | E3 : `ent_coef` 0,005 (**livré**) | idem | 7 | final | 12 | 27/34 (14 / 13) | 39 | 0 | 44,8 / 63,5 / 59,8 |
| 21/11 | F1 : E3 sur 1M pas | `driver2-ent005-1M.yaml` | 7 | final | 11 | 24/34 (15 / 9) | 35 | — | 37,8 / 55,2 / 51,4 |
| 21/11 | F2 : `pas_max` 4500 | `driver2-ent005-pasmax4500.yaml` | 7 | 300k | 12 | — | — | — | 51,6 / 74,8 / 68,1 |
| 21/11 | F3 : `ent_coef` 0,01 | `driver2-ent01.yaml` | 7 | 300k | 12 | 28/34 (15 / 13) | 40 | — | environ 10 % plus lent qu'E3 |
| 21/11 | F3 | idem | 7 | final | 11 | 27/34 (15 / 12) | 38 | — | 46,3 / 65,0 / 60,3 |
| 21/11 | G1 : réseau 128 × 128 | `driver2-reseau128.yaml` | 7 | final | 11 | — | — | 0 | 49,5 / 75,7 / 68,2 |
| 21/11 | G2 : réseau 128 × 128 sur 1M pas | `driver2-reseau128-1M.yaml` | 7 | 600k | 12 | 25/34 (14 / 11) | 37 | — | 48,6 / 72,2 / 65,7 |

## Série automatique du 21/11 (25 runs, base E3)

Chaque configuration change un réglage d'E3 et tourne avec les graines 7 et 2 (H1 : graine 7 seulement). Meilleur modèle parmi 300k, 400k et final. Les 17 circuits ne sont mesurés que pour les modèles à 12/12, ou à 11/12 plus rapides qu'E3.

| Config | Fichier (`essais/`) | Graine 7 | Graine 2 | Lecture |
|---|---|---|---|---|
| H1 : affinage d'E3 (`depuis`, learning rate 0,0001) | `driver2-affinage.yaml` | 11/12, **34/46** (38,9 / 55,7 / 52,1) | — | rapide comme F1, faible sous la pluie |
| H2 : `target_kl` 0,02 | `driver2-targetkl.yaml` | 12/12, 26/46 | 12/12, 32/46 | lent, finit peu |
| `penalite_choc` 8 | `driver2-choc8.yaml` | 12/12, 29/46 | 12/12, 36/46 | sous E3 |
| `penalite_choc` 12 | `driver2-choc12.yaml` | 0/12 (immobile) | 8/12 | à écarter |
| `gamma` 0,997 | `driver2-gamma997.yaml` | 11/12 | 6/12 | sous E3 |
| `ent_coef` 0,003 | `driver2-ent003.yaml` | 12/12, 32/46 | 12/12, 39/46 | égal à E3 au mieux, 23 % plus lent |
| `ent_coef` 0,007 | `driver2-ent007.yaml` | 10/12 | 7/12 | à écarter |
| `n_epochs` 5 | `driver2-epochs5.yaml` | 10/12 | 11/12 | moyen |
| **`n_epochs` 20** | `driver2-epochs20.yaml` | 6/12 | **12/12, 45/46** (400k : 45,9 / 65,5 / 59,1) | meilleur résultat, une graine sur deux |
| `gae_lambda` 0,90 | `driver2-gae090.yaml` | 11/12 | 10/12 | rapide, faible sous la pluie |
| `gae_lambda` 0,98 | `driver2-gae098.yaml` | 12/12, 38/46 | 4/12 | fragile |
| `clip_range` 0,1 | `driver2-clip01.yaml` | 12/12, 42/46 | 12/12, 43/46 | le plus régulier entre graines, environ 20 % plus lent |
| `clip_range` 0,3 | `driver2-clip03.yaml` | 8/12 | 12/12, 35/46 | à écarter |

Runs (graine 7, graine 2) : affinage `161952` ; targetkl `162945`, `164048` ; choc8 `165159`, `170128` ; choc12 `171127`, `172046` ; gamma997 `172957`, `173846` ; ent003 `174713`, `175739` ; ent007 `180753`, `181626` ; epochs5 `182522`, `183319` ; epochs20 `184119`, `185118` ; gae090 `190405`, `191223` ; gae098 `192055`, `193051` ; clip01 `193941`, `195132` ; clip03 `200406`, `201300` (préfixe `driver2-20261121-`).

## Vérifications avant livraison

Environ 75 modèles ont été mesurés : le meilleur peut avoir eu de la chance sur ces 46 courses précises. Deux vérifications :

1. **Deuxième graine de course** (30000 au lieu de 20000) :

| Modèle | Total /46, graine 20000 | Total /46, graine 30000 | Course moyenne en validation |
|---|---|---|---|
| E3, graine 7 (livré avant) | 39 | 37 | 175,3 / 177,4 s |
| `n_epochs` 20, graine 2, 400k (série) | 45 | 41 | 174,7 / 177,6 s |
| **`n_epochs` 20, graine 2, final (401 408 pas), réentraîné (livré)** | **43** | **41** | **175,4 / 177,7 s** |
| `clip_range` 0,1, graine 2, final | 43 | 41 | 208,5 / 209,4 s |

2. **Reproductibilité.** La même configuration, réentraînée (graine 2, même commit), redonne exactement les mêmes poids à chaque sauvegarde (vérifié dans la 2e série). Le modèle final du run livré (43/46) diffère de la sauvegarde 400k (45/46) d'une seule mise à jour PPO : l'entraînement s'arrête à 401 408 pas.

## 2e série automatique du 22/11 (15 runs, base : pilote livré)

Même méthode que la première série, autour du pilote livré (`driver2.yaml`, `n_epochs` 20). D'abord la configuration livrée telle quelle avec trois autres graines (13, 21, 42), puis six variantes d'un seul réglage, chacune avec les graines 2 et 13. Meilleur modèle parmi 300k et final (run à 600k : 300k, 400k, 500k et final). Les 17 circuits sont mesurés pour les modèles à 12/12, ou à 11/12 plus rapides que le livré ; tout modèle à 42/46 ou plus repasse les 46 courses avec la graine de course 30000.

**Configuration livrée, selon la graine d'entraînement :**

| Graine | Meilleur modèle | Validation | Total /46 | Tours O / Z / M (s) |
|---|---|---|---|---|
| **2 (livré)** | final | 12/12 | **43** (graine 30000 : 41) | 46,1 / 65,9 / 59,4 |
| 13 | final | 12/12 | 35 (pluie 7/17) | 40,1 / 58,8 / 54,0 |
| 21 | final | 10/12 | — | 57,2 / 84,2 / 79,9 |
| 42 | 300k | 12/12 | 38 | 48,1 / 70,5 / 65,0 |

**Variantes :**

| Config | Fichier (`essais/`) | Graine 2 | Graine 13 | Lecture |
|---|---|---|---|---|
| `n_epochs` 15 | `driver2-s2-epochs15.yaml` | 11/12 (300k) | 0/12 (immobile) | à écarter |
| `n_epochs` 30 | `driver2-s2-epochs30.yaml` | 12/12, 38/46 | 11/12, 37/46 (8 chocs par course) | rapide, faible sous la pluie |
| `clip_range` 0,1 | `driver2-s2-clip01.yaml` | 0/12 (immobile) | 12/12, **44/46**, graine 30000 : **43/46** (50,4 / 73,7 / 66,9) | le plus sûr, 9 à 13 % plus lent, une graine sur deux |
| `batch_size` 128 | `driver2-s2-batch128.yaml` | 11/12, 37/46 (300k ; pluie 9/17) | 0/12 (immobile) | à écarter |
| douceur 0,1 | `driver2-s2-douceur01.yaml` | 10/12 (300k) | 9/12 | à écarter |
| 600k pas | `driver2-s2-600k.yaml` | 400k : 12/12, **45/46**, graine 30000 : 41/46 (45,9 / 65,5 / 59,1) ; final : 9/12 | 500k : 12/12, 39/46 ; final : 32/46 | meilleur à 400k–500k, se dégrade ensuite |

Runs (graine 2, graine 13) : livré graine 13 `091615`, graine 21 `092617`, graine 42 `093447` ; epochs15 `094610`, `095403` ; epochs30 `100209`, `101258` ; clip01 `102618`, `103712` ; batch128 `105205`, `110105` ; douceur01 `110910`, `111804` ; 600k `112732`, `114617` (préfixe `driver2-20261122-`).

**Conclusions :**

- **La configuration livrée est fragile selon la graine.** Graine 2 : 43/46. Les graines 13, 21 et 42 donnent au mieux 35/46, 10/12 et 38/46. Le pilote livré est un bon tirage, pas une configuration sûre.
- **3 runs sur 12 restent immobiles** (`n_epochs` 15 graine 13, `clip_range` 0,1 graine 2, `batch_size` 128 graine 13) : 0/12 à toutes les sauvegardes, malgré `ent_coef` 0,005. Le piège de l'immobilité n'est pas réglé par les réglages de PPO ; une pénalité d'immobilité (code commun) reste à proposer.
- **S'entraîner plus longtemps n'aide pas.** Au-delà de 500k pas, les deux graines vont plus vite mais tapent les murs (8 à 12 chocs par course) et perdent la pluie.
- **`clip_range` 0,1 confirme la première série** : meilleur total avec la graine de course 30000 (43/46), mais 9 à 13 % plus lent, et immobile avec la graine 2.
- **L'entraînement est reproductible au bit près.** Les sauvegardes 100k à 400k du run livré, de l'essai `n_epochs` 20 de la première série et du run à 600k (graine 2) ont exactement les mêmes poids. Le 45/46 de la sauvegarde 400k et le 43/46 du modèle final du run livré ne viennent pas du hasard : avec 2 048 pas par mise à jour, l'entraînement s'arrête à 401 408 pas, et le modèle final a une mise à jour PPO de plus que la sauvegarde 400k.
- **Pilote livré conservé.** Aucune variante ne le bat avec les deux graines de course à la même vitesse : le 45/46 ne fait que 41/46 avec la graine 30000, comme le livré, et le 44/46 de `clip_range` 0,1 est 13 % plus lent.

## Lectures

- **`fin_sur_choc: false` règle la pluie.** Avec un arrêt au premier choc, le pilote n'apprend jamais à se dégager d'un mur : 4 courses sur 17 finies sous la pluie, 11 sans arrêt.
- **La pénalité de choc est le levier de récompense qui compte.** 10 est le bon réglage : 5 tape les murs, 7 et 8 n'apportent rien, 12 fige le pilote.
- **Gamma 0,995 rend la conduite propre** : il freine avant le virage, 0,2 choc par course.
- **`ent_coef` 0,005 réduit le piège de l'immobilité sans le supprimer.** Sans lui, une graine sur trois apprend à rester sur place (immobile, il perd environ 12 ; un choc coûte 10). Avec lui, 3 runs sur 15 de la 2e série restent immobiles. Il stabilise aussi les entraînements longs.
- **`n_epochs` 20 est le meilleur levier trouvé** (45/46), mais avec une graine sur deux.
- **`clip_range` 0,1 est le plus régulier entre graines** (42 et 43/46), mais environ 20 % plus lent.
- **N'apportent rien** : abandon à 30 (pilote craintif), coût du temps 0,015 et 0,02 (perd la pluie), learning rate 0,0002 (immobilité), lots 512/128, `pas_max` 4500, douceur 0,1, `ent_coef` 0,003 et 0,007 (0,01 : 40/46 à 300k mais 10 % plus lent), `target_kl`, gamma 0,997, `gae_lambda` 0,90 et 0,98, `clip_range` 0,3, réseau 128 × 128.
- **Vitesse et pluie s'opposent.** Les versions rapides (1M pas, coût du temps, affinage, `gae_lambda` 0,90) perdent toutes des courses sous la pluie. Le réseau 128 × 128 ne résout pas ce dilemme : la limite vient plutôt de ce que perçoit le pilote (LiDAR à l'avant seulement, pas de mémoire) et de la récompense.
- **Le hasard pèse lourd**, entre graines d'entraînement (45/46 contre 6/12) comme entre graines de course (45 contre 41). Peu de conclusions fermes sans deux graines de chaque.
- **Les 3 circuits de validation sont trop flatteurs** : 11/12 en validation, mais 17/34 sur les 17 autres circuits pour le pilote du 20/11.
- **Point faible commun à tous les modèles : Shanghai**, jamais fini : la plus longue ligne droite du jeu (110 m) débouche sur un virage de rayon compris entre 0,7 et 1,1 m selon le lissage, le plus serré du jeu dans tous les cas (rayon de courbure mesuré sur la ligne centrale `simulation/maps/<circuit>/<circuit>_centerline.csv` ; méthode dans la section 7 de `submission/driver2/DRIVER2.md`).

## Pilote livré

- **Run :** `driver2-20261121-214154-ppo`, exporté dans `submission/driver2` (commit `a9ac8af`).
- **Configuration :** `training/configs/driver2.yaml`, soit E3 + `n_epochs` 20 : graine 2, 400 000 pas, `ent_coef` 0,005, gamma 0,995, `penalite_choc` 10, `fin_sur_choc: false`. Le fichier est identique à la section `config` du `meta.json` du run.
- **Résultats :** validation 12/12 (0,2 choc par course), tours 46,1 / 65,9 / 59,4 s. Sur 46 courses : 43/46 (graine de course 20000) et 41/46 (graine 30000), contre 39 et 37 pour E3, à la même vitesse.
- **Export :** `make verify DRIVER=driver2` répond VALID ; `model.onnx.data` fait 27 144 octets.
