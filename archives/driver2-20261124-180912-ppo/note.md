# driver2-20261124-180912-ppo

Réentraînement de contrôle de B (driver2-20261123-194118-ppo, archivé sur CRA-106) avec make train DRIVER=driver2 et driver2.yaml au commit f607576 : poids identiques à B (13 tenseurs, modèle final, sauvegardes 400k et 500k). Pilote driver2 livré le 24/11. Chiffres de B par runs/courses_detail.py, sous l'adhérence 0,7 : 44, 44, 45 et 46/46 avec les graines de course 20000 à 50000 (moyenne 44,75) ; sous l'adhérence 0,5 : 43/46 (graine 30000 : 44/46) ; tours 47,0 / 67,8 / 62,4 s ; 0,33 choc par course. Le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix.

Archivé le 2026-11-24 19:42, commit du run : f607576.
