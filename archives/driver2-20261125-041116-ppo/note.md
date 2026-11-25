# driver2-20261125-041116-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : nsteps1024 (essais/driver2-s5-nsteps1024.yaml : nsteps512 + n_steps 1024, 800k pas), graine 5. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 600k : adhérence 0,7 12/12, 31/46, adhérence 0,5 12/12, 31/46, tours sous 0,7 63,4 / 91,0 / 82,0 s ; 700k : adhérence 0,7 12/12, 42/46 (graine 30000 : 43/46), adhérence 0,5 11/12, 42/46 (graine 30000 : 43/46), tours sous 0,7 53,2 / 76,9 / 69,2 s ; final : adhérence 0,7 11/12, 40/46, adhérence 0,5 12/12, 40/46, tours sous 0,7 51,0 / 74,5 / 66,9 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
