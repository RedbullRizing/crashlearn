# driver2-20261124-201829-ppo

Série 5 driver2, vitesse sans perdre d'arrivées (CRA-107), commit a0c6541. Config : nsteps1024 (essais/driver2-s5-nsteps1024.yaml : nsteps512 + n_steps 1024, 800k pas), graine 2. Chiffres : training/configs/essais/RESULTATS-s5.md (série 5, même branche), mesurés par runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 600k : adhérence 0,7 8/12 (17 circuits non mesurés), adhérence 0,5 8/12 (17 circuits non mesurés), tours sous 0,7 73,9 / 106,5 / 94,9 s ; 700k : adhérence 0,7 12/12, 24/46, adhérence 0,5 12/12, 23/46, tours sous 0,7 63,9 / 91,7 / 84,2 s ; final : adhérence 0,7 12/12, 31/46, adhérence 0,5 11/12, 29/46, tours sous 0,7 60,6 / 86,7 / 79,8 s.

Archivé le 2026-11-25 21:30, commit du run : a0c6541.
