# driver2-20261125-011225-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : temps02 (essais/driver2-s5-temps02.yaml : nsteps512 + cout_temps 0,02), graine 5. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 3/12 (17 circuits non mesurés), adhérence 0,5 2/12 (17 circuits non mesurés), tours sous 0,7 70,0 / 103,1 / – s ; 500k : adhérence 0,7 11/12, 29/46, adhérence 0,5 11/12, 28/46, tours sous 0,7 60,0 / 88,5 / 79,9 s ; final : adhérence 0,7 9/12 (17 circuits non mesurés), adhérence 0,5 8/12 (17 circuits non mesurés), tours sous 0,7 52,2 / 77,0 / 69,5 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
