# driver2-20261123-214319-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : livrée (training/configs/driver2.yaml), graine 1. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 300k : adhérence 0,7 12/12, 39/46, adhérence 0,5 12/12, 37/46, tours sous 0,7 48,5 / 69,2 / 64,9 s ; final : adhérence 0,7 10/12 (17 circuits non mesurés), adhérence 0,5 10/12 (17 circuits non mesurés), tours sous 0,7 41,6 / 59,3 / 55,1 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
