# driver2-20261123-211012-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : clip01 (essais/driver2-s2-clip01.yaml : livrée + clip_range 0.1), graine 42. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 300k : adhérence 0,7 12/12, 23/46, adhérence 0,5 12/12, 25/46, tours sous 0,7 66,8 / 97,5 / 87,7 s ; final : adhérence 0,7 12/12, 39/46, adhérence 0,5 12/12, 39/46, tours sous 0,7 57,8 / 84,8 / 77,0 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
