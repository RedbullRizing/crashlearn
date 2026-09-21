# Crash & Learn

Apprentissage par renforcement sur simulateur de course — Bastien Cochet, Mathias Arnaud, Julien Lefebvre et Frank Lagarrue.

Rendu : **7 février 2027 à 23:42 (Europe/Paris)**.

## Documentation et suivi

Le [projet Linear Crash & Learn](https://linear.app/crash-and-learn/project/crash-and-learn-47dda639be2b) centralise tickets, jalons, décisions et documents. Le PDF original du sujet est dans ses ressources.

- [Guide de l'équipe — comment le projet fonctionne](https://linear.app/crash-and-learn/document/guide-de-lequipe-comment-le-projet-fonctionne-f119272e8e55)
- [Cahier des charges et organisation](https://linear.app/crash-and-learn/document/cahier-des-charges-et-organisation-9aab6b9e1cd5)
- [API du simulateur — référence et pièges](https://linear.app/crash-and-learn/document/api-du-simulateur-reference-et-pieges-25e8206e25e6)
- [Contrat de soumission et export ONNX](https://linear.app/crash-and-learn/document/contrat-de-soumission-et-export-onnx-a54c16368b2b)
- [Formalisme MDP et fonction de récompense](https://linear.app/crash-and-learn/document/formalisme-mdp-et-fonction-de-recompense-064f260d7d33)
- [Protocole d'entraînement et d'évaluation](https://linear.app/crash-and-learn/document/protocole-dentrainement-et-devaluation-92dc9fca8aa7)
- [Robustesse — météo, bruit et généralisation](https://linear.app/crash-and-learn/document/robustesse-meteo-bruit-et-generalisation-e47ef1c7c5d0)
- [Stratégie multi-agent et course](https://linear.app/crash-and-learn/document/strategie-multi-agent-et-course-a44be83c06e2)

## Développement

Dépôt principal : [RedbullRizing/crashlearn](https://github.com/RedbullRizing/crashlearn) (`origin`). Le remote `epitech` est réservé à la remise finale.

Une branche par issue, avec le [nom généré par Linear](https://linear.app/docs/github#branch-name) ; le lien avec le ticket passe par les [magic words](https://linear.app/docs/github#magic-words) dans la PR ou le message de commit. Backlog partagé, tâches prises librement et petites PR ; aucun domaine réservé.

Le simulateur d'Epitech n'est pas versionné : télécharge l'archive et décompresse-la en `simulation/`, puis `make sim-hash` pour vérifier que tu as la même version que l'équipe. Toutes les commandes passent par le `Makefile` — voir [`CONTRIBUTING.md`](CONTRIBUTING.md).

Le code d'entraînement n'existe pas encore. Le cadrage est maintenu dans Linear ; ce dépôt accueille `training/` et le dossier `submission/` livré au tournoi.
