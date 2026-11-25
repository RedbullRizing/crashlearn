# driver2-20261121-214154-ppo

LIVRÉ. Pilote driver2 livré (commit a9ac8af). Config : training/configs/driver2.yaml, soit E3 + n_epochs 20, graine 2, 400k pas (lancé avec essais/driver2-epochs20.yaml --graine 2 --pas 400000). Réentraînement du meilleur modèle de la série (driver2-20261121-185118-ppo à 400k : 45/46), non identique bit à bit. Validation 12/12 (sec 6/6, pluie 6/6), tours 46,1 / 65,9 / 59,4 s, 0,2 choc/course. Graine de course 20000 : 17 circuits 31/34 (sec 16, pluie 15), total 43/46, temps moyen 203,3 s. Graine 30000 : 29/34 (sec 16, pluie 13), total 41/46, temps moyen 204,6 s. Référence E3 : 39/46 et 37/46, temps moyen 200,2 et 199,9 s.

Archivé le 2026-11-22 01:04, commit du run : 9f9f174.
