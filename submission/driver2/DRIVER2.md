# driver2

Pilote de Frank, entraîné seul sur la piste par apprentissage par renforcement. C'est le pilote « prudent » de l'équipe : un choc contre un mur lui coûte 10, contre 2 pour driver1.

| | |
|---|---|
| **Modèle livré** | run `driver2-20261125-193741-ppo`, livré le 25/11 (commit `2f77ee6`) : réentraînement de `driver2-20261124-233935-ppo` (série 5, CRA-107), mêmes poids |
| **Algorithme** | PPO (Stable-Baselines3) |
| **Entraînement** | 800 000 décisions (802 816), 8 courses en parallèle, 14 min |
| **Résultat** | sous l'adhérence de 0,7 à 1,0 annoncée pour le tournoi : **44,50/46 en moyenne** sur 4 graines de course (**minimum 44**), en comptant les 17 circuits d'entraînement ; **12/12** en validation sur des circuits jamais vus, avec chacune des 4 graines de course ; temps moyen **190,1 s** sur les 17 circuits, 10 % de moins que le pilote précédent |
| **Meilleur tour** | **42,2 s** (Oschersleben) |
| **Point faible** | sous la pluie à Montréal et Monza, il reste parfois collé à un mur jusqu'à l'abandon (section 7) |
| **Vérification** | `make verify DRIVER=driver2` : VALID |

---

## 1. Comment il apprend

**PPO** : le pilote essaie, reçoit une note à chaque décision, et ajuste petit à petit sa conduite pour avoir de meilleures notes. Il n'imite personne.

- **Pourquoi PPO.** La vitesse et le braquage sont continus, ce qui écarte DQN. PPO est stable : une correction ne peut pas trop changer le pilote d'un coup. Il est aussi simple à faire tourner sur 8 simulateurs en parallèle.
- **Le réseau de neurones.** Deux réseaux de 2 × 64 neurones, soit environ 13 500 paramètres. Le premier conduit, c'est lui qui est livré dans `model.onnx`. Le second juge si la situation est bonne et ne sert qu'à l'entraînement. Un réseau de 2 × 128 a été essayé (G1, G2) : il apprend plus lentement et ne fait pas mieux.

### Ce qu'il voit (38 valeurs)

| Entrée | Nombre | Rôle |
|---|---|---|
| Distances aux murs (LiDAR) | 18 | regroupées en 18 secteurs devant la voiture |
| Vitesse, braquage | 2 | son propre état |
| Pluie | 1 | 0 au sec, 1 sous forte pluie, pour freiner plus tôt |
| Commande précédente | 2 | se souvenir de ce qu'il vient de faire |
| 3 voitures les plus proches | 15 | vides en solo, utilisées par le champion |

### Ce qu'il fait

- **Vitesse** : de −2 m/s (marche arrière) à 10 m/s.
- **Braquage** : de −0,42 à +0,42 rad.

### Sa note, à chaque décision

| Élément | Valeur | But |
|---|---|---|
| Mètres avancés sur la piste | +1 par mètre | avancer |
| Temps qui passe | −0,01 | se dépêcher |
| À-coups de volant | −0,05 × changement | conduire fluide |
| Choc contre un mur | **−10** | éviter les murs (−2 pour driver1) |
| Contact avec une voiture | −1 | ne pas percuter |
| Abandon | −10 | ne jamais rester bloqué |

Une course d'entraînement **ne s'arrête pas au choc** : elle continue jusqu'à un abandon ou jusqu'à 150 s. Le pilote apprend ainsi à se dégager d'un mur, ce qui compte surtout sous la pluie. En course, un choc n'élimine jamais.

---

## 2. Réglages

Fichier `training/configs/driver2.yaml`. En gras, ce qui diffère de driver1.

