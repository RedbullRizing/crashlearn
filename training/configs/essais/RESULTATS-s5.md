# Série 5 de driver2 : vitesse sans perdre d'arrivées (CRA-107)

**Question.** Le pilote livré pendant la série, B (`n_steps` 512 graine 2, modèle final, `driver2-20261123-194118-ppo`), finit beaucoup de courses (44,75/46 en moyenne sous 0,7 sur 4 graines de course), mais il est lent : 211,3 s en temps moyen sur les 17 circuits. Peut-on gagner en vitesse sans perdre d'arrivées, sous l'adhérence de 0,7 à 1,0 annoncée pour le tournoi ?

Les configurations sont à côté de ce fichier. Les 24 runs entraînés pendant la série sont dans `archives/driver2-20261124-*` et `archives/driver2-20261125-*` : courbes, `meta.json`, CSV des courses du modèle final et une note qui donne les chiffres de chaque modèle mesuré. La série a tourné du 24/11/2026 à 20:07 au 25/11 à 06:17 (10 h 10), au commit `a0c6541`.

## Méthode

- **Quatre configurations**, chacune égale à celle de B (`driver2-s4-nsteps512.yaml`) à une différence près :
  - **nsteps512** : `driver2-s4-nsteps512.yaml` tel quel, sur 8 nouvelles graines, pour savoir si B est un bon tirage ;
  - **temps015** : `driver2-s5-temps015.yaml`, avec `cout_temps: 0.015` au lieu de 0,01 ;
  - **temps02** : `driver2-s5-temps02.yaml`, avec `cout_temps: 0.02` ;
  - **nsteps1024** : `driver2-s5-nsteps1024.yaml`, avec `n_steps: 1024` et `pas: 800000`. Chaque mise à jour PPO porte sur 8 192 pas au lieu de 4 096 ; le run s'arrête à 802 816 pas, soit 98 mises à jour.
- **Graines d'entraînement** :
  - nsteps512 : 3, 4, 6, 7, 8, 9, 10 et 11 (les graines 2, 13, 21, 42, 1 et 5 ont été mesurées dans la série 4) ;
  - temps015 et nsteps1024 : 2, 13, 21, 42, 1 et 5 ;
  - temps02 : 2, 13, 1 et 5.

  Les 24 runs ont été lancés à tour de rôle (une graine de chaque configuration, puis la suivante), tous au commit `a0c6541`, dépôt non modifié.
- **Modèles mesurés** : les sauvegardes 400k et 500k et le modèle final ; pour nsteps1024, les sauvegardes 600k et 700k et le modèle final.
- **Double évaluation**, comme dans la série 4 : `runs/courses_detail.py`, sur les mêmes courses, sous l'adhérence minimale 0,7 (la **condition de décision**) et sous 0,5. Total sur 46 = 12 courses de validation + 34 sur les 17 circuits d'entraînement, avec la graine de course 20000.
  - La validation est mesurée dans les deux conditions pour tous les modèles.
  - Les 17 circuits sont mesurés, dans les deux conditions, pour tout modèle à 11/12 ou plus dans au moins une condition.
  - Un modèle à 42/46 ou plus repasse les 46 courses avec la graine de course 30000, dans cette condition.
  - **Confirmation** : sous 0,7, un modèle qui fait au moins 44/46 avec les graines 20000 et 30000, et au plus 205,0 s en temps moyen sur les 17 circuits (courses finies, deux graines réunies), rejoue les 46 courses avec les graines 40000 et 50000.
- **Règle de CRA-107, fixée avant la série** : sur les 4 graines de course, sous 0,7, une moyenne d'au moins 44,25/46, un minimum d'au moins 44 et un temps moyen d'au plus 205,0 s sur les 17 circuits (courses finies, 4 graines réunies).
- **B n'a pas été rejoué** : ses chiffres sont relus dans ses CSV de la série 4 (graines de course 20000 à 50000 sous 0,7, 20000 et 30000 sous 0,5).
- **Médianes par configuration**, sous 0,7, avec les règles de la série 4 :
  - une graine compte son total /46 dès que ses 46 courses sont mesurées ;
  - elle compte 0 seulement si ses 17 circuits n'ont pas été mesurés, c'est-à-dire à moins de 11/12 dans les deux conditions ;
  - « meilleur modèle » prend le meilleur des 3 modèles de chaque graine ; « final seul » prend le modèle final ;
  - le nombre de graines à moins de 11/12 en validation sous 0,7 est un indicateur séparé, hors médianes.

