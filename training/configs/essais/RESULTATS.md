# Campagne d'essais driver3 du 18/11/2026 (CRA-99)

Évaluation : `make evaluer`, 12 courses de validation (Oschersleben, Zandvoort, MexicoCity ; 4 par circuit, sec/pluie en alternance), déterministe, mêmes courses pour tous.
Les runs sont dans `runs/` (brouillon local, non versionné). Les sorties brutes sont dans `evaluations_brutes_*.txt` à côté de ce fichier.

## Variantes driver3 (changement par rapport à driver3.yaml), modèle final

| Variante | Pas | Courses finies /12 (g1, g2, g3) | Moy. | Chocs/course (moy.) | Tour Osche / Zandv (moy.) |
|---|---|---|---|---|---|
| référence driver3 | 300k | 4, 9, 3 | 5,3 | 81 | 36,7 / 49,0 |
| prudent (pénalité de choc 5) | 300k | 7, 7, 8 | 7,3 | 38 | 39,0 / 56,7 |
| cout02 (coût du temps 0,02) | 300k | 6, 8, 7 | 7,0 | 38 | 38,6 / 56,2 |
| lr1e4 (taux d'apprentissage 0,0001) | 600k | 6, 0, 0 | 2,0 | 68 | 42 / 62 (rares) |
| lots512 (n_steps 512, batch_size 128) | 500k | 7, 8, 10 | 8,3 | 44 | 35,7 / 51,8 |
| lots512, graines 4 à 6 | 500k | 9, 7, 5 | 7,0 | 62 | 36,3 / 52,4 |

lots512 sur 6 graines : 7,7 courses finies en moyenne, minimum 5.

## Runs (graine -> dossier dans `runs/`)

- prudent : g1 driver3-20261118-144100-ppo, g2 -144347, g3 -144743
- cout02 : g1 driver3-20261118-145146-ppo, g2 -145609, g3 -150007
- lr1e4 : g1 driver3-20261118-150413-ppo, g2 -151251, g3 -152237
- lots512 : g1 driver3-20261118-153216-ppo, g2 -153925, g3 -154351, g4 -160347, g5 -160943, g6 -161539
- modèle exporté dans `submission/driver3` : driver3-20261118-112519-ppo (référence, graine 2, 300k), 9/12, tours 34,4 / 48,9 / 45,8

## Lectures

- Les réglages de récompense déplacent le compromis vitesse / prudence (coût du temps élevé : rapide et risqué ; pénalité de choc élevée : propre et plus lent).
- Le taux d'apprentissage 0,0001 ne converge pas en 600k pas.
- Les lots plus gros (lots512) ne dégradent pas le modèle après 300k pas comme la configuration actuelle.
- Le bruit entre graines est grand (une même configuration va de 3 à 10 courses finies) : peu de conclusions fermes avec 3 graines.
- Les dossiers `runs/*-c200k`, `-c300k`, `-c400k`, `-c500k` sont des copies de checkpoints faites pour l'évaluation ; ils n'ont pas de meta.json.