| Réglage | Valeur | En clair |
|---|---|---|
| `pas` | **800 000** | décisions jouées au total ; le run s'arrête à 802 816, soit 98 corrections |
| `envs` | 8 | courses en parallèle |
| `n_steps` | **1024** | décisions par course avant chaque correction (8 192 au total, au lieu de 2 048) : moins de corrections, chacune fondée sur plus d'expérience ; d'où 800 000 décisions au lieu de 400 000 |
| `batch_size` | 64 | taille des paquets étudiés d'un coup |
| `n_epochs` | **20** | chaque lot d'expérience est étudié 20 fois au lieu de 10 |
| `learning_rate` | 0,0003 | taille de chaque correction |
| `gamma` | **0,995** | il anticipe environ 10 s devant lui, au lieu de 5 s |
| `ent_coef` | **0,005** | il garde un peu de hasard dans ses gestes, pour ne pas rester figé |
| `graine` | **21** | départ du hasard |
| `penalite_choc` | **10** | un choc coûte 10 |
| `fin_sur_choc` | **non** | un choc ne termine pas la course d'entraînement |
| `meteo` | oui | pluie aléatoire pendant l'entraînement |
| `adversaires` | aucun | entraîné seul sur la piste |

Le fichier est identique à la configuration enregistrée dans le `meta.json` du run livré. L'entraînement est reproductible au bit près : relancer `make train DRIVER=driver2` redonne le même modèle (voir la section 7).

---

## 3. Circuits

| Groupe | Circuits | Rôle |
|---|---|---|
| **Entraînement (17)** | Austin, BrandsHatch, Catalunya, Hockenheim, IMS, Melbourne, Montreal, Monza, MoscowRaceway, Nuerburgring, Sakhir, SaoPaulo, Sepang, Shanghai, Silverstone, Spielberg, YasMarina | il apprend dessus ; on y mesure aussi chaque candidat |
| **Validation (3)** | Oschersleben, Zandvoort, MexicoCity | jamais vus à l'entraînement ; on mesure et on choisit dessus |
| **Test (3)** | Spa, Budapest, Sochi | jamais utilisés, gardés pour la mesure finale |

Les 3 circuits de validation se sont révélés trop flatteurs : un pilote à 11/12 en validation ne finissait que 17 courses sur 34 sur les 17 autres circuits. Chaque candidat est donc aussi mesuré sur les 17 circuits d'entraînement, au sec et sous la pluie.

---

## 4. Météo

Le simulateur d'Epitech reste toujours au sec. La pluie est ajoutée par `training/env.py`.

- Toutes les 20 s, un nouveau temps est tiré : **sec 30 % du temps**, sinon une pluie d'intensité variable, le plus souvent légère.
- **La piste glisse** : l'adhérence des pneus passe de 1,0 au sec à 0,5 sous forte pluie. Elle est appliquée au vrai moteur physique.
- **Le capteur se trompe** : ±0,1 % au sec, jusqu'à ±10 % sous forte pluie, et jusqu'à 5 % des rayons décrochent.
- **Le pilote lit la pluie** dans ses entrées, il n'a pas à la deviner.

---

## 5. Progrès pendant l'entraînement du modèle livré

| Avancement | Durée d'une course d'entraînement | Note moyenne | Hésitation |
|---|---|---|---|
| début | 11 s | −869 | 1,01 |
| 25 % | 16 s | −34 | 0,91 |
| 50 % | 68 s | −76 | 0,78 |
| 75 % | 89 s | 170 | 0,67 |
| fin | **104 s** | **321** | **0,57** |

Valeurs relevées dans les courbes TensorBoard du run `driver2-20261125-193741-ppo`, au point enregistré le plus proche de chaque quart de l'entraînement.

Une course d'entraînement dure au plus 150 s ; elle s'arrête plus tôt quand le pilote abandonne. Au début, il abandonne vite et accumule les chocs, d'où une note très négative. Vers 25 %, ses courses ne durent que 16 s : il avance trop peu et se fait éliminer par la règle de stagnation (10 s sans progrès). À mi-parcours, ses courses s'allongent (68 s), mais sa note reste négative. Il en sort ensuite : ses courses durent 104 s en moyenne à la fin et sa note monte à 321.

« Hésitation » est la part de hasard dans ses commandes : plus elle baisse, plus ses gestes sont sûrs.

---

## 6. Entraînements, l'un après l'autre

Chaque essai repart du pilote livré à ce moment-là et ne change qu'un seul réglage. Deux mesures, avec les mêmes courses pour tous :