## Résultats par graine

Meilleur modèle de chaque graine et de chaque configuration sous 0,7. Le total sous 0,5 est celui du même modèle. Entre parenthèses, le total avec la graine de course 30000. Tours : meilleurs tours à Oschersleben / Zandvoort / MexicoCity sous 0,7, en secondes. Temps moyen : courses finies sur les 17 circuits, graine de course 20000, sous 0,7.

| Graine | Config | Meilleur modèle | Validation 0,7 | **Total 0,7** | Total 0,5 | Tours O / Z / M (s) | Temps moyen 17c (s) |
|---|---|---|---|---|---|---|---|
| 2 | temps015 | final | 12/12 | **30** | 28 | 60,9 / 87,8 / 78,5 | 245,1 |
| 2 | temps02 | final | 9/12 | — | 7/12 | 52,1 / 73,4 / 69,2 | — |
| 2 | nsteps1024 | final | 12/12 | **31** | 29 | 60,6 / 86,7 / 79,8 | 245,7 |
| 13 | temps015 | final | 11/12 | **39** | 36 | 46,6 / 68,5 / 62,1 | 208,3 |
| 13 | temps02 | 500k | 11/12 | **42** (43) | 42 (42) | 44,5 / 63,6 / 58,0 | 198,1 |
| 13 | nsteps1024 | 600k | 12/12 | **43** (43) | 41 | 54,2 / 78,6 / 70,0 | 244,2 |
| 21 | temps015 | 400k | 12/12 | **42** (40) | 43 (43) | 51,8 / 74,8 / 67,7 | 229,0 |
| 21 | nsteps1024 | final, **pilote livré** | 12/12 | **44** (45) | 45 (43) | 42,5 / 61,1 / 55,6 | 190,4 |
| 42 | temps015 | 400k | 12/12 | **42** (41) | 37 | 43,6 / 64,6 / 62,0 | 204,9 |
| 42 | nsteps1024 | 600k | 12/12 | **44** (44) | 43 (44) | 56,2 / 80,5 / 71,7 | 244,7 |
| 1 | temps015 | 500k | 10/12 | **37** | 39 | 46,9 / 67,6 / 61,2 | 211,5 |
| 1 | temps02 | 500k | 12/12 | **46** (45) | 46 (46) | 50,0 / 74,0 / 67,2 | 236,0 |
| 1 | nsteps1024 | final | 0/12, roule au pas | — | 0/12 | 135,1 / 198,8 / — | — |
| 5 | temps015 | 400k | 12/12 | **43** (46) | 45 (45) | 47,4 / 67,8 / 61,5 | 211,6 |
| 5 | temps02 | 500k | 11/12 | **29** | 28 | 60,0 / 88,5 / 79,9 | 249,7 |
| 5 | nsteps1024 | 700k | 12/12 | **42** (43) | 42 (43) | 53,2 / 76,9 / 69,2 | 234,7 |
| 3 | nsteps512 | 400k | 12/12 | **43** (44) | 43 (44) | 55,4 / 79,8 / 72,5 | 246,6 |
| 4 | nsteps512 | 400k | 11/12 | **39** | 41 | 42,6 / 60,8 / 55,6 | 186,3 |
| 6 | nsteps512 | final | 11/12 | **35** | 33 | 48,8 / 70,9 / 63,0 | 217,4 |
| 7 | nsteps512 | 400k | 12/12 | **44** (42) | 43 (40) | 47,6 / 69,0 / 64,2 | 214,6 |
| 8 | nsteps512 | 500k | 11/12 | **41** | 43 (38) | 37,4 / 54,5 / 49,8 | 172,2 |
| 9 | nsteps512 | 400k | 12/12 | **45** (44) | 45 (45) | 54,5 / 79,5 / 70,4 | 245,2 |
| 10 | nsteps512 | final | 10/12 | — | 9/12 | 68,0 / 99,0 / 89,0 | — |
| 11 | nsteps512 | 500k | 12/12 | **40** | 39 | 51,4 / 74,2 / 68,2 | 226,5 |

