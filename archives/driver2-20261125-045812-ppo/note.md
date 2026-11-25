# driver2-20261125-045812-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : nsteps512 (essais/driver2-s4-nsteps512.yaml : config de driver2-20261123-194118-ppo, n_steps 512, 600k pas, nouvelles graines), graine 11. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 10/12 (17 circuits non mesurés), adhérence 0,5 8/12 (17 circuits non mesurés), tours sous 0,7 56,4 / 81,0 / 74,8 s ; 500k : adhérence 0,7 12/12, 40/46, adhérence 0,5 11/12, 39/46, tours sous 0,7 51,4 / 74,2 / 68,2 s ; final : adhérence 0,7 9/12, 30/46, adhérence 0,5 11/12, 32/46, tours sous 0,7 45,9 / 65,7 / 60,2 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
