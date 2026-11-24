# driver2-20261123-203402-ppo

Série 4 driver2, robustesse aux graines (CRA-106). Config : clip01 (essais/driver2-s2-clip01.yaml : livrée + clip_range 0.1), graine 21. Chiffres : runs/courses_detail.py, adhérence 0,7 et 0,5, graine de course 20000 (30000 si rejoué), total sur 46 = 12 courses de validation + 34 sur les 17 circuits ; le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix. 300k : adhérence 0,7 12/12, 37/46, adhérence 0,5 11/12, 36/46, tours sous 0,7 56,6 / 82,4 / 75,5 s ; final : adhérence 0,7 12/12, 32/46, adhérence 0,5 12/12, 29/46, tours sous 0,7 54,6 / 80,3 / 75,2 s.

Archivé le 2026-11-24 18:59, commit du run : f036318.