**Par configuration**, sous 0,7. Temps moyen et tours : moyenne des graines dont les 46 courses sont mesurées, meilleur modèle, graine de course 20000. Pour comparer, la config de B dans la série 4 (graines 2, 13, 21, 42, 1 et 5) et sur les 14 graines des deux séries.

| Config | Graines | Graines à moins de 11/12 (meilleur modèle) | Dont immobiles | **Médiane, meilleur modèle** | Min – max | **Médiane, final seul** | Finals à moins de 11/12 | Temps moyen 17c (s) | Tours moyens O / Z / M (s) |
|---|---|---|---|---|---|---|---|---|---|
| nsteps512, nouvelles graines | 8 | 1 (10) | 0 | 40,5 | 0 – 45 | 34,5 | 5 | 215,6 | 48,2 / 69,8 / 63,4 |
| temps015 | 6 | 1 (1) | 0 | 40,5 | 30 – 43 | 34,5 | 2 | 218,4 | 49,5 / 71,8 / 65,5 |
| temps02 | 4 | 1 (2) | 0 | 35,5 | 0 – 46 | 18,5 | 2 | 227,9 | 51,5 / 75,4 / 68,4 |
| **nsteps1024** | 6 | 1 (1) | 0 | **42,5** | 0 – 44 | **41,5** | 1 | 231,9 | 53,3 / 76,8 / 69,3 |
| nsteps512, série 4 | 6 | 0 | 0 | 40,0 | 36 – 46 | 40,0 | 2 | 220,9 | 49,7 / 71,7 / 65,8 |
| nsteps512, séries 4 et 5 | 14 | 1 | 0 | 40,0 | 0 – 46 | 36,0 | 7 | 218,0 | 48,9 / 70,7 / 64,5 |

« Dont immobiles » compte le meilleur modèle de chaque graine. nsteps1024 graine 1 n'y figure pas, car son modèle final roule, mais au pas : ses sauvegardes 600k et 700k sont immobiles (0/12, aucun tour), et son modèle final fait des tours de 135 s sans finir une course.

Runs (préfixe `driver2-`) :

| Config | Graine 2 | Graine 13 | Graine 21 | Graine 42 | Graine 1 | Graine 5 |
|---|---|---|---|---|---|---|
| temps015 | `20261124-194535` | `20261124-205856` | `20261124-224741` | `20261125-004626` | `20261125-023055` | `20261125-033929` |
| temps02 | `20261124-200402` | `20261124-212116` | — | — | `20261124-231110` | `20261125-011225` |
| nsteps1024 | `20261124-201829` | `20261124-214658` | `20261124-233935` | `20261125-012948` | `20261125-024950` | `20261125-041116` |

| Config | Graine 3 | Graine 4 | Graine 6 | Graine 7 | Graine 8 | Graine 9 | Graine 10 | Graine 11 |
|---|---|---|---|---|---|---|---|---|
| nsteps512 | `20261124-190742` | `20261124-204245` | `20261124-222420` | `20261125-001900` | `20261125-020610` | `20261125-030813` | `20261125-044228` | `20261125-045812` |

## Confirmation sur quatre graines de course

Un seul modèle a passé le seuil de confirmation : nsteps1024 graine 21, modèle final (`233935`). Il a rejoué les 46 courses sous 0,7 avec les graines de course 40000 et 50000. B est relu dans ses CSV.
- Tours : meilleur tour sur les validations des 4 graines.
- Temps moyen : courses finies sur les 17 circuits, 4 graines réunies.
- Chocs : moyenne par course, toutes courses comprises (184 courses).

