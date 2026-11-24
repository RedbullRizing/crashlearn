# driver2-20261123-223251-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : livrée (training/configs/driver2.yaml), graine 5. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 300k : adhérence 0,7 12/12, 41/46, adhérence 0,5 12/12, 40/46, tours sous 0,7 51,2 / 74,5 / 68,0 s ; final : adhérence 0,7 11/12, 34/46, adhérence 0,5 8/12, 27/46, tours sous 0,7 42,9 / 57,1 / 57,9 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