- **Validation** : `make evaluer`, 12 courses sur les 3 circuits de validation, au sec et sous la pluie en alternance ;
- **Total** : les 12 courses de validation plus 34 courses sur les 17 circuits d'entraînement (une au sec, une sous la pluie par circuit), soit 46.

Les 34 courses sur les circuits d'entraînement viennent de `runs/courses_detail.py`, un script personnel hors dépôt. Il appelle la même fonction `training.train.evaluer` que `make evaluer` (politique déterministe, pas de fin sur choc, 6 000 pas au plus), sur les 17 circuits d'**entraînement**, avec 2 courses par circuit : une au sec, une sous la pluie. La graine de course vaut 20000 par défaut, ou 30000 pour la vérification. Il écrit le détail de chaque course (résultat, temps au tour, chocs) dans `runs/<run>/courses-entrainement.csv` (`-g30000` pour l'autre graine). Il pourra être intégré à `training/` si l'équipe le valide.

```
python runs/courses_detail.py <run> entrainement [30000]   # 17 circuits × sec et pluie
python runs/courses_detail.py <run> validation [30000]     # les 12 courses de make evaluer
```

On mesure aussi les sauvegardes à 300k et 400k : le dernier modèle n'est pas toujours le meilleur. Le tableau donne le meilleur modèle de chaque essai. Le détail de tous les essais est dans `training/configs/essais/RESULTATS-driver2.md`.

| Date | Run | Ce qui change | Validation | Total /46 | Chocs / course | Tours Osche / Zandv / Mexic |
|---|---|---|---|---|---|---|
| 13/11 | `155108` | premier run : choc −5, 500k pas, graine 2 : livré | 8/12 | — | 6,2 | 34,8 / 50,5 / 46,4 s |
| 20/11 | `093517` | idem sur 2M pas | 5/12 | — | 45,8 | 35,7 / 47,0 / — |
| 20/11 | `122717` | **choc −10**, graine 7, sauvegarde 300k : livré | 11/12 | 28 | 0 | 39,2 s (Osche) |
| 20/11 | `153430` | **sans fin sur choc**, 400k : livré | 12/12 | 37 | 4,8 | 41,2 / 59,4 / 54,4 s |
| 20/11 | `163329` | coût du temps 0,02, sauvegarde 400k | 8/12 | — | 17,2 | 39,9 / 55,2 / 52,2 s |
| 20/11 | `165157` | **gamma 0,995**, 400k : livré | 12/12 | 37 | 0,2 | 41,4 / 60,0 / 55,7 s |
| 20/11 | `200330` | douceur 0,1 | 12/12 | 38 | 1,2 | 43,9 / 66,3 / 61,0 s |
| 20/11 | `202627` | douceur 0,1 sur 1M pas, sauvegarde 700k | 10/12 | — | 5,2 | 35,6 / 52,2 / 48,1 s |
| 21/11 | `112230` | config `165157`, graine 2 | 0/12 | — | — | ne roule jamais |
| 21/11 | `120735` | **`ent_coef` 0,005**, 500k : livré | 12/12 | 39 | 0 | 44,8 / 63,5 / 59,8 s |
| 21/11 | `131748` | idem sur 1M pas | 11/12 | 35 | — | 37,8 / 55,2 / 51,4 s |
| 21/11 | `152915` | réseau 2 × 128 sur 1M pas, sauvegarde 600k | 12/12 | 37 | — | 48,6 / 72,2 / 65,7 s |
| 21/11 | `185118` | série : **`n_epochs` 20**, graine 2, sauvegarde 400k | 12/12 | **45** | 0 | 45,9 / 65,5 / 59,1 s |
| 21/11 | `184119` | série : `n_epochs` 20, graine 7 | 6/12 | — | 0,1 | 46,8 / 65,9 / — |
| 21/11 | `195132` | série : `clip_range` 0,1, graine 2 | 12/12 | 43 | 0 | 55,0 / 79,5 / 72,2 s |
| 21/11 | **`214154`** | **`n_epochs` 20, graine 2, réentraîné, modèle final (401 408 pas) : livré du 22/11 au 24/11** | **12/12** | **43** | **0,2** | **46,1 / 65,9 / 59,4 s** |
| 22/11 | 12 runs, `211057` à `234601` | essai v3 (CRA-105) : entraîner sous l'adhérence 0,7, pénalité d'immobilité 0,03, ou les deux ; graines 2, 13, 21 et 42 | — | aucun gain sous 0,7 | — | — |
| 23/11 | 12 runs, `194118` à `230119` | série 4 (CRA-106) : livrée, `clip_range` 0,1 et **`n_steps` 512 sur 600k pas**, graines 2, 13, 21, 42, 1 et 5 | — | médianes sous 0,7 : 39,5 / 33 / **40** | — | — |
| 23/11 | **`194118`** | **`n_steps` 512, 600k pas, graine 2, modèle final (602 112 pas) : livré du 24/11 au 25/11** (réentraîné à l'identique le 24/11, `180912`) | **12/12** | **44** | **0,6** | **47,1 / 67,9 / 62,6 s** |
| 24/11 | 24 runs, `190742` à `045812` | série 5 (CRA-107) : config de `194118` sur 8 nouvelles graines, `cout_temps` 0,015, `cout_temps` 0,02 et **`n_steps` 1024 sur 800k pas** ; graines 2, 13, 21, 42, 1 et 5 (3 à 11 pour la config de `194118`) | — | médianes sous 0,7 : 40,5 / 40,5 / 35,5 / **42,5** | — | — |
| 24/11 | **`233935`** | **`n_steps` 1024, 800k pas, graine 21, modèle final (802 816 pas) : modèle livré** (réentraîné à l'identique le 25/11, `193741`) | **12/12** | **44** | **0,9** | **42,5 / 61,1 / 55,6 s** |

En gras : les réglages gardés. « Livré » : le modèle a été le pilote driver2 jusqu'à la livraison suivante. Tous les runs sont archivés dans `archives/` avec une note. Les chiffres de ce tableau et des notes (`note.md`) viennent de `make evaluer` (12 courses de validation) et, quand elles ont été jouées, des 46 courses. Les cinq dernières lignes sont mesurées par `runs/courses_detail.py` sous l'adhérence 0,7 (graine de course 20000) : voir `training/configs/essais/RESULTATS-v3.md` (branche de CRA-105), `RESULTATS-s4.md` (branche de CRA-106) et, pour la série 5, la branche de CRA-107. Le `bilan.json` de chaque archive est l'évaluation automatique de fin d'entraînement : 6 courses seulement (une au sec et une sous la pluie sur chacun des 3 circuits de validation, `eval_episodes: 2` ; 12 pour l'essai 2M pas), avec la graine de course `graine` + 10 000. Elle ne sert pas au choix.

**Ce qu'on en retient**

- **Laisser la course continuer après un choc règle la pluie.** Avec un arrêt au premier choc, le pilote n'apprend jamais à se dégager d'un mur : 4 courses finies sur 17 sous la pluie. Sans arrêt, 11 sur 17.
- **Un choc doit coûter cher.** À −5, il tape les murs ; à −10, il ne les touche presque plus. −7, −8 et −12 font moins bien.
- **Anticiper plus loin rend la conduite propre.** Avec gamma 0,995, il freine avant le virage au lieu de taper le mur : 0,2 choc par course.
- **Un peu de hasard aide contre le piège de l'immobilité.** Sans `ent_coef`, une graine sur trois apprend à rester sur place : rester immobile coûte environ 12, un peu plus qu'un choc. `ent_coef` 0,005 a sauvé la graine 2, qui restait immobile sans lui. Mais 4 runs sur 43 avec `ent_coef` 0,005 sont restés immobiles du début à la fin (série 1 : `penalite_choc` 12 avec la graine 7 ; série 2 : `n_epochs` 15 avec la graine 13, `clip_range` 0,1 avec la graine 2, `batch_size` 128 avec la graine 13). D'autres runs avaient une sauvegarde immobile à 300k avant de repartir : `n_epochs` 5 avec la graine 2 (0/12 à 300k, 11/12 au final) et, avec `ent_coef` 0,003, la graine 7 (0/12 à 300k, 12/12 au final). Il réduit le piège de l'immobilité sans le supprimer : dans la série 5, `n_steps` 1024 avec la graine 1 est encore immobile à 600k et 700k, et ne fait que se traîner au final (0/12).
- **Étudier chaque lot 20 fois au lieu de 10 (`n_epochs` 20) est le meilleur levier trouvé** : 45/46 pour la sauvegarde 400k, 43/46 pour le modèle final livré, qui a une mise à jour PPO de plus.
- **Vitesse et pluie s'opposent.** Toutes les versions rapides (1M pas, coût du temps plus fort, affinage) perdent des courses sous la pluie. Le pilote livré est la seule exception trouvée (série 5) : 10 % plus rapide que le précédent pour une arrivée de moins sur 184 courses, mais ses abandons sous la pluie sont plus durs (section 7).
- **Augmenter le coût du temps ne rend pas plus rapide** (série 5, `cout_temps` 0,015 et 0,02) : en moyenne, les pilotes sont même plus lents (218 et 228 s sur les 17 circuits, contre 216 s pour la config de `194118`) et moins réguliers (médianes 40,5 et 35,5).
- **Le hasard pèse lourd.** La même configuration donne 45/46 avec la graine 2 et 6/12 avec la graine 7.
- **`n_steps` 512 rend l'entraînement plus régulier d'une graine à l'autre** (série 4, 6 graines, sous l'adhérence 0,7) : aucune graine à moins de 11/12, médiane 40/46, et 40 aussi sur le modèle final seul. La configuration précédente fait 39,5 (35 sur le modèle final seul) et `clip_range` 0,1 fait 33 (30,5). Sur 8 nouvelles graines (série 5), la médiane reste à 40,5, mais 5 modèles finaux sur 8 tombent sous 11/12 (médiane du final seul : 34,5) : la régularité du modèle final ne se confirme pas.
- **`n_steps` 1024 donne la meilleure médiane de la série 5** (6 graines, sous l'adhérence 0,7) : 42,5/46, et 41,5 sur le modèle final seul. Une graine sur six (la graine 1) reste prise dans le piège de l'immobilité. La graine 21 donne le pilote livré.
- **Juger sur plusieurs graines d'entraînement et de course.** Un candidat peut chuter avec une autre graine de course : `n_steps` 512 graine 13, modèle final, passe de 43 à 37/46. Le pilote livré, comme le précédent, a été confirmé sur 4 graines de course.

### Mesure sur 46 courses, avec quatre graines de course

Pour vérifier qu'un pilote n'a pas seulement eu de la chance sur 46 courses précises, on les relance avec d'autres départs et une autre météo : graines de course 20000, 30000, 40000 et 50000, sous l'adhérence 0,7 (FU2). Tours : meilleur tour sur les validations des 4 graines. Temps moyen : courses finies sur les 17 circuits. Chocs : moyenne sur toutes les courses.

| Modèle | 20000 | 30000 | 40000 | 50000 | **Moyenne /46** | **Min** | Tours O / Z / M | Temps moyen 17c | Chocs/course |
|---|---|---|---|---|---|---|---|---|---|
| `214154` (livré du 22/11 au 24/11) | 42 | 43 | 44 | 44 | 43,25 | 42 | 46,1 / 65,9 / 59,4 s | 202,4 s | 0,99 |
| `194118` (livré du 24/11 au 25/11) | 44 | 44 | 45 | 46 | 44,75 | 44 | 47,0 / 67,8 / 62,4 s | 211,3 s | 0,33 |
| **`233935` (livré)** | **44** | **45** | **45** | **44** | **44,50** | **44** | **42,2 / 61,0 / 55,6 s** | **190,1 s** | **2,94** |

C'est la règle du tournoi qui fait préférer les arrivées à la vitesse : une course fait 3 tours (`_REQUIRED_LAPS` dans `simulation/env_simulation.py`), les arrivées sont classées au temps, puis les abandons, et un abandon n'est jamais devant une arrivée (sujet, partie 3). `194118` avait été choisi pour ses arrivées : 1,5 course de plus que `214154` en moyenne, avec un minimum de 44 contre 42, et trois fois moins de chocs, mais un peu plus lent (211,3 s contre 202,4 s). Dans la série 4, la sauvegarde 400k de `n_steps` 512 graine 13 (45,25 de moyenne, minimum 44) n'avait pas été retenue : ses arrivées étaient dans le bruit face à `194118`, mais elle était plus lente (217,5 s) et touchait plus les murs (1,35 choc par course).

**Pourquoi `233935` remplace `194118`.** La série 5 (CRA-107) cherchait à gagner en vitesse sans perdre d'arrivées, avec une règle fixée avant les essais : sur les 4 graines de course, sous l'adhérence 0,7, une moyenne d'au moins 44,25/46, un minimum d'au moins 44 et un temps moyen d'au plus 205,0 s sur les 17 circuits. `194118` la remplit par ses arrivées, mais pas par son temps (211,3 s) ; `233935` est le seul modèle de la série 5 à la remplir. Il finit autant de courses à une près sur 184 (44,50 contre 44,75 de moyenne, même minimum) et il est 10 % plus rapide : 190,1 s contre 211,3 s en temps moyen sur les 17 circuits, 42,2 s contre 47,0 s au meilleur tour à Oschersleben.

Il touche en revanche plus les murs : 2,94 chocs par course contre 0,33. Presque tous viennent de 4 abandons où il reste collé à un mur sous la pluie, à Montréal et à Monza (section 7) ; sur ses courses finies, il fait 0,51 choc par course, contre 0,32 pour `194118`. Les chocs ne comptent pas dans le classement, mais ces abandons ne tombent pas au hasard. `194118` reste donc archivé comme solution de repli (`archives/driver2-20261124-180912-ppo`, configuration au commit `f607576`) : il finit Montréal et Monza sous la pluie avec les 4 graines de course.

### Conditions de la pédagogie (FU2)

La pédagogie annonce pour le tournoi une adhérence de 0,7 à 1,0 sous la pluie. Le pilote s'entraîne avec une adhérence de 0,5 à 1,0 (section 4), mais il est choisi sous 0,7 à 1,0. Sur les 46 courses, avec une adhérence de 0,7 à 1,0 :

| `233935` (livré), adhérence 0,7–1,0 | Validation | 17 circuits (sec / pluie) | Total /46 | Temps moyen 17c |
|---|---|---|---|---|
| graine de course 20000 | 12/12 | 32/34 (17 / 15) | **44** | 190,4 s |
| graine de course 30000 | 12/12 | 33/34 (17 / 16) | **45** | 189,2 s |
| graine de course 40000 | 12/12 | 33/34 (17 / 16) | **45** | 190,4 s |
| graine de course 50000 | 12/12 | 32/34 (17 / 15) | **44** | 190,2 s |

Sous l'adhérence 0,5 à 1,0, il fait 45/46 (graine de course 30000 : 43/46). `194118` faisait 44, 44, 45 et 46/46 sous 0,7, et 43 et 44/46 sous 0,5 ; `214154`, 42 et 43/46 sous 0,7, et 43 et 41/46 sous 0,5 : entraîné sur la plage la plus large, un pilote couvre celle du tournoi. L'essai v3 (CRA-105) a aussi testé l'inverse : entraîner sous 0,7 à 1,0, une pénalité d'immobilité, ou les deux. Aucun n'a amélioré les arrivées, sur quatre graines d'entraînement. Le détail est dans `training/configs/essais/RESULTATS-v3.md`, sur la branche de CRA-105.

---

## 7. Ce sur quoi il a du mal

Les virages sont mesurés sur la ligne centrale de chaque circuit (`simulation/maps/<circuit>/<circuit>_centerline.csv`) : le rayon de courbure y est calculé point par point, lissé sur ±2 m, et un virage est compté comme « serré » quand son rayon passe sous 2 m.

1. **Shanghai.** Jusqu'à la série 3, aucun modèle ne l'avait fini, ni au sec ni sous la pluie. Le pilote livré le finit au sec avec toutes les graines de course. Sous la pluie, il le finit avec 3 graines de course sur 4 sous l'adhérence 0,7, et avec les deux graines mesurées sous 0,5 (`194118` l'abandonnait avec ces deux-là). La plus longue ligne droite du jeu (110 m) y débouche sur un virage de rayon compris entre 0,7 et 1,1 m selon le lissage, le plus serré du jeu dans tous les cas. C'est de l'ordre du rayon de braquage minimal de la voiture, environ 0,74 m : le pilote arrive vite et doit tourner presque en butée.
2. **Montréal et Monza sous la pluie.** C'est le point faible du pilote livré. Sous l'adhérence 0,7, il abandonne par stagnation à Montréal sous la pluie avec 2 graines de course sur 4 (40000 et 50000, 137 et 156 chocs) et à Monza sous la pluie avec 2 sur 4 (30000 et 50000, 39 et 116 chocs) : il reste plaqué contre un mur jusqu'à l'élimination. Ce n'est pas le hasard d'une graine de course : il sort aussi de la piste à Montréal sous la pluie sous l'adhérence 0,5 (graine 30000, 104 chocs), et ses sauvegardes 600k et 700k abandonnent déjà à Montréal sous la pluie (94 à 142 chocs). `194118` finit ces deux courses avec les 4 graines de course, avec 0 à 4 chocs.
3. **Vitesse ou pluie.** Jusqu'à la série 4, toutes les versions plus rapides perdaient des courses sous la pluie. `131748` (1M pas) tourne en 37,8 s à Oschersleben contre 46,1 s pour le pilote livré alors (`214154`), mais finit 8 courses de moins sur 46. Un réseau plus grand (2 × 128) ne change rien : la limite vient plutôt de ce que le pilote perçoit (LiDAR à l'avant seulement, aucune mémoire) et de l'adhérence sous forte pluie (0,5). Le classement se fait à l'arrivée (section 6), donc on a choisi de finir. Le pilote livré est 10 % plus rapide que `194118` pour presque autant d'arrivées, mais il n'abandonne que sous la pluie, et sur d'autres courses que `194118` (une seule en commun : Shanghai, graine 20000) :
   - sous l'adhérence 0,7 : à MoscowRaceway et Shanghai (graine de course 20000), à Monza (30000), à Montréal (40000), et à Montréal et Monza (50000), toujours par stagnation ;
   - sous l'adhérence 0,5 : à YasMarina (20000), et à MexicoCity, deux fois, et Montréal (30000), par stagnation sauf la sortie de piste à Montréal.
4. **Le piège de l'immobilité.** Un pilote qui reste sur place est éliminé au bout de 10 s et perd environ 12 (abandon 10, temps 2) : c'est moins qu'un essai qui finit dans un mur après plusieurs chocs à −10. Certains entraînements apprennent donc à ne plus bouger. D4 (learning rate 0,0002, `100238`) est immobile dès 350k pas. La configuration de `165157`, avec la graine 2 au lieu de 7 (`112230`), ne roule jamais : 0/12. `ent_coef` 0,005, qui garde un peu de hasard dans les gestes, le réduit sans le supprimer : 4 runs sur 43 sont restés immobiles malgré lui (voir la section 6). Une pénalité d'immobilité (0,03 sous 0,3 m/s) a été testée dans l'essai v3 (CRA-105) : aucun run n'y est resté immobile, avec ou sans elle, donc son effet sur le piège n'est pas démontré, et elle n'améliore pas les arrivées.
5. **Des circuits de validation trop faciles.** Mesuré sur les lignes centrales des circuits, Oschersleben n'a aucun virage de rayon inférieur à 2 m et Zandvoort un seul, contre 3 à Shanghai et 11 à YasMarina. MexicoCity, avec 7 virages serrés, est le seul exigeant des trois. Conséquence : le pilote du 20/11 faisait 11/12 en validation, mais seulement 17/34 sur les 17 circuits d'entraînement. D'où le deuxième banc de mesure (section 6).
6. **Le bug d'export.** `make export` ajoute les nouveaux poids à la fin de `submission/driver2/model.onnx.data` au lieu de remplacer le fichier : après 5 exports, il faisait 135 Ko au lieu de 27 Ko. Le pilote marche, mais le livrable est pollué. Contournement : supprimer le fichier avant chaque export (voir « Reproduire »). La correction tient en une ligne dans `training/exporter.py`, code commun : proposée dans la PR #26 (CRA-103), en relecture.
7. **L'entraînement est reproductible au bit près, mais le modèle final n'est pas une sauvegarde.** Réentraînée avec la même graine, une configuration redonne exactement les mêmes poids à chaque sauvegarde.
   - Avec la configuration précédente (`n_steps` 256), c'est vérifié sur trois runs avec la graine 2 : le run `214154`, l'essai `n_epochs` 20 de la première série et le run à 600k de la deuxième. Une mise à jour PPO y porte sur 2 048 pas (256 × 8 simulateurs). Un run à `pas: 400000` s'arrête donc à 401 408 pas, et son modèle final a une mise à jour PPO de plus que la sauvegarde 400k. Cette seule mise à jour sépare les 45/46 de la sauvegarde 400k et les 43/46 du modèle final de `214154`. D'où la règle : évaluer les sauvegardes, pas seulement le modèle final.
   - Le pilote livré est le modèle final d'un run à `pas: 800000`, arrêté à 802 816 pas (98 mises à jour de 8 192 pas). Il a été entraîné pendant la série 5 sur la branche de CRA-107 (`233935`), puis réentraîné avec `make train DRIVER=driver2` sur cette branche (`193741`) : les 13 tenseurs de la politique sont identiques, pour le modèle final comme pour les sauvegardes 600k et 700k. Le pilote précédent avait suivi le même chemin (`194118` sur la branche de CRA-106, puis `180912` ici, mêmes poids). Le modèle livré se refait donc d'une branche à l'autre, sans choisir de sauvegarde.

   Le hasard pèse en revanche entre graines : 45/46 avec la graine 2, 6/12 avec la graine 7 pour `n_epochs` 20. Il faut donc juger une configuration sur plusieurs graines (six dans la série 4, quatre à huit dans la série 5).

---

## 8. Prochaines étapes

- **Fait :**
  - la 2e série d'essais autour de `n_epochs` 20 : le résultat dépend fortement de la graine d'entraînement (voir `training/configs/essais/RESULTATS-driver2.md`) ;
  - l'adhérence de 0,7 à 1,0 annoncée par la pédagogie est évaluée sans réentraîner : le pilote précédent faisait 42/46 et 43/46. Réentraîner à 0,7 fait passer la meilleure graine (2) de 42 à 26 (essai v3, CRA-105) ;
  - la série 4 (CRA-106), sur 6 graines d'entraînement : `n_steps` 512 est la configuration la plus régulière, et son modèle final avec la graine 2 a été le pilote livré du 24/11 au 25/11 (44,75/46 en moyenne sous 0,7 sur 4 graines de course, voir `training/configs/essais/RESULTATS-s4.md` sur la branche de CRA-106) ;
  - la série 5 (CRA-107), pour gagner en vitesse sans perdre d'arrivées : `n_steps` 1024 avec la graine 21 devient le pilote livré (44,50/46 en moyenne sous 0,7 sur 4 graines de course, 190,1 s contre 211,3 s), `194118` restant la solution de repli (section 6).
- **Code commun :**
  - le bug d'export (`exporter.py`) : correctif proposé, PR #26 (CRA-103) en relecture ;
  - `CONFIG=` dans `make train` et les notes en UTF-8 dans `garder.py` : correctif proposé, PR #27 (CRA-104) en relecture ;
  - pénalité d'immobilité : testée dans l'essai v3 (CRA-105, branche séparée non fusionnée), résultat non concluant ; driver2 ne l'utilise pas ;
  - à proposer : un LiDAR à 360° et une mémoire (plusieurs images LiDAR empilées) ;
  - à proposer : l'intégration de `courses_detail.py` dans `training/`.
- **Pistes restantes :**
  - les abandons sous la pluie à Montréal et Monza, où le pilote livré reste collé au mur (section 7) ;
  - un autre découpage des circuits de validation, trop faciles aujourd'hui (section 7) ;
  - une stratégie face aux adversaires.

---

## Reproduire

```
make train DRIVER=driver2                                  # entraîner (redonne le même modèle au bit près) ; affiche le run créé dans runs/
rm submission/driver2/model.onnx.data                      # sinon l'export s'ajoute à l'ancien fichier
make export RUN=<run créé par make train> DRIVER=driver2   # livrer un run : il doit exister dans runs/ (non versionné) ;
                                                           # le run livré est driver2-20261125-193741-ppo
make verify DRIVER=driver2                                 # vérifier la livraison
make evaluer RUN="<run1> <run2>"                           # comparer sur 12 courses
```
