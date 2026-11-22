# driver2

Pilote de Frank, entraîné seul sur la piste par apprentissage par renforcement. C'est le pilote « prudent » de l'équipe : un choc contre un mur lui coûte 10, contre 2 pour driver1.

| | |
|---|---|
| **Modèle livré** | run `driver2-20261121-214154-ppo`, livré le 22/11 (commit `a9ac8af`) |
| **Algorithme** | PPO (Stable-Baselines3) |
| **Entraînement** | 400 000 décisions, 8 courses en parallèle, 7 min |
| **Résultat** | **12 courses finies sur 12** sur des circuits jamais vus (sec 6/6, pluie 6/6) ; **43/46** en ajoutant les 17 circuits d'entraînement |
| **Meilleur tour** | **46,1 s** (Oschersleben) |
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
| `pas` | **400 000** | décisions jouées au total |
| `envs` | 8 | courses en parallèle |
| `n_steps` | 256 | décisions par course avant chaque correction (2 048 au total) |
| `batch_size` | 64 | taille des paquets étudiés d'un coup |
| `n_epochs` | **20** | chaque lot d'expérience est étudié 20 fois au lieu de 10 |
| `learning_rate` | 0,0003 | taille de chaque correction |
| `gamma` | **0,995** | il anticipe environ 10 s devant lui, au lieu de 5 s |
| `ent_coef` | **0,005** | il garde un peu de hasard dans ses gestes, pour ne pas rester figé |
| `graine` | **2** | départ du hasard |
| `penalite_choc` | **10** | un choc coûte 10 |
| `fin_sur_choc` | **non** | un choc ne termine pas la course d'entraînement |
| `meteo` | oui | pluie aléatoire pendant l'entraînement |
| `adversaires` | aucun | entraîné seul sur la piste |

Le fichier est identique à la configuration enregistrée dans le `meta.json` du run livré. Mais relancer `make train DRIVER=driver2` ne redonne pas le même modèle au bit près : les 8 simulateurs en parallèle rendent l'entraînement non déterministe. On obtient un pilote du même niveau, pas le même (voir la section 7).

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
| début | 11 s | −1 058 | 1,00 |
| 25 % | 30 s | −135 | 0,82 |
| 50 % | 69 s | −67 | 0,66 |
| 75 % | 61 s | 43 | 0,53 |
| fin | **73 s** | **42** | **0,47** |

Une course d'entraînement dure au plus 150 s ; elle s'arrête plus tôt quand le pilote abandonne. Au début, il abandonne vite et accumule les chocs, d'où une note très négative.

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
| 21/11 | **`214154`** | **`n_epochs` 20, graine 2, 400k, réentraîné : modèle livré** | **12/12** | **43** | **0,2** | **46,1 / 65,9 / 59,4 s** |

En gras : les réglages gardés. « Livré » : le modèle a été le pilote driver2 jusqu'à la livraison suivante. Tous les runs sont archivés dans `archives/` avec une note.

**Ce qu'on en retient**

- **Laisser la course continuer après un choc règle la pluie.** Avec un arrêt au premier choc, le pilote n'apprend jamais à se dégager d'un mur : 4 courses finies sur 17 sous la pluie. Sans arrêt, 11 sur 17.
- **Un choc doit coûter cher.** À −5, il tape les murs ; à −10, il ne les touche presque plus. −7, −8 et −12 font moins bien.
- **Anticiper plus loin rend la conduite propre.** Avec gamma 0,995, il freine avant le virage au lieu de taper le mur : 0,2 choc par course.
- **Un peu de hasard évite le piège de l'immobilité.** Sans `ent_coef`, une graine sur trois apprend à rester sur place : rester immobile coûte environ 12, un peu plus qu'un choc. Avec `ent_coef` 0,005, toutes les graines roulent.
- **Étudier chaque lot 20 fois au lieu de 10 (`n_epochs` 20) est le meilleur levier trouvé** : 45/46 au mieux, 43/46 une fois réentraîné.
- **Vitesse et pluie s'opposent.** Toutes les versions rapides (1M pas, coût du temps plus fort, affinage) perdent des courses sous la pluie.
- **Le hasard pèse lourd.** La même configuration donne 45/46 avec la graine 2 et 6/12 avec la graine 7. Il faut toujours essayer deux graines.

### Mesure sur 46 courses, avec deux graines de course

Pour vérifier que le pilote livré n'a pas seulement eu de la chance sur ces 46 courses précises, on les relance avec d'autres départs et une autre météo (graine de course 30000 au lieu de 20000).

| Modèle | Validation | 17 circuits (sec / pluie) | Total /46 | Course moyenne en validation |
|---|---|---|---|---|
| `120735` (livré avant), graine 20000 | 12/12 | 27/34 (14 / 13) | 39 | 175,3 s |
| `120735`, graine 30000 | 12/12 | 25/34 (13 / 12) | 37 | 177,4 s |
| **`214154` (livré), graine 20000** | **12/12** | **31/34 (16 / 15)** | **43** | **175,4 s** |
| **`214154`, graine 30000** | **12/12** | **29/34 (16 / 13)** | **41** | **177,7 s** |

