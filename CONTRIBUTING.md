# Contribuer

## Démarrage

Tout passe par le conteneur : il épingle la chaîne ONNX (`onnx 1.22`, `onnxruntime 1.29`, `torch 2.13+cpu`) avec laquelle le tournoi chargera nos modèles, et le couple `numpy 2.4.6` / `numba 0.65.1` sans lequel la simulation ne démarre pas. Un modèle exporté hors de cette image risque le *Unsupported model IR version* le jour J.

Les commandes passent par le `Makefile` à la racine. `make` seul liste tout.

```bash
make build          # construit l'image, ~10 min la première fois
make check          # vérifie que le simulateur tourne
make test           # les tests fournis par Epitech
```

Voir une course — on enregistre, puis on rejoue : le simulateur est headless, il n'y a pas de fenêtre live.

```bash
make record NAME=essai CARS=1 CTRL=pure_pursuit
make venv           # une fois, installe de quoi afficher
make replay NAME=essai     # fenêtre interactive
make video  NAME=essai     # ou export MP4
```

Entraîner et suivre les courbes sur <http://localhost:6006> :

```bash
make train DRIVER=driver1
make board
```

Vérifier une soumission — c'est le filtre exact de l'évaluation, à lancer tôt et souvent :

```bash
make verify DRIVER=driver1   # un pilote seul
make verify-gp               # la livraison complète
```

**Windows** : `make` n'existe pas dans `cmd.exe`. Lancez ces commandes depuis WSL2 ou Git Bash — le Makefile détecte la plateforme et adapte le chemin de l'environnement Python et le backend d'affichage.

## Arborescence

```
training/      env.py, features.py, train.py — dépend de gymnasium et sb3
submission/    livré au tournoi : driver1..4 et champion, rien d'autre
simulation/    fourni par Epitech, non modifié
logs/ runs/ recordings/   artefacts, hors suivi de version
```

Docker crée dans `simulation/` cinq dossiers vides — `training/`, `submission/`, `logs/`, `runs/`, `recordings/`. Ce ne sont pas des doublons : `/app` est un montage de `simulation/`, donc monter `../training` sur `/app/training` oblige Docker à créer le point de montage sur le disque. Ils restent vides. **Si un fichier y apparaît, c'est qu'une commande a tourné sans l'override** — vos fichiers sont au mauvais endroit. `make clean` les supprime.

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
