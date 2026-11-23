# Essai v3 de driver2 : adhérence 0,7 à 1,0 et pénalité d'immobilité (CRA-105)

L'essai v3 répond à deux questions :

- **Faut-il entraîner sous l'adhérence annoncée par la pédagogie pour le tournoi ?** La pédagogie (FU2) annonce une adhérence de 0,7 à 1,0 sous la pluie. La v2 s'entraîne de 0,5 à 1,0 (`FRICTION_PLUIE` dans `features.py`).
- **Une pénalité d'immobilité règle-t-elle le piège de l'immobilité ?** Malgré `ent_coef` 0,005, 4 runs sur 43 des séries 1 et 2 sont restés immobiles du début à la fin.

Les configurations sont à côté de ce fichier (`driver2-v3-*.yaml`). Les runs sont dans `archives/driver2-20261122-2*` : courbes, `meta.json` et une note avec les totaux dans les deux conditions. La série a tourné le 22/11/2026, au commit `e1f5c21`.

## Méthode

- **Deux options du code commun, désactivées par défaut**, sur la branche CRA-105. Avec les valeurs par défaut, le MDP v2 est identique : même empreinte de 8 épisodes, avant et après le changement.
  - `friction_min` (env) : l'adhérence la plus basse sous la pluie, de 0,5 (v2) à 1,0.
  - `penalite_immobilite` (récompense) : une pénalité retirée à chaque pas où la voiture roule à moins de 0,3 m/s. Elle vaut 0 par défaut.
- **Trois configurations**, chacune égale au pilote livré (`driver2.yaml`) plus une ou deux lignes :
  - friction 0,7 : `friction_min: 0.7` ;
  - immobilité 0,03 : `penalite_immobilite: 0.03`, soit 6 points perdus pour 10 s à l'arrêt ;
  - les deux.
- **Quatre graines d'entraînement** (2, 13, 21, 42), 400k pas par run, soit 12 runs. Le modèle final et la sauvegarde 300k sont mesurés tous les deux.
- **Double évaluation.** Chaque modèle est rejoué sur les mêmes courses dans deux conditions :
  - adhérence 0,7–1,0 : les conditions annoncées pour le tournoi, et la **condition de décision** ;
  - adhérence 0,5–1,0 : la condition v2, celle des séries précédentes.

  `training.train.evaluer` prend pour cela un argument facultatif `friction_min`, à 0,5 par défaut. `runs/courses_detail.py` le prend en 4e argument et ajoute alors le suffixe `-f07` au nom de son CSV.
- **Références v2 réévaluées.** Pour chaque graine, le meilleur modèle v2 de la même config livrée est réévalué sous 0,7. Son score sous 0,5 vient des séries 1 et 2.
- **Règles des mesures longues :**
  - les 17 circuits sont mesurés, dans les deux conditions, pour tout modèle à 11/12 ou plus dans au moins une condition ;
  - un modèle à 42/46 ou plus dans une condition repasse les 46 courses dans cette condition avec la graine de course 30000.
- **Marge de bruit.** Le même modèle varie de 1 à 6 points entre les graines de course 20000 et 30000 : le pilote livré fait 42 puis 43 sous 0,7, et immobilité g42 300k fait 43 puis 37. Un écart de ±3 ou moins est donc compté comme une égalité.

## Résultats par graine

Meilleur modèle de chaque run (sauvegarde 300k ou final), dans chaque condition. Total = courses finies sur 46 (12 de validation + 34 sur les 17 circuits). Quand les 17 circuits n'ont pas été mesurés, le tableau donne la validation sur 12. L'écart se lit par rapport à la v2 de la même graine, dans la même condition.

| Graine | Config | **Adhérence 0,7–1,0 (décision)** | Écart | Adhérence 0,5–1,0 (v2) | Écart |
|---|---|---|---|---|---|
| 2 | **v2 livré** (final) | **42**, graine 30000 : 43 | – | **43**, graine 30000 : 41 | – |
| 2 | friction 0,7 | 26 (300k) | **−16** | 26 (300k) | **−17** |
| 2 | immobilité 0,03 | 39 (300k) | −3 | 42, graine 30000 : 40 (300k) | −1 |
| 2 | les deux | 39 (300k) | −3 | 38 (300k) | −5 |
| 13 | **v2** (final) | **38** | – | **35** | – |
| 13 | friction 0,7 | 40 (300k) | +2 | 38 (300k) | +3 |
| 13 | immobilité 0,03 | 9/12 (final) | **raté** | 8/12 | **raté** |
| 13 | les deux | 39 (final) | +1 | 37 (final) | +2 |
| 21 | **v2** (final) | **9/12** | – | **10/12** | – |
| 21 | friction 0,7 | 41 (300k) | réparé | 39 (300k) | réparé |
| 21 | immobilité 0,03 | 40 (final) | réparé | 42, graine 30000 : 42 (final) | réparé |
| 21 | les deux | 38 (300k) | réparé | 29 (300k, 8/12) | −2/12 |
| 42 | **v2** (300k) | **40** | – | **38** | – |
| 42 | friction 0,7 | 36 (300k) | −4 | 33 (300k) | −5 |
| 42 | immobilité 0,03 | 43, graine 30000 : 37 (300k) | +3 | 44, graine 30000 : 41 (300k) | +6 |
| 42 | les deux | 10/12 (final) | **raté** | 8/12 | **raté** |

