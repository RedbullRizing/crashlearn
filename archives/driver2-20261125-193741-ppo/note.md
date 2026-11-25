# driver2-20261125-193741-ppo

Réentraînement de contrôle de driver2-20261124-233935-ppo (série 5, CRA-107) avec make train DRIVER=driver2 et driver2.yaml au commit 2f77ee6 : 13/13 tenseurs identiques pour le modèle final et les sauvegardes 600k et 700k (torch.equal sur policy.pth). Pilote driver2 livré le 25/11. Chiffres sous l'adhérence 0,7 tirés de local/serie5/resultats.md (runs/courses_detail.py, 4 graines de course 20000 à 50000) : 44, 45, 45 et 44/46, moyenne 44,50 ; temps moyen 190,1 s sur 17 circuits (211,3 s pour le pilote précédent) ; 2,94 chocs par course, dont presque tous dans 4 abandons par stagnation sous la pluie à Montréal et Monza. make verify : VALID. Course sim_recorder.py --submission à Oschersleben au sec : arrivée en 3 tours, 128,2 s, 0 choc. Le bilan.json est l'évaluation de fin d'entraînement (6 courses), qui ne sert pas au choix.

Archivé le 2026-11-25 20:59, commit du run : 2f77ee6.
