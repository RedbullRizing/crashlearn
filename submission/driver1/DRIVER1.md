# driver1

Pilote de Bastien, entraîné seul sur la piste par apprentissage par renforcement.

| | |
|---|---|
| **Modèle livré** | run `driver1-20261113-131306-ppo`, livré le 13/11 |
| **Algorithme** | PPO (Stable-Baselines3) |
| **Entraînement** | 500 000 décisions, 8 courses en parallèle, 8 min |
| **Résultat** | **10 courses finies sur 12** sur des circuits jamais vus (sec 5/6, pluie 5/6) |
| **Meilleur tour** | **34,9 s** (Oschersleben) |
| **Vérification** | `make verify DRIVER=driver1` : VALID |

---

## 1. Comment il apprend

**PPO** : le pilote essaie, reçoit une note à chaque décision, et ajuste petit à petit sa conduite pour avoir de meilleures notes. Il n'imite personne.

- **Pourquoi PPO.** La vitesse et le braquage sont continus, ce qui écarte DQN. PPO est stable : une correction ne peut pas trop changer le pilote d'un coup. Il est aussi simple à faire tourner sur 8 simulateurs en parallèle.
- **Le réseau de neurones.** Deux réseaux de 2 × 64 neurones, soit environ 13 500 paramètres. Le premier conduit, c'est lui qui est livré dans `model.onnx`. Le second juge si la situation est bonne et ne sert qu'à l'entraînement. Cette taille est la valeur par défaut, elle n'a pas été comparée à d'autres.

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
| Choc contre un mur | −2 | éviter les murs |
| Contact avec une voiture | −1 | ne pas percuter |
| Abandon | −10 | ne jamais rester bloqué |

Une course d'entraînement s'arrête au premier choc contre un mur, sur un abandon, ou après 150 s.

---

## 2. Réglages

Fichier `training/configs/driver1.yaml`.

| Réglage | Valeur | En clair |
|---|---|---|
| `pas` | 500 000 | décisions jouées au total |
| `envs` | 8 | courses en parallèle |
| `n_steps` | 256 | décisions par course avant chaque correction (2 048 au total) |
| `batch_size` | 64 | taille des paquets étudiés d'un coup |
| `learning_rate` | 0,0003 | taille de chaque correction |
| `gamma` | 0,99 | il anticipe environ 5 s devant lui |
| `graine` | 1 | départ du hasard, pour rejouer à l'identique |
| `fin_sur_choc` | oui | un choc contre un mur termine la course |
| `meteo` | oui | pluie aléatoire pendant l'entraînement |
| `adversaires` | aucun | entraîné seul sur la piste |

---

## 3. Circuits

| Groupe | Circuits | Rôle |
|---|---|---|
| **Entraînement (17)** | Austin, BrandsHatch, Catalunya, Hockenheim, IMS, Melbourne, Montreal, Monza, MoscowRaceway, Nuerburgring, Sakhir, SaoPaulo, Sepang, Shanghai, Silverstone, Spielberg, YasMarina | il apprend dessus |
| **Validation (3)** | Oschersleben, Zandvoort, MexicoCity | jamais vus à l'entraînement ; on mesure et on choisit dessus |
| **Test (3)** | Spa, Budapest, Sochi | jamais utilisés, gardés pour la mesure finale |

Montreal, le plus étroit (1,39 m), est volontairement dans l'entraînement : sinon le pilote ne verrait aucune piste de moins de 2 m.

---

## 4. Météo

Le simulateur d'Epitech reste toujours au sec. La pluie est ajoutée par `training/env.py`.

- Toutes les 20 s, un nouveau temps est tiré : **sec 30 % du temps**, sinon une pluie d'intensité variable, le plus souvent légère.
- **La piste glisse** : l'adhérence des pneus passe de 1,0 au sec à 0,5 sous forte pluie. Elle est appliquée au vrai moteur physique.
- **Le capteur se trompe** : ±0,1 % au sec, jusqu'à ±10 % sous forte pluie, et jusqu'à 5 % des rayons décrochent.
- **Le pilote lit la pluie** dans ses entrées, il n'a pas à la deviner.

---

## 5. Progrès pendant l'entraînement du modèle livré

| Avancement | Tient avant un mur | Note moyenne | Hésitation |
|---|---|---|---|
| début | 1,8 s | −0,3 | 0,99 |
| 25 % | 16 s | 82 | 0,62 |
| 50 % | 11,5 s | 73 | 0,50 |
| 75 % | 20,6 s | 140 | 0,40 |
| fin | **30,5 s** | **204** | **0,34** |

« Hésitation » est la part de hasard dans ses commandes : plus elle baisse, plus ses gestes sont sûrs.

---

## 6. Entraînements, l'un après l'autre

