# driver2-20261123-230119-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : nsteps512 (essais/driver2-s4-nsteps512.yaml : livrée + n_steps 512, 600k pas), graine 5. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 400k : adhérence 0,7 11/12, 37/46, adhérence 0,5 10/12, 34/46, tours sous 0,7 52,9 / 75,8 / 69,3 s ; 500k : adhérence 0,7 11/12, 35/46, adhérence 0,5 11/12, 32/46, tours sous 0,7 44,1 / 64,0 / 57,8 s ; final : adhérence 0,7 10/12, 32/46, adhérence 0,5 12/12, 34/46, tours sous 0,7 40,1 / 57,8 / 52,4 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