| Modèle | 20000 | 30000 | 40000 | 50000 | **Moyenne /46** | **Min** | Tours O / Z / M (s) | **Temps moyen 17c (s)** | Chocs/course | Abandons | Règle de CRA-107 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B : nsteps512 graine 2, final (`194118`) | 44 | 44 | 45 | 46 | **44,75** | **44** | 47,0 / 67,8 / 62,4 | **211,3** | 0,33 | 5 stagnations | non : temps 211,3 s > 205,0 s |
| **nsteps1024 graine 21, final (`233935`)** | 44 | 45 | 45 | 44 | **44,50** | **44** | 42,2 / 61,0 / 55,6 | **190,1** | 2,94 | 6 stagnations | **oui** |

Abandons, tous sous la pluie et tous par stagnation :

| Graine de course | B (`194118`) | nsteps1024 graine 21 (`233935`) |
|---|---|---|
| 20000 | BrandsHatch (1 choc), Shanghai (0) | MoscowRaceway (2 chocs), Shanghai (0) |
| 30000 | MexicoCity, validation (0), Austin (0) | Monza (39) |
| 40000 | MexicoCity, validation (1) | Montréal (137) |
| 50000 | aucun | Montréal (156), Monza (116) |

- **Les deux modèles n'abandonnent pas sur les mêmes courses** : une seule en commun, Shanghai avec la graine 20000. `233935` finit les 4 autres courses que B abandonne, et B finit les 5 autres courses que `233935` abandonne.
- **Les chocs de `233935` viennent de ses abandons** : il reste plaqué contre un mur jusqu'à l'élimination. Sur ses courses finies, il fait 0,51 choc par course, contre 0,32 pour B. Un choc est un pas de 50 ms passé au contact d'un mur, pas un impact distinct.
- **Aucune de ces courses n'a été coupée par la limite de 300 s.**

Les modèles qui faisaient au moins 44/46 avec les graines 20000 et 30000, mais trop lents pour être confirmés (temps moyen sur les 17 circuits, deux graines réunies) :

- temps02 graine 1, 500k : 46 et 45/46, 235,4 s ;
- nsteps1024 graine 42, 600k : 44 et 44/46, 244,4 s ;
- nsteps512 graine 9, 400k : 45 et 44/46, 244,6 s ;
- nsteps512 graine 9, 500k : 44 et 44/46, 211,0 s.

## Conclusions

- **Un seul modèle remplit la règle : nsteps1024 graine 21, modèle final (`driver2-20261124-233935-ppo`), devenu le pilote driver2 le 25/11.**
  - **Il finit presque autant de courses que B** : 44,50 de moyenne contre 44,75, une arrivée de moins sur 184 courses, avec le même minimum (44).
  - **Il est 10 % plus rapide** : 190,1 s contre 211,3 s en temps moyen sur les 17 circuits, et des tours de 42,2 / 61,0 / 55,6 s contre 47,0 / 67,8 / 62,4 s.
  - **Sous 0,5**, il fait 45/46 (graine de course 30000 : 43/46), contre 43 et 44/46 pour B.
  - **Il est reproductible avec `make train`** : c'est le modèle final d'un run complet. Réentraîné sur la branche de CRA-100 (`driver2-20261125-193741-ppo`), il redonne les mêmes poids, pour le modèle final comme pour les sauvegardes 600k et 700k (commits `2f77ee6`, `05ea44a` et `89eb436`).
