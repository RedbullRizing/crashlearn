# Série 4 de driver2 : robustesse aux graines d'entraînement (CRA-106)

**Question.** La configuration livrée réussit avec la graine 2, mais beaucoup moins avec d'autres graines : le pilote livré est un bon tirage, pas une configuration sûre. Existe-t-il une configuration qui donne un bon pilote avec la plupart des graines, sous l'adhérence de 0,7 à 1,0 annoncée pour le tournoi ?

Les configurations sont à côté de ce fichier. Les 12 runs entraînés pendant la série sont dans `archives/driver2-20261123-*` : courbes, `meta.json` et une note qui donne les chiffres de chaque modèle mesuré. La série a tourné du 23/11/2026 à 20:19 au 24/11 à 00:22, au commit `f036318`.

## Méthode

- **Trois configurations**, chacune égale au pilote livré à une ligne près :
  - **livrée** : `training/configs/driver2.yaml` tel quel ;
  - **clip01** : `driver2-s2-clip01.yaml`, avec `clip_range: 0.1`, le plus sûr de la série 2 avec la graine 13 (44/46), mais immobile avec la graine 2 ;
  - **nsteps512** : `driver2-s4-nsteps512.yaml`, avec `n_steps: 512` et `pas: 600000`. Chaque mise à jour PPO porte sur 4 096 pas au lieu de 2 048, soit environ 147 mises à jour au lieu de 196.

  Les options de CRA-105 (`friction_min`, `penalite_immobilite`) restent à leurs valeurs par défaut à l'entraînement. Elles ne servent qu'à évaluer sous 0,7.
- **Six graines d'entraînement** : 2, 13, 21, 42, 1 et 5. Modèles mesurés :
  - livrée et clip01 : la sauvegarde 300k et le modèle final ;
  - nsteps512 : les sauvegardes 400k et 500k, et le modèle final.
- **Runs réutilisés.** L'entraînement est reproductible au bit près, donc les 6 runs qui existaient déjà n'ont pas été relancés, seulement mesurés :
  - livrée graines 2, 13, 21 et 42 ;
  - clip01 graines 2 et 13.

  Le script a vérifié que leur `meta.json` correspond à la config (graine, `pas`, `ppo`, `env`), et que les copies 300k de la série 2 sont identiques octet pour octet aux sauvegardes. Il restait 12 runs à entraîner.
- **Double évaluation**, comme l'essai v3 : `runs/courses_detail.py`, sur les mêmes courses, sous l'adhérence minimale 0,7 (la **condition de décision**) et sous 0,5 (celle de la v2). Total sur 46 = 12 courses de validation + 34 sur les 17 circuits d'entraînement, avec la graine de course 20000.
  - La validation est mesurée dans les deux conditions pour tous les modèles.
  - Les 17 circuits sont mesurés, dans les deux conditions, pour tout modèle à 11/12 ou plus dans au moins une condition.
  - Un modèle à 42/46 ou plus repasse les 46 courses avec la graine de course 30000, dans cette condition.
- **Médianes par configuration**, sous 0,7 :
  - une graine compte son total /46 dès que ses 46 courses sont mesurées ;
  - elle compte 0 seulement si ses 17 circuits n'ont pas été mesurés, c'est-à-dire à moins de 11/12 dans les deux conditions ;
  - « meilleur modèle » prend le meilleur modèle de chaque graine ; « final seul » prend le modèle final, pour comparer à nombre de candidats égal (nsteps512 en a 3, les autres 2) ;
  - le nombre de graines à moins de 11/12 en validation sous 0,7 est un indicateur séparé, hors médianes.

## Résultats par graine

Meilleur modèle de chaque graine et de chaque configuration sous 0,7. Le total sous 0,5 est celui du même modèle. Entre parenthèses, le total avec la graine de course 30000. Tours : meilleurs tours à Oschersleben / Zandvoort / MexicoCity sous 0,7, en secondes.