Le bilan de fin d'entraînement porte sur **6 courses complètes** sur les circuits de validation : une au sec et une avec la météo, par circuit.

| Date | Run | Ce qui change | Fini | Chocs / course | Meilleur tour |
|---|---|---|---|---|---|
| 21/09 | `naif` | pilote écrit à la main, sans apprentissage, sur `example` | 0 % | 152 | — |
| 25/09 | `naif` | idem, autre graine | 0 % | 138 | — |
| 13/11 | `102502` | premier essai MDP v2 : 1,5M pas, 2 envs | pas de bilan | — | — |
| 13/11 | **`131306`** | **500k pas, 8 envs, graine 1 : modèle livré** | **3/6** | **0,8** | **35,6 s** |
| 13/11 | `135614` | idem mais 1M pas | 3/6 | 6,8 | 33,1 s |
| 13/11 | `152630` | reprise du livré, +300k pas, **sans arrêt au choc** | 1/6 | 26,5 | 44,1 s |
| 13/11 | `153059` | reprise, sans arrêt au choc, choc −5, temps −0,02 | 3/6 | 29,0 | 34,9 s |
| 13/11 | `155512` | reprise, temps −0,02 | 3/6 | 16,5 | 35,1 s |
| 13/11 | `160019` | reprise, temps −0,03 | **5/6** | **0,7** | **31,9 s** |
| 13/11 | `172402` | 500k pas, graine 2 | 3/6 | 82,2 | 32,7 s |
| 13/11 | `173411` | 500k pas, graine 3 | **5/6** | **0,5** | 32,8 s |
| 13/11 | `185640` | 500k pas, graine 4 | 3/6 | 37,3 | 34,8 s |

« Reprise » : l'entraînement repart du modèle livré au lieu de partir de zéro.

**Ce qu'on en retient**

- **Le hasard pèse lourd.** Avec les mêmes réglages et seulement une graine différente, on obtient 3/6 ou 5/6. Six courses ne suffisent pas pour juger un pilote. D'où `make evaluer`, qui compare des runs sur 12 courses identiques.
- **Plus long n'est pas mieux.** 1M de pas ne fait pas mieux que 500k.
- **Ne plus arrêter la course au choc empire les choses**, même avec la marche arrière : 1/6 et 3/6, avec 26 à 29 chocs par course.
- **Faire coûter le temps plus cher aide** : avec −0,03 au lieu de −0,01, `160019` fait 5/6 avec moins d'un choc par course.

### Mesure sur 12 courses (`make evaluer`)

| Run | Fini | Sec | Pluie | Chocs / course | Oschersleben | Zandvoort | MexicoCity |
|---|---|---|---|---|---|---|---|
| `131306` (livré) | **10/12** | 5/6 | 5/6 | 6,2 | 34,9 s | 50,0 s | 46,5 s |

`160019` et `173411` n'ont pas encore été mesurés sur 12 courses.

---

## 7. Ce sur quoi il a du mal

1. **Forte pluie.** Sur MexicoCity (graine 7), il fait 2 tours en 94,5 s au sec, mais abandonne après 14 s sous forte pluie continue. Il freine à la distance qu'il faudrait au sec et finit dans le mur.
2. **Se dégager d'un mur.** Collé au mur, il alterne marche avant et marche arrière sans avancer, et le simulateur l'élimine : moins de 1 m gagné en 10 s. À l'entraînement, le premier choc arrête la course, donc il n'a jamais appris à repartir. Le laisser continuer après un choc n'a pas marché pour l'instant (`152630`, `153059`).
3. **Les chocs.** Il touche un mur environ 6 fois par course sur les 12 courses de mesure.
4. **Les résultats varient d'un entraînement à l'autre** : de 3/6 à 5/6 selon la graine.

Les courses enregistrées se revoient dans le visualiseur 3D (`make visualiseur`) : `driver1_sec_mexico`, `driver1_meteo_mexico` et `driver1_pluie_mexico`.

---

## 8. Prochaines étapes

- Mesurer `160019` et `173411` sur 12 courses, et remplacer le modèle livré s'ils font mieux :
  `make evaluer RUN="driver1-20261113-131306-ppo driver1-20261113-160019-ppo driver1-20261113-173411-ppo"`
- Entraîner de zéro avec un temps plus coûteux (`cout_temps: 0.03`).
- Comparer la taille du réseau (2 × 32, 2 × 64, 2 × 128).
- Mesurer l'écart entre circuits d'entraînement et circuits de validation, pour vérifier qu'il n'a pas appris les circuits par cœur.

---

## Reproduire

```
make train DRIVER=driver1                                 # entraîner
make export RUN=driver1-20261113-131306-ppo DRIVER=driver1 # livrer un run
make verify DRIVER=driver1                                # vérifier la livraison
make evaluer RUN="<run1> <run2>"                          # comparer sur 12 courses
```