- **Son point faible : Montréal et Monza sous la pluie.** Il y abandonne 2 fois sur 4 chacun, collé au mur (39 à 156 chocs). Ce n'est pas le hasard d'une graine de course : il sort aussi de la piste à Montréal sous la pluie sous 0,5 (graine 30000, 104 chocs), et ses sauvegardes 600k et 700k abandonnent déjà à Montréal sous la pluie (94 à 142 chocs). B finit ces deux courses avec les 4 graines de course. B reste la solution de repli.
- **nsteps1024 a la meilleure médiane de la série** : 42,5 sous 0,7, et 41,5 sur le modèle final seul. Son modèle final est presque aussi bon que son meilleur modèle (41,5 contre 42,5), alors que l'écart est de 6 à 17 points pour les trois autres configurations. Graine 21 : 41 à 600k, 43 à 700k, 44 au final. Elle reste lente en moyenne (231,9 s) : la graine 21 est une exception rapide.
- **Augmenter le coût du temps ne rend pas plus rapide.** temps015 et temps02 font 218,4 et 227,9 s en temps moyen sur les 17 circuits, contre 215,6 s pour nsteps512 sur ses nouvelles graines. Ils sont aussi moins réguliers : médianes de 40,5 et 35,5, et 34,5 et 18,5 sur le modèle final seul.
- **B est un bon tirage.** Sur 8 nouvelles graines, la configuration de B garde une médiane de 40,5, comme dans la série 4 (40), mais 5 modèles finaux sur 8 sont à moins de 11/12 sous 0,7, et sa médiane sur le modèle final seul tombe à 34,5. La régularité du modèle final vue dans la série 4 ne se confirme pas.
- **Graines ratées.** Une graine par configuration a son meilleur modèle à moins de 11/12 sous 0,7 :
  - nsteps1024 graine 1 : le piège de l'immobilité, malgré `ent_coef` 0,005 (voir plus haut) ;
  - nsteps512 graine 10 : la sauvegarde 400k roule au pas (0/12, tours de 118 s) ; le modèle final plafonne à 10/12 ;
  - temps02 graine 2 : 9/12 au mieux, avec 11,8 chocs par course pour le modèle final ;
  - temps015 graine 1 : 10/12 sous 0,7 (37/46), 12/12 sous 0,5.
- **Le meilleur modèle n'est souvent pas le dernier.** Sous 0,7, avec la graine de course 20000 :
  - nsteps512 graine 7 : 44 à 400k, 42 à 500k, 37 au final ;
  - nsteps512 graine 9 : 45, 44, puis 41 ;
  - nsteps512 graine 11 : 10/12 à 400k, 40 à 500k, 30 au final ;
  - nsteps512 graine 4 : 39 à 400k, puis 8/12 à 500k (20,2 chocs par course en validation) et 9/12 au final ;
  - temps015 graine 21 : 42 à 400k, 10/12 à 500k, 30 au final (12,5 chocs par course en validation).

  Il faut continuer de mesurer toutes les sauvegardes.
- **Un modèle peut chuter avec une autre graine de course** : temps02 graine 1, modèle final, fait 45/46 avec la graine 20000 et 37/46 avec la graine 30000.
- **Une partie des abandons vient de notre limite de 300 s.** Sur les 3 644 courses jouées sous 0,7 pendant la série avec les graines de course 20000 et 30000, il y a 564 abandons : 436 stagnations, 127 « temps écoulé » et 1 sortie de piste. Les 92 courses de la confirmation (graines 40000 et 50000) ajoutent 3 stagnations, celles de `233935` à Montréal et Monza. Les « temps écoulé » touchent les modèles lents, dont les tours font environ 100 s ou plus sur les longs circuits : 3 tours n'y tiennent pas en 300 s.
  - Sur les 17 circuits : temps015 graine 2, final (14) ; nsteps1024 graine 2, final (11) et 700k (12) ; nsteps512 graine 6, 400k et 500k (10 chacun) ; temps02 graine 5, 500k (10) ; nsteps1024 graine 5, 600k (14).
  - En validation : surtout nsteps512 graine 10, 400k (12) et temps015 graine 2, 400k (8).

  Leurs totaux bas (24 à 31/46 pour la graine 2) mesurent donc surtout leur lenteur. Ni `233935` ni les modèles proches de la règle n'ont d'abandon pour temps écoulé.

Règles de course du simulateur (3 tours, stagnation, sortie de piste, absence de limite de temps) : voir `RESULTATS-s4.md`.
