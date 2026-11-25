# driver2-20261124-194535-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : temps015 (essais/driver2-s5-temps015.yaml : nsteps512 + cout_temps 0,015), graine 2. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 4/12 (17 circuits non mesurés), adhérence 0,5 4/12 (17 circuits non mesurés), tours sous 0,7 88,1 / 125,3 / 110,8 s ; 500k : adhérence 0,7 10/12 (17 circuits non mesurés), adhérence 0,5 9/12 (17 circuits non mesurés), tours sous 0,7 68,4 / 99,2 / 88,6 s ; final : adhérence 0,7 12/12, 30/46, adhérence 0,5 12/12, 28/46, tours sous 0,7 60,9 / 87,8 / 78,5 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
