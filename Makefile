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

DC := cd simulation && docker compose

# --- paramètres, surchargeables en ligne de commande -----------------------
# Exemple : make record NAME=grand-crash CARS=4 CTRL=random
# CTRL : pure_pursuit | random | submission
NAME   ?= essai
STEPS  ?= 1500
CARS   ?= 1
CTRL   ?= pure_pursuit
DRIVER ?= driver1

.DEFAULT_GOAL := help
.PHONY: help build check test venv record replay video train board board-stop verify verify-gp clean

help:                    ## Affiche cette aide
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Paramètres : NAME=$(NAME) STEPS=$(STEPS) CARS=$(CARS) CTRL=$(CTRL) DRIVER=$(DRIVER)"

# --- mise en route ---------------------------------------------------------
build:                   ## Construit l'image Docker (~10 min la première fois)
	$(DC) build

check:                   ## Vérifie que le simulateur tourne
	$(DC) run --rm sim

test:                    ## Lance les tests fournis par Epitech
	@cd simulation; \
	 docker compose run --rm sim python test_contract.py; a=$$?; \
	 docker compose run --rm sim python test_integration.py; b=$$?; \
	 echo ""; echo "=================================================="; \
	 if [ $$a -eq 0 ]; then echo "  test_contract     OK"; \
	                   else echo "  test_contract     ECHEC"; fi; \
	 if [ $$b -eq 0 ]; then echo "  test_integration  OK"; \
	                   else echo "  test_integration  ECHEC"; fi; \
	 if [ $$a -ne 0 ] || [ $$b -ne 0 ]; then \
	   echo ""; \
	   echo "  Deux echecs sont connus et viennent du simulateur fourni,"; \
	   echo "  pas de notre code : T08 (friction) et T05 (collisions)."; \
	   echo "  Voir le guide de l'equipe dans Linear."; \
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

clean:                   ## Arrête les conteneurs, purge enregistrements et points de montage
	@$(DC) down --remove-orphans 2>/dev/null || echo "  Docker non démarré — conteneurs ignorés"
	rm -f recordings/*.npz recordings/*.mp4
	@for d in training submission logs runs recordings; do \
	   rmdir "simulation/$$d" 2>/dev/null && echo "  supprimé simulation/$$d" || true; \
	 done
