# Partie 1 — Formalisme MDP et choix de l'algorithme

Ce document répond aux deux attendus de la partie 1 : décrire le MDP (espace d'états, espace d'actions, récompense, conditions de fin) et justifier l'algorithme. Le code qui l'implémente est `training/features.py` (observation et action, partagé avec `agent.py`) et `training/env.py` (récompense, fin d'épisode, météo).

Les quatre pilotes `driver1` à `driver4` et le champion partagent ce MDP. Ils ne diffèrent que par leurs poids de récompense, leur graine et, pour le champion, la présence d'adversaires (`training/configs/<pilote>.yaml`).

## Le problème

Une voiture doit boucler trois tours d'un circuit inconnu, le plus vite possible, sous une météo changeante. Elle ne connaît ni sa position ni le tracé : elle ne perçoit que son LiDAR, sa vitesse, son braquage et, en course, la position relative des autres voitures. Le simulateur décide 20 fois par seconde.

L'état réel du monde (pose exacte, tracé, adhérence) n'est que partiellement observé. C'est un POMDP, que l'on traite comme un MDP sur l'observation enrichie de l'action précédente (voir « Mémoire » plus bas).

## Espace d'observation : 38 valeurs dans [-1,5 ; 1,5]

| Entrées | Nombre | Calcul | Pourquoi |
|---|---|---|---|
| LiDAR avant | 18 | Rayons 23 à 76 (±95° autour du cap), minimum par paquets de 3, puis `log(d / 0,1) / log(150)` | Voir loin devant, finement ce qui est proche |
| Vitesse | 1 | `velocity / 10` | |
| Braquage réel | 1 | `steering / 0,4189` | |
| Pluie | 1 | `(1 − friction_current) / 0,5`, écrêté à [0, 1] | Savoir quand freiner plus tôt |
| Action précédente | 2 | Sortie du réseau au pas d'avant | Mémoire courte, douceur |
| Adversaires | 3 × 5 | Pour les 3 plus proches : présent, `x_rel / 10`, `y_rel / 10` (écrêtés à ±1), `yaw_rel / π`, `speed / 10` | Le LiDAR ne voit pas les voitures |

**Pourquoi pas les 100 rayons ?** Le sujet pose la question : *avez-vous vraiment besoin de toutes les observations ?* Non. Les 46 rayons arrière ne servent pas à une voiture qui avance. Le minimum par secteur garde l'obstacle le plus proche, celui qui compte, et rend l'entrée moins sensible au bruit d'un rayon isolé.

**Pourquoi un logarithme ?** Le LiDAR va de 0,1 à 15 m. En linéaire, tout ce qui décide d'un choc (0,1 à 2 m) tiendrait dans 13 % de l'échelle. Avec le logarithme, 1 m vaut déjà 0,46 : le réseau distingue 30 cm de 60 cm.

**Pourquoi la pluie en entrée ?** Le simulateur publie l'adhérence courante dans `get_step_info()["friction_current"]`, qu'`agent.py` reçoit au tournoi. Plutôt que de la deviner à partir de glissades, la politique la lit, et peut freiner plus tôt sous la pluie. Au sec, la valeur est 0, comme à l'entraînement.

**Pourquoi trier les adversaires par distance ?** Les emplacements 0 à 3 du simulateur sont des numéros fixes, pas un ordre de course. Trier par distance rend l'entrée indépendante du numéro de chaque voiture. Un emplacement vide (adversaire absent, abandonné, ou la voiture elle-même) est rempli de zéros, avec un indicateur de présence à 0 : un adversaire n'est jamais confondu avec une voiture collée au pare-chocs.

**Un seul format pour tous.** En solo, les 15 entrées d'adversaires restent à zéro. Le champion part donc directement d'un pilote solo, sans changer la taille du réseau.

### Mémoire et conscience du temps

Le sujet demande : *faut-il se souvenir de ce qui vient de se passer ?* Oui, un peu. Une seule photo du LiDAR ne dit pas si la voiture dérape ni dans quel sens elle tournait. Trois éléments portent cette mémoire courte :

- la **vitesse** et le **braquage réel**, qui résument l'élan de la voiture ;
- l'**action précédente**, ce que la politique avait décidé un pas plus tôt ;
- la **pluie**, qui change lentement (toutes les 20 s).

Nous n'avons pas empilé plusieurs images LiDAR ni utilisé de réseau récurrent. À 20 Hz, la voiture bouge de 50 cm au plus entre deux pas : l'action précédente et la vitesse suffisent à lever l'ambiguïté. Un réseau récurrent compliquerait l'export ONNX et la reproduction de l'état interne dans `agent.py`, pour un gain que nos mesures ne réclament pas.

## Espace d'action : 2 valeurs dans [-1, 1]

| Sortie | Commande envoyée au simulateur |
|---|---|
| `a[0]` | vitesse cible = `-2 + (a[0] + 1) / 2 × 12`, de -2 à 10 m/s |
| `a[1]` | braquage = `a[1] × 0,4189` rad |

Les bornes sont celles de l'API (`_TARGET_SPEED_MIN`, `_TARGET_SPEED_MAX`). Le réseau sort des valeurs normalisées, ce qui garde les deux sorties à la même échelle pour PPO.

**La marche arrière compte.** En v1, nous l'avions interdite (vitesse de 0 à 10 m/s). Résultat : une voiture qui touchait un mur en biais restait collée, sans pouvoir se dégager, jusqu'à l'élimination pour stagnation. Avec la marche arrière, sur le même nombre de pas, le taux de courses finies sur les circuits de validation passe de 50 % à 100 %.

## Récompense

À chaque pas :

```
r = progression en mètres le long du circuit
    − 0,01                                   (coût du temps)
    − 0,05 × |braquage − braquage précédent| (douceur)
    − 2    si choc contre un mur
    − 1    si contact avec une autre voiture
    − 10   si élimination (sortie de piste ou stagnation)
```

- **Progression en mètres.** Le simulateur donne `progress_delta` en fraction de tour. On la multiplie par la longueur du circuit, sinon un mètre vaudrait deux fois moins sur Spa (554 m) que sur Oschersleben (261 m). Reculer donne une progression négative : la marche arrière coûte, elle ne sert qu'à se dégager.
- **Coût du temps.** Il rend la lenteur coûteuse et pousse à finir vite. Il prévient aussi la « police » du sujet : une voiture trop prudente perd des points à chaque pas sans rien gagner.
- **Douceur.** Le sujet demande si secouer le volant 20 fois par seconde est acceptable. Ce terme pénalise les à-coups. Il reste petit devant la progression : il départage deux façons de passer un virage, il n'empêche pas de tourner.
- **Choc et élimination.** Ils rendent visibles les erreurs que la progression seule ne punit pas assez tôt.

C'est le compromis *progression, survie, vitesse* du sujet. Nous l'avons vu basculer : sans fin d'épisode sur choc, un choc ne coûtait que -2, et la politique a appris à foncer en acceptant de toucher les murs (voir plus bas).

### Quatre pilotes, quatre variantes

Chaque membre a sa variante de récompense, pour explorer ce compromis :

| Pilote | Idée | Réglage différent |
|---|---|---|
| driver1 | Référence | poids par défaut |
| driver2 | Prudent | choc mur à -5 |
| driver3 | Pressé | coût du temps à 0,03 par pas |
| driver4 | Coulé | douceur à 0,2, horizon plus long (γ = 0,995) |

## Conditions de fin d'épisode

| Fin | Type Gymnasium | Cause |
|---|---|---|
| Trois tours bouclés | `terminated` | statut 2 du simulateur |
| Élimination | `terminated` | sortie de piste à plus de 1 m du bord, ou moins de 1 m de progression en 10 s |
| Choc contre un mur | `terminated` | à l'entraînement seulement |
| 3 000 pas (150 s) | `truncated` | limite de temps |

**Pourquoi finir l'épisode sur un choc, alors que le simulateur ne le fait pas ?** Au tournoi, un choc n'élimine pas : la voiture rebondit et repart. Mais à l'entraînement, finir l'épisode sur un choc rend le mur très coûteux : la politique perd toute la progression qu'elle aurait faite ensuite. Nous avons comparé les deux règles, avec marche arrière, sur 300 000 pas :

| Règle | Courses finies (validation) | Chocs mur par course | Meilleur tour |
|---|---|---|---|
| Fin sur choc | 6 / 6 | 0,17 | 32,9 s |
| Sans fin sur choc | 6 / 6 | 7,5 | 39,7 s |

Sans fin sur choc, la voiture finit aussi, mais en frottant les murs, et chaque choc la ralentit. L'évaluation, elle, applique la vraie règle du tournoi : pas de fin sur choc.

**Troncature et non terminaison.** La limite de 3 000 pas est une troncature : PPO continue d'estimer la valeur de l'état final au lieu de la mettre à zéro, la course n'étant pas réellement finie.

## Météo : du chaos à l'entraînement

Le sujet annonce de la pluie au tournoi : adhérence instable et rayons LiDAR corrompus. Le simulateur fourni les laisse figés : deux `TODO` dans `_update_friction` et `_update_lidar_noise`, avec une adhérence μ = 1 et un bruit de ±0,1 %. Ses constantes donnent pourtant les bornes : μ de 1 (sec) à 0,5 (forte pluie), bruit jusqu'à ±10 %, un changement toutes les 20 s.

`env.py` remplace ces deux méthodes, dans le processus d'entraînement seulement et sans modifier aucun fichier d'Epitech :

- toutes les 20 s, et dès le départ, un nouveau temps est tiré : sec 30 % du temps, sinon une intensité de pluie entre 0 et 1 ;
- l'adhérence μ descend de 1 à 0,5 avec la pluie, et elle est réellement appliquée au moteur (`update_params`), donc la voiture glisse ;
- le bruit LiDAR monte de ±0,1 % à ±10 % ;
- sous forte pluie, jusqu'à 5 % des rayons décrochent à chaque pas, à 0,1 m ou à 15 m.

À l'évaluation, une course sur deux se fait sous la pluie.

## Généralisation

Les 24 circuits sont séparés une fois pour toutes :

- **entraînement** : 17 circuits ;
- **validation** : Oschersleben, Zandvoort, MexicoCity, jamais vus à l'entraînement, pour comparer les réglages ;
- **test** : Spa, Budapest, Sochi, jamais utilisés pour décider quoi que ce soit ;
- `example` sert au débogage.

## Choix de l'algorithme : PPO

Nous utilisons PPO (Proximal Policy Optimization) de Stable-Baselines3, avec une politique gaussienne et deux réseaux de 2 × 64 neurones (politique et valeur).

**Pourquoi un algorithme à actions continues.** La vitesse et le braquage sont continus. Discrétiser (par exemple 5 vitesses × 7 angles) rendrait la conduite saccadée, à l'opposé de *smooth is good*, et ferait exploser le nombre d'actions. Cela écarte DQN et ses variantes.

**Pourquoi PPO plutôt que SAC.** SAC est l'autre candidat naturel en actions continues, et il réutilise mieux chaque échantillon. Trois raisons nous font préférer PPO ici :

1. **La simulation est bon marché, la stabilité est chère.** Nous faisons rouler 8 simulateurs en parallèle et produisons des millions de pas. L'avantage de SAC, l'efficacité par échantillon, compte peu. Le défaut de PPO, qui jette ses données après chaque mise à jour, coûte peu.
2. **Stabilité.** La limite (clip) de PPO empêche une mise à jour de trop changer la politique d'un coup. Avec une récompense que nous modifions souvent, cela évite qu'un mauvais lot de courses ne détruise un pilote qui savait déjà rouler.
3. **Peu de réglages et un parallélisme naturel.** PPO collecte avec plusieurs environnements à la fois sans tampon de rejeu de plusieurs millions de transitions. Ses valeurs par défaut fonctionnent, ce qui nous laisse concentrer les essais sur le MDP, là où se joue la conduite.

**Pourquoi Stable-Baselines3.** Une implémentation de référence et testée de PPO, plutôt qu'une version maison où un bug d'avantage ou de normalisation passerait inaperçu. L'export ONNX ne prend que le réseau de politique (`training/exporter.py`) : `agent.py` n'importe que `onnxruntime`, `numpy` et `os`.

**Réglages.** Les valeurs par défaut de SB3, sauf la taille de collecte : 2 048 pas par mise à jour au total, quel que soit le nombre d'environnements. À l'évaluation et au tournoi, la politique est déterministe : elle joue la moyenne de la gaussienne, sans le bruit d'exploration.

## Résultats

Le rapport final (CRA-87, à venir) donnera les courbes, les résultats par pilote et ce que ces choix ont donné.
