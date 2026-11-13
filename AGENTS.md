# AGENTS.md

Crash & Learn : pilotes de course entraînés par renforcement (PPO, Gymnasium, stable-baselines3) sur le simulateur d'Epitech.

## Code

Le code se lit seul : noms précis et docstrings portent le sens. Un fichier Python sous `training/` contient zéro commentaire `#` ; une explication nécessaire devient un meilleur nom ou une ligne de docstring.

`submission/<pilote>/agent.py` et `features.py` sont des copies écrites par `make export` : modifier l'original dans `training/`.

`simulation/` appartient à Epitech et reste en lecture seule.

Un changement sous `training/` est terminé quand `make test` passe dans le conteneur.

## Pointeurs

- **Branche, commit, run, config pilote** : lire [`CONTRIBUTING.md`](CONTRIBUTING.md) avant d'agir.
- **Observation, action, récompense** : lire [`docs/partie1-mdp-et-algorithme.md`](docs/partie1-mdp-et-algorithme.md) ; ce contrat avec `agent.py` change seulement sur décision de l'équipe.
- **API du simulateur, export ONNX, protocole d'évaluation** : ouvrir le document Linear listé dans [`README.md`](README.md).