« raté » : moins de 11/12 en validation alors que la v2 de la même graine tient les 46 courses. « réparé » : la v2 de la même graine rate (9 ou 10/12), la v3 tient les 46 courses.

**Vitesse sous 0,7.** Meilleurs tours à Oschersleben / Zandvoort / MexicoCity, en secondes, et temps moyen sur les 17 circuits :

| Modèle | Tours O / Z / M (s) | Temps moyen 17 circuits |
|---|---|---|
| Pilote livré (v2, graine 2) | 46,1 / 65,9 / 59,4 | 202,8 s |
| Meilleur v3 : immobilité graine 42, 300k | 44,9 / 64,7 / 58,6 | 204,0 s |

Les écarts de vitesse suivent la graine, pas la configuration :
- graines 2 et 13 (v2 bonne) : la v3 est de 7 à 40 % plus lente au tour ;
- graines 21 et 42 (v2 faible ou lente) : la v3 est de 7 à 22 % plus rapide.

Runs, par graine 2, 13, 21 et 42 (préfixe `driver2-20261122-`) :

| Config | Graine 2 | Graine 13 | Graine 21 | Graine 42 |
|---|---|---|---|---|
| friction 0,7 | `211057` | `215355` | `222838` | `231500` |
| immobilité 0,03 | `212344` | `220629` | `224418` | `232656` |
| les deux | `214056` | `221558` | `230232` | `234601` |

## Conclusions

- **Aucun gain.** Sous 0,7, chaque configuration v3 :
  - répare la graine 21, ratée en v2 ;
  - en casse une autre : la graine 2 pour friction 0,7 (26/46), la graine 13 pour immobilité, la graine 42 pour les deux.

  Le reste est égal à la v2, aux 3 points de bruit près. Chaque configuration garde exactement une graine ratée sur quatre, comme la v2 : la robustesse ne s'améliore pas.
- **Le pilote livré tient déjà sous 0,7 : 42/46 et 43/46** avec les graines de course 20000 et 30000, contre 43 et 41 sous 0,5. Entraîné de 0,5 à 1,0, il couvre la plage 0,7–1,0. Les références v2 des graines 13 et 42 font même mieux sous 0,7 que sous 0,5 (38 contre 35, 40 contre 38) : l'adhérence 0,7 est la condition la plus facile.
- **S'entraîner sous 0,7 n'aide pas.** C'est la seule configuration qui perd des points avec deux graines sur quatre (−16 et −4). Même dans la condition où ils ont été entraînés, les modèles friction 0,7 ne font pas mieux que la v2 sur les graines où elle tenait.
- **La pénalité d'immobilité n'est pas démontrée.** Aucun des 12 runs n'est resté immobile, ni aucun des 24 modèles : le plus faible fait 6/12. Mais les runs friction 0,7, sans pénalité, n'ont pas été immobiles non plus. La v2 ne l'avait jamais été avec la config livrée sur ces 4 graines, et en v2, environ 1 run sur 11 restait immobile : 0 sur 12 reste du hasard possible.

  C'est la meilleure des trois sous 0,5 : trois graines sur quatre font 42/46 ou plus, contre une seule en v2. Cet avantage disparaît sous 0,7.
- **Le meilleur modèle v3 ne bat pas le pilote livré.** Il s'agit d'immobilité graine 42, sauvegarde 300k :

  | Condition | Graine de course 20000 | Graine de course 30000 |
  |---|---|---|
  | Adhérence 0,7 | 43 contre 42 | **37 contre 43** (validation 9/12) |
  | Adhérence 0,5 | 44 contre 43 | 41 contre 41 |

  Sur les quatre mesures, il totalise 165 contre 168 pour le pilote livré.
- **Il faut évaluer sous 0,7, sans réentraîner.** Pour juger un pilote dans les conditions du tournoi, il suffit de le rejouer sous l'adhérence 0,7 à 1,0 : l'option `friction_min` de `evaluer` le permet sans changer le MDP d'entraînement. `FRICTION_PLUIE` peut rester à 0,5.
- **Il faut plusieurs graines.** Avec une seule graine, cet essai aurait conclu dans les deux sens, selon la graine :
  - « immobilité : +6 » (graine 42) ;
  - « les deux : raté » (graine 42) ;
  - « friction 0,7 : −16 » (graine 2).

  Une configuration ne se juge qu'avec au moins quatre graines d'entraînement et deux graines de course.
- **Pilote livré conservé** : `driver2.yaml` et `submission/driver2/` ne changent pas.