| Graine | Config | Meilleur modèle | Validation 0,7 | **Total 0,7** | Total 0,5 | Tours O / Z / M (s) | Temps moyen 17c (s) |
|---|---|---|---|---|---|---|---|
| 2 | livrée | final, **pilote livré** | 12/12 | **42** (43) | 43 (41) | 46,1 / 65,9 / 59,4 | 202,8 |
| 2 | clip01 | final | 0/12, immobile | — | — | — | — |
| 2 | nsteps512 | final | 12/12 | **44** (44) | 43 (44) | 47,1 / 67,9 / 62,6 | 211,5 |
| 13 | livrée | final | 10/12 | **38** | 35 | 40,1 / 58,8 / 53,9 | 182,1 |
| 13 | clip01 | final | 12/12 | **44** (42) | 44 (43) | 50,4 / 72,7 / 67,2 | 229,0 |
| 13 | nsteps512 | 400k | 12/12 | **46** (46) | 45 (43) | 49,6 / 71,0 / 65,2 | 218,6 |
| 21 | livrée | final | 9/12 | — | 10/12 | 57,5 / 84,2 / 79,9 | — |
| 21 | clip01 | 300k | 12/12 | **37** | 36 | 56,6 / 82,4 / 75,5 | 246,0 |
| 21 | nsteps512 | 500k | 11/12 | **36** | 28 | 53,5 / 77,9 / 71,2 | 239,5 |
| 42 | livrée | 300k | 12/12 | **40** | 38 | 48,1 / 70,5 / 65,2 | 224,4 |
| 42 | clip01 | final | 12/12 | **39** | 39 | 57,8 / 84,8 / 77,0 | 249,5 |
| 42 | nsteps512 | final | 11/12 | **40** | 35 | 47,0 / 68,5 / 63,2 | 215,9 |
| 1 | livrée | 300k | 12/12 | **39** | 37 | 48,5 / 69,2 / 64,9 | 218,0 |
| 1 | clip01 | final | 10/12 | **24** | 25 | 64,5 / 94,7 / 85,5 | 250,6 |
| 1 | nsteps512 | 400k | 12/12 | **40** | 36 | 48,2 / 69,0 / 63,1 | 208,0 |
| 5 | livrée | 300k | 12/12 | **41** | 40 | 51,2 / 74,5 / 68,0 | 238,4 |
| 5 | clip01 | final | 11/12 | **29** | 30 | 59,4 / 86,5 / 78,9 | 246,9 |
| 5 | nsteps512 | 400k | 11/12 | **37** | 34 | 52,9 / 75,8 / 69,3 | 231,7 |

**Par configuration**, sous 0,7 :

| Config | Graines à moins de 11/12 (meilleur modèle) | Dont immobiles | **Médiane, meilleur modèle** | Min – max | **Médiane, final seul** | Finals à moins de 11/12 | Temps moyen 17c (s) | Tours moyens O / Z / M (s) |
|---|---|---|---|---|---|---|---|---|
| livrée | 2 (13, 21) | 0 | 39,5 | 0 – 42 | 35,0 | 4 | 213,1 | 46,8 / 67,8 / 62,3 |
| clip01 | 2 (2, 1) | 1 (2) | 33,0 | 0 – 44 | 30,5 | 2 | 244,4 | 57,7 / 84,2 / 76,8 |
| **nsteps512** | **0** | 0 | **40,0** | **36 – 46** | **40,0** | 2 | 220,9 | 49,7 / 71,7 / 65,8 |

Runs (préfixe `driver2-`) :

| Config | Graine 2 | Graine 13 | Graine 21 | Graine 42 | Graine 1 | Graine 5 |
|---|---|---|---|---|---|---|
| livrée | `20261121-214154` | `20261122-091615` | `20261122-092617` | `20261122-093447` | `20261123-214319` | `20261123-223251` |
| clip01 | `20261122-102618` | `20261122-103712` | `20261123-203402` | `20261123-211012` | `20261123-215538` | `20261123-224749` |
| nsteps512 | `20261123-194118` | `20261123-200448` | `20261123-205017` | `20261123-212646` | `20261123-220912` | `20261123-230119` |

## Confirmation sur quatre graines de course

Les deux meilleurs modèles de la série (A et B), le modèle final de nsteps512 graine 13 et le pilote livré ont rejoué les 46 courses sous 0,7, avec les graines de course 40000 et 50000 en plus de 20000 et 30000.
- Tours : meilleur tour sur les validations des 4 graines.
- Temps moyen : courses finies sur les 17 circuits, 4 graines.
- Chocs : moyenne par course, toutes courses comprises.

| Modèle | 20000 | 30000 | 40000 | 50000 | **Moyenne /46** | **Min** | Tours O / Z / M (s) | Temps moyen 17c (s) | Chocs/course | Abandons |
|---|---|---|---|---|---|---|---|---|---|---|
| Pilote livré (livrée graine 2, final, `214154`) | 42 | 43 | 44 | 44 | **43,25** | **42** | 46,1 / 65,9 / 59,4 | 202,4 | 0,99 | 11 stagnations |
| **A** : nsteps512 graine 13, 400k (de `200448`) | 46 | 46 | 44 | 45 | **45,25** | **44** | 49,6 / 70,8 / 65,2 | 217,5 | 1,35 | 3 stagnations |
| nsteps512 graine 13, final (`200448`) | 43 | 43 | 40 | 37 | **40,75** | **37** | 39,5 / 56,6 / 51,1 | 177,9 | 4,44 | 21 stagnations |
| **B** : nsteps512 graine 2, final (`194118`) | 44 | 44 | 45 | 46 | **44,75** | **44** | 47,0 / 67,8 / 62,4 | 211,3 | 0,33 | 5 stagnations |

