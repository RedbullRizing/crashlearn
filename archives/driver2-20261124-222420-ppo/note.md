# driver2-20261124-222420-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : nsteps512 (essais/driver2-s4-nsteps512.yaml : config de driver2-20261123-194118-ppo, n_steps 512, 600k pas, nouvelles graines), graine 6. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 12/12, 30/46, adhérence 0,5 12/12, 32/46, tours sous 0,7 60,5 / 87,2 / 77,9 s ; 500k : adhérence 0,7 11/12, 28/46, adhérence 0,5 12/12, 31/46, tours sous 0,7 61,2 / 88,2 / 77,7 s ; final : adhérence 0,7 11/12, 35/46, adhérence 0,5 8/12, 33/46, tours sous 0,7 48,8 / 70,9 / 63,0 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
