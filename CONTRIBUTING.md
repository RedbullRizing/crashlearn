# Contribuer

## Démarrage

### 1. Le simulateur

`simulation/` **n'est pas versionné** : 163 fichiers pour 12 Mo qui ne nous appartiennent pas et qu'on ne modifie jamais. Télécharge l'archive sur l'intranet Epitech et décompresse-la à la racine du dépôt, dans un dossier nommé `simulation/`.

Vérifie ensuite que tu as la même version que le reste de l'équipe :

```bash
make sim-hash      # doit afficher : 85e85fbe139c5a05
```

Si l'empreinte diffère, tu n'as pas la même version et vos résultats ne seront pas comparables. C'est déjà arrivé : une première archive avait une API des adversaires différente.

### 2. L'image Docker

Tout passe par le conteneur : il épingle la chaîne ONNX (`onnx 1.22`, `onnxruntime 1.29`, `torch 2.13+cpu`) avec laquelle le tournoi chargera nos modèles, et le couple `numpy 2.4.6` / `numba 0.65.1` sans lequel la simulation ne démarre pas. Un modèle exporté hors de cette image risque le *Unsupported model IR version* le jour J.

Notre image (`crashlearn-sim:train`) ajoute à celle d'Epitech la pile d'entraînement, `gymnasium 1.4.0` et `stable-baselines3 2.9.2`, sans toucher aux versions ci-dessus. Pour en ajouter une : une ligne épinglée dans `docker-compose.yml`, puis `make build`.

Les commandes passent par le `Makefile` à la racine. `make` seul liste tout.

```bash
make build          # construit l'image, ~10 min la première fois
make check          # vérifie que le simulateur tourne
make test           # les tests fournis par Epitech
```

### 3. Au quotidien

Voir une course — on enregistre, puis on rejoue : le simulateur est headless, il n'y a pas de fenêtre live.

```bash
make record NAME=essai CTRL=pure_pursuit                 # circuit example
make record NAME=spa   CTRL=pure_pursuit CIRCUIT=Spa GRAINE=7
make record NAME=d2    CTRL=submission DRIVER=driver2    # un pilote précis
make venv           # une fois, installe de quoi afficher
make replay NAME=essai     # fenêtre interactive
make video  NAME=essai     # ou export MP4
```

`CTRL=submission` charge `submission/$(DRIVER)` et ne marche qu'avec `CARS=1` : un dossier pilote seul n'est pas recopié sur plusieurs voitures. `pure_pursuit` est la référence d'Epitech : il lit la pose exacte et la ligne centrale, à 2 m/s fixes — un repère, pas un pilote livrable.

Entraîner et suivre les courbes sur <http://localhost:6006> :

```bash
make courses DRIVER=driver1 CIRCUIT=Spa EPISODES=5   # banc d'évaluation, écrit dans runs/
make train DRIVER=driver1                            # dès que training/train.py existe (CRA-71)
make board
```

### 4. Suivre et garder ses runs

Chaque run (`make courses`, puis `make train`) crée son dossier dans `runs/` : les courbes TensorBoard, `meta.json` (graine, commit, configuration, versions) et `bilan.json` (chiffres finaux).

`runs/` est un **brouillon local** : hors dépôt, propre à chaque machine, perdu au prochain nettoyage. Les runs à conserver — ceux qui montrent l'évolution d'un pilote, pour le rapport et la soutenance — passent dans `archives/`, **versionné** :

```bash
make runs                                             # repérer le run
make garder RUN=driver2-20261115-143012-ppo NOTE="première reward qui boucle un tour"
git add archives/driver2-20261115-143012-ppo && git commit -m "chore(archives): …"
```

`make garder` ne copie que le léger — courbes, `meta.json`, `bilan.json`, configuration — plus un `note.md` avec la note donnée. Les modèles restent dans `runs/` : un modèle livré va dans `submission/`. Il prévient si le run a été lancé avec du code non commité : un tel run n'est pas reproductible, mieux vaut ne pas l'archiver.

```bash
make board          # TensorBoard sur http://localhost:6006, une fois pour toutes
make runs           # tableau des bilans, archives et brouillon
make runs DRIVER=driver2
make board-stop
```

- TensorBoard lit les deux dossiers : les runs apparaissent préfixés `archives/` ou `local/`. Taper `archives/` dans le filtre des runs, en haut à gauche, ne montre que les runs gardés — c'est la vue à présenter. Taper `driver2` isole un pilote.
- Après un `git pull`, les runs archivés par les autres membres apparaissent dans TensorBoard, sans rien faire.
- TensorBoard tourne dans le conteneur, rien à installer. Il relit ses dossiers en continu, et redémarre avec Docker jusqu'à `make board-stop` ou `make clean`.
- Sous Linux, les fichiers écrits par le conteneur appartiennent à root : `sudo chown -R $USER runs/` pour pouvoir les supprimer.
- Port 6006 déjà pris : `make board-stop`, ou arrêter l'autre TensorBoard.

### 5. Vérifier une soumission

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
simulation/    fourni par Epitech, non versionné, jamais modifié
runs/ recordings/          artefacts, hors suivi de version
archives/      runs gardés avec make garder, versionnés
```

`docker-compose.yml` est à nous. Le simulateur est construit dans l'image (son Dockerfile fait `COPY . /app`) et n'est pas monté depuis le disque : seuls nos dossiers le sont. On ne touche à aucun fichier d'Epitech, donc une nouvelle archive se remplace sans conflit.

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

Modèles, enregistrements et journaux sont hors suivi de version. Pour les retrouver, une seule convention : `runs/<pilote>-<AAAAMMJJ>-<HHMMSS>-<algo>/`, par exemple `runs/driver1-20261115-143012-ppo/`. Le dossier est créé par `training/runs.py`, avec un `meta.json` (graine, commit, config) et un `bilan.json`.

Deux exceptions :

- `submission/<pilote>/model.onnx` et son `.onnx.data`, parce que c'est un livrable ;
- `archives/`, les runs gardés avec `make garder` — courbes et bilans, jamais de modèle.