Aucune de ces courses n'a été coupée par la limite de 300 s : tous les abandons sont des stagnations.

## Conclusions

- **nsteps512 est la configuration la plus régulière entre graines.**
  - Aucune graine n'est à moins de 11/12 pour son meilleur modèle, contre 2 sur 6 pour la livrée et pour clip01.
  - Sa médiane est de 40 sous 0,7, et reste à 40 sur le modèle final seul : l'avantage ne vient pas de son troisième modèle candidat.
  - Son minimum est le plus haut (36). Les deux autres configurations ont chacune une graine à 0.
- **La configuration livrée reste fragile** : 4 modèles finaux sur 6 sont à moins de 11/12 sous 0,7, et sa médiane tombe de 39,5 à 35 sur le modèle final seul.
- **Choix : B, nsteps512 graine 2, modèle final (`driver2-20261123-194118-ppo`), nouveau pilote driver2.**
  - **Ses arrivées sont dans le bruit face à A :** 44,75 de moyenne contre 45,25, avec le même minimum (44). Les deux varient de 44 à 46 selon la graine de course.
  - **Il est plus rapide que A :** 211,3 s de moyenne sur les 17 circuits contre 217,5 s, et des tours de 47,0 / 67,8 / 62,4 s contre 49,6 / 70,8 / 65,2 s.
  - **Il touche le moins les murs :** 0,33 choc par course, contre 1,35 pour A et 0,99 pour le pilote livré.
  - **Il est reproductible avec `make train` :** c'est le modèle final d'un run complet, avec la graine 2. L'entraînement étant reproductible au bit près, la config suffit à le refaire, sans choisir de sauvegarde. A est la sauvegarde 400k d'un run de graine 13.
  - **Face au pilote livré :** sous 0,7, il fait 44,75 de moyenne et 44 au minimum, contre 43,25 et 42. Sous 0,5, il fait 43 (graine de course 30000 : 44), contre 43 (41). Il est un peu plus lent : 211,3 s contre 202,4 s, et des tours de 47,0 / 67,8 / 62,4 s contre 46,1 / 65,9 / 59,4 s.
- **A reste l'alternative** : le meilleur total moyen de la série (45,25), mais plus lent et avec plus de chocs.
- **Ce qui reste fragile :**
  - **La sauvegarde 500k est souvent en creux.** Graine 2 : 40 à 400k, 8/12 à 500k, 44 au final. Graine 13 : 46, 39, puis 43. Il faut continuer de mesurer toutes les sauvegardes.
  - **Un modèle peut chuter avec une autre graine de course.** nsteps512 graine 13 final passe de 43 à 37 avec la graine de course 50000, avec 4,44 chocs par course. Il faut plusieurs graines de course pour confirmer un candidat ; ici, quatre.
  - **clip01 est en partie coupé par notre limite de 300 s.** C'est la configuration la plus lente (temps moyen 244,4 s, tours moyens 57,7 / 84,2 / 76,8 s). Une partie de ses abandons sont des « temps écoulé » : 3 tours n'y tiennent pas en 300 s sur les longs circuits. Si le tournoi laisse plus de temps, clip01 est sous-estimé.

## Règles de course du simulateur

Lues dans `simulation/env_simulation.py` :

- **3 tours** bouclés pour être classé à l'arrivée (`_REQUIRED_LAPS`).
- **20 décisions par seconde** : un pas dure 50 ms (5 sous-pas physiques à 100 Hz).
- **Stagnation** : abandon si la voiture gagne moins de 1 m de progression en 10 s (200 pas).
- **Sortie de piste** : abandon immédiat si le centre de la voiture dépasse la demi-largeur locale de la piste + 1,00 m (`_OFFTRACK_MARGIN_M`). `simulation/INSTRUCTIONS.md` annonce 0,50 m, mais le code applique 1,00 m.
- **Chocs** : jamais pénalisés, jamais éliminatoires.
- **Aucune limite de temps** dans le simulateur : la fin de course est laissée au programme qui le fait tourner. La limite de 6 000 pas (300 s) est la nôtre : `training.train.evaluer`, `runs/courses_detail.py` et `training/grand_prix.py`. La limite du tournoi n'est pas écrite dans le dépôt.
