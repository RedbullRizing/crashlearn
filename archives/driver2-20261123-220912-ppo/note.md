# driver2-20261123-220912-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : nsteps512 (essais/driver2-s4-nsteps512.yaml : livrée + n_steps 512, 600k pas), graine 1. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 12/12, 40/46, adhérence 0,5 10/12, 36/46, tours sous 0,7 48,2 / 69,0 / 63,1 s ; 500k : adhérence 0,7 11/12, 38/46, adhérence 0,5 12/12, 39/46, tours sous 0,7 49,4 / 71,2 / 65,1 s ; final : adhérence 0,7 11/12, 40/46, adhérence 0,5 12/12, 45/46 (graine 30000 : 43/46), tours sous 0,7 47,9 / 68,9 / 62,6 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
