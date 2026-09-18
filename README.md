# Crash & Learn

Apprentissage par renforcement sur simulateur de course — Bastien Cochet ([@bstcoc](https://github.com/bstcoc)), Mathias Arnaud ([@Frataque](https://github.com/Frataque)), Julien Lefebvre ([@Juliendev200](https://github.com/Juliendev200)) et Frank Lagarrue ([@Knarfyy](https://github.com/Knarfyy)).

Rendu : **7 février 2027 à 23:42 (Europe/Paris)**.

## Le projet

Entraîner des agents de conduite sur un simulateur dérivé de `f1tenth_gym`, jusqu'à la victoire au Grand Prix Epitech. Le sujet se déroule en quatre parties :

| Partie | Objectif | Livrable |
| --- | --- | --- |
| 1 — Permis solo | Quatre pilotes bouclent le circuit seuls, sous météo et bruit variables | `driver1/` à `driver4/`, formalisme MDP et justification de l'algorithme |
| 2 — Grand Crash Auto | Les quatre solos courent ensemble et s'entre-percutent | Aucun code : le diagnostic de l'échec |
| 3 — Multi-agent | Une politique qui détecte, évite et dépasse les adversaires | `champion/` et le rapport final |
| 4 — Grand Prix | Qualifications régionales puis tournoi national | Après la date de rendu |

**La contrainte qui structure tout le dépôt** : le code d'entraînement et le code de course vivent dans deux mondes séparés. `env.py` (wrapper Gymnasium) et `train.py` dépendent de Gymnasium et Stable-Baselines3 ; `agent.py` est le **seul fichier chargé le jour du tournoi** et ne peut importer que `onnxruntime`, `numpy` et `os` — tous les agents de toutes les équipes tournent dans un même processus, sans isolation.

Conséquence directe : le prétraitement existe en double, dans `env.py` et dans `agent.py`. S'ils divergent, l'agent se comporte différemment au tournoi de ce que montrent les courbes d'entraînement — **silencieusement, sans erreur**. La parade retenue est un `features.py` purement numpy, importé des deux côtés.

Stack : PPO via Stable-Baselines3, export ONNX en opset ≤ 17, entraînement CPU accepté.

## Documentation et suivi

Le [projet Linear Crash & Learn](https://linear.app/crash-and-learn/project/crash-and-learn-47dda639be2b) centralise tickets, jalons, décisions et documents. **C'est la source de vérité** : ce dépôt accueille le code, pas le cadrage.

- [Cahier des charges et organisation](https://linear.app/crash-and-learn/document/cahier-des-charges-et-organisation-9aab6b9e1cd5)
- [API du simulateur — référence et pièges](https://linear.app/crash-and-learn/document/api-du-simulateur-reference-et-pieges-25e8206e25e6)
- [Contrat de soumission et export ONNX](https://linear.app/crash-and-learn/document/contrat-de-soumission-et-export-onnx-a54c16368b2b)
- [Formalisme MDP et fonction de récompense](https://linear.app/crash-and-learn/document/formalisme-mdp-et-fonction-de-recompense-064f260d7d33)
- [Protocole d'entraînement et d'évaluation](https://linear.app/crash-and-learn/document/protocole-dentrainement-et-devaluation-92dc9fca8aa7)
- [Robustesse — météo, bruit et généralisation](https://linear.app/crash-and-learn/document/robustesse-meteo-bruit-et-generalisation-e47ef1c7c5d0)
- [Stratégie multi-agent et course](https://linear.app/crash-and-learn/document/strategie-multi-agent-et-course-a44be83c06e2)

### Jalons

| Jalon | Échéance | Contenu |
| --- | --- | --- |
| M1 — Socle et maîtrise du simulateur | 19/10/2026 | Le simulateur tourne chez tout le monde, son API est documentée, l'outillage d'entraînement est en place |
| M2 — Permis de conduire solo | 07/12/2026 | Partie 1 : quatre pilotes livrés, `verify_submission.py` passe, formalisme MDP écrit |
| M3 — Grand Crash Auto | 21/12/2026 | Partie 2 : modes d'échec mesurés et diagnostic rédigé |
| M4 — Champion multi-agent | 25/01/2027 | Partie 3 : tournoi interne et désignation du champion |
| M5 — Rendu et Grand Prix | 07/02/2027 | Rendu complet, rapport final, soutenance |

Le backlog est un graphe : 56 issues reliées par 109 dépendances `blocks`. Trois tickets seulement n'ont aucun bloqueur et constituent les points d'entrée — `CRA-5` (faire tourner le simulateur), `CRA-9` (initialiser le dépôt) et `CRA-12` (rendre les entraînements reproductibles).

## Développement

Dépôt principal : [RedbullRizing/crashlearn](https://github.com/RedbullRizing/crashlearn) (`origin`). Le remote `epitech` pointe sur `EpitechMscProPromo2027/T-AIA-901-LYN-9-1-crashlearn-11` et est réservé à la remise.

Backlog partagé, tâches prises librement, petites PR ; aucun domaine réservé. Chaque membre porte son propre pilote solo en Partie 1 ; la Partie 3 est un effort commun dont sort un seul champion.

### Branches et commits

Une branche par issue, avec le nom **généré par Linear** (`Cmd/Ctrl + Shift + .` sur l'issue) :

```
bastiencochet/cra-9-initialiser-le-depot-et-la-structure-du-projet
```

Le lien Linear ↔ GitHub s'appuie sur des mots-clés dans le titre ou la description de la PR, ou dans un message de commit :

| Effet | Mots-clés |
| --- | --- |
| Ferme l'issue au merge | `close`, `closes`, `fix`, `fixes`, `resolve`, `resolves`, `complete`, `completes`, `implement`, `implements` |
| Lie sans fermer | `ref`, `refs`, `references`, `part of`, `contributes to`, `towards` |
| Simple relation | `relates to`, `related to` |
| Empêche le lien automatique | `skip CRA-9`, `ignore CRA-9` |

Exemple : `Closes CRA-9`. Une branche poussée passe l'issue **In Progress**, une PR mergée la passe **Done** — ce qui débloque mécaniquement les issues qu'elle bloquait.

Références : [magic words](https://linear.app/docs/github#magic-words) et [format de branche](https://linear.app/docs/github#branch-name).

### État

Le socle n'est pas encore initialisé — voir [`CRA-9`](https://linear.app/crash-and-learn/issue/CRA-9). L'arborescence, le `.gitignore` et les commandes de développement (construction de l'image Docker, lancement d'un entraînement, vérification d'une soumission) seront ajoutés avec.