Il finit 4 courses de plus que le pilote précédent avec chaque graine, à la même vitesse.

---

## 7. Ce sur quoi il a du mal

1. **Shanghai.** Aucun modèle ne l'a fini, ni au sec ni sous la pluie. La plus longue ligne droite du jeu (110 m) y débouche sur le virage le plus serré (rayon de 0,84 m). Ce rayon est à peine plus grand que le rayon de braquage minimal de la voiture, environ 0,74 m : le pilote arrive vite et doit tourner presque en butée.
2. **Vitesse ou pluie.** Toutes les versions plus rapides perdent des courses sous la pluie. `131748` (1M pas) tourne en 37,8 s à Oschersleben contre 46,1 s, mais finit 8 courses de moins sur 46. Un réseau plus grand (2 × 128) ne change rien : la limite vient plutôt de ce que le pilote perçoit (LiDAR à l'avant seulement, aucune mémoire) et de l'adhérence sous forte pluie (0,5). Le classement se fait à l'arrivée, donc on a choisi de finir. Le pilote livré abandonne encore sous la pluie à YasMarina (graine de course 20000), et à Montreal, Monza et MoscowRaceway (graine 30000).
3. **Le piège de l'immobilité.** Un pilote qui reste sur place est éliminé au bout de 10 s et perd environ 12 (abandon 10, temps 2) : c'est moins qu'un essai qui finit dans un mur après plusieurs chocs à −10. Certains entraînements apprennent donc à ne plus bouger. D4 (learning rate 0,0002, `100238`) est immobile dès 350k pas. La configuration de `165157`, avec la graine 2 au lieu de 7 (`112230`), ne roule jamais : 0/12. `ent_coef` 0,005, qui garde un peu de hasard dans les gestes, l'évite. Une pénalité d'immobilité dans le code commun le réglerait à la source.
4. **Des circuits de validation trop faciles.** Mesuré sur les lignes centrales des circuits, Oschersleben n'a aucun virage de rayon inférieur à 2 m et Zandvoort un seul, contre 3 à Shanghai et 11 à YasMarina. MexicoCity, avec 7 virages serrés, est le seul exigeant des trois. Conséquence : le pilote du 20/11 faisait 11/12 en validation, mais seulement 17/34 sur les 17 circuits d'entraînement. D'où le deuxième banc de mesure (section 6).
5. **Le bug d'export.** `make export` ajoute les nouveaux poids à la fin de `submission/driver2/model.onnx.data` au lieu de remplacer le fichier : après 5 exports, il faisait 135 Ko au lieu de 27 Ko. Le pilote marche, mais le livrable est pollué. Contournement : supprimer le fichier avant chaque export (voir « Reproduire »). La correction tient en une ligne dans `training/exporter.py`, code commun.
6. **L'entraînement n'est pas reproductible au bit près.** Les 8 simulateurs en parallèle le rendent non déterministe. Réentraînée avec la même graine et le même commit, la configuration livrée donne 43/46 au lieu de 45/46. Le hasard pèse aussi entre graines : 45/46 avec la graine 2, 6/12 avec la graine 7. Il faut donc juger une configuration sur plusieurs graines, et `driver2.yaml` redonne un pilote du même niveau, pas le même modèle.

---

## 8. Prochaines étapes

- **Une 2e série d'essais autour de `n_epochs` 20**, un réglage à la fois, mesurée sur les deux bancs et avec deux graines de course :
  - d'abord la robustesse : la configuration livrée avec les graines d'entraînement 13, 21 et 42 ;
  - puis `n_epochs` 15 et 30, `clip_range` 0,1, `batch_size` 128, douceur 0,1 et 600 000 pas.
- **Des propositions de code commun à soumettre à l'équipe**, chacune en PR séparée :
  - une adhérence sous la pluie de 0,7 à 1,0 au lieu de 0,5, demandée par la pédagogie (`FRICTION_PLUIE` dans `features.py`) ; tous les pilotes devront être réentraînés ;
  - la correction du bug d'export dans `exporter.py` ;
  - une pénalité d'immobilité ;
  - un LiDAR à 360° et une mémoire (plusieurs images LiDAR empilées) ;
  - l'écriture des notes en UTF-8 dans `garder.py` ;
  - `CONFIG=` dans `make train`, et l'intégration de `courses_detail.py` dans `training/`.

---

## Reproduire

```
make train DRIVER=driver2                                  # entraîner (même niveau, pas le même modèle)
rm submission/driver2/model.onnx.data                      # sinon l'export s'ajoute à l'ancien fichier
make export RUN=driver2-20261121-214154-ppo DRIVER=driver2  # livrer un run
make verify DRIVER=driver2                                 # vérifier la livraison
make evaluer RUN="<run1> <run2>"                           # comparer sur 12 courses
```
