# driver2-20261125-020610-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : nsteps512 (essais/driver2-s4-nsteps512.yaml : config de driver2-20261123-194118-ppo, n_steps 512, 600k pas, nouvelles graines), graine 8. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 10/12, 37/46, adhérence 0,5 12/12, 43/46 (graine 30000 : 43/46), tours sous 0,7 39,5 / 57,0 / 52,1 s ; 500k : adhérence 0,7 11/12, 41/46, adhérence 0,5 12/12, 43/46 (graine 30000 : 38/46), tours sous 0,7 37,4 / 54,5 / 49,8 s ; final : adhérence 0,7 11/12, 34/46, adhérence 0,5 11/12, 33/46, tours sous 0,7 37,1 / 54,2 / 49,4 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
