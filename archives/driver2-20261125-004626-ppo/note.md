# driver2-20261125-004626-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : temps015 (essais/driver2-s5-temps015.yaml : nsteps512 + cout_temps 0,015), graine 42. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 12/12, 42/46 (graine 30000 : 41/46), adhérence 0,5 10/12, 37/46, tours sous 0,7 43,6 / 64,6 / 62,0 s ; 500k : adhérence 0,7 12/12, 39/46, adhérence 0,5 11/12, 37/46, tours sous 0,7 44,1 / 61,5 / 61,0 s ; final : adhérence 0,7 12/12, 41/46, adhérence 0,5 12/12, 43/46 (graine 30000 : 39/46), tours sous 0,7 44,0 / 61,6 / 59,4 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
