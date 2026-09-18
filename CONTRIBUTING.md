# Contribuer

## Démarrage

Tout passe par le conteneur : il épingle la chaîne ONNX (`onnx 1.22`, `onnxruntime 1.29`, `torch 2.13+cpu`) avec laquelle le tournoi chargera nos modèles, et le couple `numpy 2.4.6` / `numba 0.65.1` sans lequel la simulation ne démarre pas. Un modèle exporté hors de cette image risque le *Unsupported model IR version* le jour J.

```bash
cd simulation
docker compose build                 # ~10 min la première fois
docker compose run --rm sim          # démonstration, vérifie que tout tourne
```

Les tests fournis :

```bash
docker compose run --rm sim python test_contract.py
docker compose run --rm sim python test_integration.py
```

Entraîner, puis suivre les courbes sur <http://localhost:6006> :

```bash
docker compose run --rm sim python training/train.py
docker compose up -d tensorboard
```

Vérifier une soumission — c'est le filtre exact de l'évaluation, à lancer tôt et souvent :

```bash
docker compose run --rm sim python verify_submission.py --submission submission/
docker compose run --rm sim python verify_submission.py --submission submission/ --grandprix
```

Enregistrer une course et la rejouer :

```bash
docker compose run --rm recorder
docker compose run --rm replay python viz_replay.py --record /app/recordings/course.mp4 --no-telemetry
```

## Arborescence

```
training/      env.py, features.py, train.py — dépend de gymnasium et sb3
submission/    livré au tournoi : driver1..4 et champion, rien d'autre
simulation/    fourni par Epitech, non modifié
logs/ runs/ recordings/   artefacts, hors suivi de version
```

`simulation/docker-compose.override.yml` est le seul fichier que nous ajoutons dans `simulation/` : il monte `training/` et `submission/` dans le conteneur, que le compose fourni ne voit pas.

`agent.py` ne peut importer que `onnxruntime`, `numpy` et `os` : `features.py` est donc recopié dans chaque dossier pilote. C'est voulu, pas un oubli — voir le [contrat de soumission](https://linear.app/crash-and-learn/document/contrat-de-soumission-et-export-onnx-a54c16368b2b).

## Branches

Une branche par issue, avec le [nom généré par Linear](https://linear.app/docs/github#branch-name) (`Cmd/Ctrl + Shift + .` sur le ticket) :

```
bastiencochet/cra-9-initialiser-le-depot-et-la-structure-du-projet
```

## Commits

Format [Conventional Commits](https://www.conventionalcommits.org), description en français :

```
type(scope): description courte

Corps facultatif.

Part of CRA-9
```

Types : `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.
Scopes usuels : `env`, `train`, `features`, `agent`, `onnx`, `docker`, `submission`, `repo`.

Le pied de message relie le commit au ticket via les [magic words](https://linear.app/docs/github#magic-words) : `Closes CRA-9` ferme l'issue au merge, `Part of CRA-9` la relie sans la fermer. Une branche poussée passe le ticket en **In Progress**, une PR mergée avec `Closes` le passe en **Done** — ce qui débloque automatiquement les tickets qu'il bloquait.

N'utilisez `Closes` que lorsque **tous** les critères d'acceptation du ticket sont remplis.

## Artefacts

Modèles, enregistrements et journaux sont hors suivi de version. Pour les retrouver, une seule convention : `runs/<pilote>-<AAAAMMJJ>-<algo>/`, par exemple `runs/driver1-20261115-ppo/`.

Seule exception, parce que c'est un livrable : `submission/<pilote>/model.onnx` et son `.onnx.data` sont versionnés.
