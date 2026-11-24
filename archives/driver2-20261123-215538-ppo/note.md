# driver2-20261123-215538-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : clip01 (essais/driver2-s2-clip01.yaml : livrée + clip_range 0.1), graine 1. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 300k : adhérence 0,7 7/12 (17 circuits non mesurés), adhérence 0,5 7/12 (17 circuits non mesurés), tours sous 0,7 71,5 / 105,5 / 94,5 s ; final : adhérence 0,7 10/12, 24/46, adhérence 0,5 11/12, 25/46, tours sous 0,7 64,5 / 94,7 / 85,5 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
