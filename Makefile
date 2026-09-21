# Crash & Learn — raccourcis de développement.
#
# macOS et Linux : make fonctionne tel quel.
# Windows        : lancer depuis WSL2 ou Git Bash (make n'existe pas dans cmd.exe).
#
# Les cibles qui simulent passent par Docker ; celles qui affichent une fenêtre
# tournent sur la machine, parce qu'un conteneur n'a pas d'écran.

# --- détection de la plateforme -------------------------------------------
ifeq ($(OS),Windows_NT)                 # Git Bash
  PY  := .venv/Scripts/python.exe
  MPL := TkAgg
else
  PY  := .venv/bin/python
  ifeq ($(shell uname -s),Darwin)
    MPL := MacOSX
  else
    MPL := TkAgg
  endif
endif

DC := docker compose

# --- paramètres, surchargeables en ligne de commande -----------------------
# Exemple : make record NAME=grand-crash CARS=4 CTRL=random
# CTRL : pure_pursuit | random | submission
NAME   ?= essai
STEPS  ?= 1500
CARS   ?= 1
CTRL   ?= pure_pursuit
DRIVER ?= driver1

.DEFAULT_GOAL := help
.PHONY: help sim-check sim-hash build check test venv record replay video train board board-stop verify verify-gp clean

help:                    ## Affiche cette aide
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Paramètres : NAME=$(NAME) STEPS=$(STEPS) CARS=$(CARS) CTRL=$(CTRL) DRIVER=$(DRIVER)"

# --- mise en route ---------------------------------------------------------
sim-check:
	@test -f simulation/Dockerfile || { \
	  echo "  simulation/ est absent."; \
	  echo "  Il n'est pas versionné : télécharge l'archive d'Epitech et"; \
	  echo "  décompresse-la en simulation/ à la racine du dépôt."; \
	  echo "  Voir CONTRIBUTING.md."; \
	  exit 1; }

sim-hash: sim-check      ## Empreinte du simulateur — doit être identique chez tous
	@cd simulation && find . -type f -not -path './__pycache__/*' -not -name '*.pyc' \
	  | sort | xargs shasum -a 256 | shasum -a 256 | cut -c1-16

build: sim-check         ## Construit l'image Docker (~10 min la première fois)
	$(DC) build

check: sim-check         ## Vérifie que le simulateur tourne
	$(DC) run --rm sim

test: sim-check          ## Lance les tests fournis par Epitech
	@docker compose run --rm sim python test_contract.py; a=$$?; \
	 docker compose run --rm sim python test_integration.py; b=$$?; \
	 echo ""; echo "=================================================="; \
	 if [ $$a -eq 0 ]; then echo "  test_contract     OK"; \
	                   else echo "  test_contract     ECHEC"; fi; \
	 if [ $$b -eq 0 ]; then echo "  test_integration  OK"; \
	                   else echo "  test_integration  ECHEC"; fi; \
	 if [ $$a -ne 0 ] || [ $$b -ne 0 ]; then \
	   echo ""; \
	   echo "  T08 (friction) echoue par conception : env_simulation.py fige"; \
	   echo "  l'adherence et porte un TODO. La meteo viendra de notre env.py."; \
	   echo "  Tout autre echec est anormal — voir le guide d'equipe dans Linear."; \
	   exit 1; \
	 fi

venv:                    ## Installe l'environnement local pour l'affichage
	python3 -m venv .venv
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet numpy pillow pyyaml matplotlib

# --- voir une course -------------------------------------------------------
record:                  ## Enregistre une course -> recordings/<NAME>.npz
	$(DC) run --rm recorder python sim_recorder.py \
		--steps $(STEPS) --num-cars $(CARS) --controller $(CTRL) \
		--out /app/recordings/$(NAME).npz

replay:                  ## Ouvre la course dans une fenêtre (nécessite make venv)
	cd simulation && MPLBACKEND=$(MPL) ../$(PY) viz_replay.py \
		--npz ../recordings/$(NAME).npz --follow

video:                   ## Exporte la course en MP4 -> recordings/<NAME>.mp4
	$(DC) run --rm replay python viz_replay.py \
		--npz /app/recordings/$(NAME).npz \
		--record /app/recordings/$(NAME).mp4 --no-telemetry

# --- entraîner -------------------------------------------------------------
train:                   ## Entraîne un pilote : make train DRIVER=driver2
	$(DC) run --rm sim python training/train.py --driver $(DRIVER)

board:                   ## Démarre TensorBoard sur http://localhost:6006
	$(DC) up -d tensorboard

board-stop:              ## Arrête TensorBoard
	$(DC) stop tensorboard

# --- vérifier avant de rendre ----------------------------------------------
verify:                  ## Vérifie un pilote : make verify DRIVER=driver2
	$(DC) run --rm sim python verify_submission.py --submission submission/$(DRIVER)

verify-gp:               ## Vérifie la livraison complète (mode tournoi)
	$(DC) run --rm sim python verify_submission.py --submission submission/ --grandprix

clean:                   ## Arrête les conteneurs et purge les enregistrements
	@$(DC) down --remove-orphans 2>/dev/null || echo "  Docker non démarré — conteneurs ignorés"
	rm -f recordings/*.npz recordings/*.mp4
