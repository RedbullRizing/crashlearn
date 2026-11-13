"""Transforme un run entraîné en dossier pilote livrable.

    make export RUN=driver4-20261030-093034-ppo DRIVER=driver4

Écrit dans `submission/<pilote>/` : `model.onnx` + `model.onnx.data` (opset 17,
réseau de politique seul, sans la fonction de valeur), `agent.py` et
`features.py` recopiés depuis `training/`. Puis vérifie, avant de rendre la main :

* que l'ONNX donne les mêmes actions que PyTorch sur des observations réelles ;
* que l'`Agent` livré, chargé comme au tournoi, finit une course.

`make verify DRIVER=driver4` reste à lancer ensuite : c'est l'outil d'Epitech.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.modules["gym"] = None

import numpy as np
import onnx
import onnxruntime
import torch
from stable_baselines3 import PPO

import env_simulation as sim
from agent_loader import validate_and_load_agent
from training.env import Course
from training.metrics import SuiviCourse
from training.runs import RACINE_RUNS

OPSET = 17
TRAINING = Path(__file__).parent


class Politique(torch.nn.Module):
    """Moyenne de la gaussienne de PPO : l'action déterministe, avant écrêtage."""

    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def forward(self, obs):
        p = self.policy
        latent = p.mlp_extractor.forward_actor(p.extract_features(obs, p.pi_features_extractor))
        return p.action_net(latent)


def exporter(model: PPO, dossier: Path) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / "model.onnx"
    entree = torch.zeros(1, model.observation_space.shape[0])
    torch.onnx.export(Politique(model.policy).eval(), entree, chemin, opset_version=OPSET,
                      input_names=["obs"], output_names=["action"],
                      dynamic_axes={"obs": {0: "n"}, "action": {0: "n"}}, dynamo=False)
    onnx.save_model(onnx.load(chemin), chemin, save_as_external_data=True,
                    all_tensors_to_one_file=True, location="model.onnx.data", size_threshold=0)
    for nom in ("agent.py", "features.py"):
        shutil.copy(TRAINING / nom, dossier / nom)


def observations_reelles(model: PPO, circuit: str, n: int = 500) -> np.ndarray:
    env = Course(circuits=[circuit], fin_sur_choc=False)
    obs, _ = env.reset(seed=0)
    lot = []
    for _ in range(n):
        lot.append(obs)
        obs, _, termine, tronque, _ = env.step(model.predict(obs, deterministic=True)[0])
        if termine or tronque:
            obs, _ = env.reset()
    return np.array(lot, dtype=np.float32)


def course_avec_agent(dossier: Path, circuit: str, pas_max: int = 6000):
    """Une course pilotée par l'Agent livré, chargé par agent_loader comme au tournoi."""
    _, agent = validate_and_load_agent(dossier)
    sim.reset(num_cars=1, seed=1)
    suivi = SuiviCourse(nb_voitures=1)
    info = sim.get_step_info()
    for _ in range(pas_max):
        sim.apply_action(0, *agent.predict(sim.get_obs(0), info))
        sim.simulation_step()
        info = sim.get_step_info()
        suivi.observer(info)
        if info["agent_status"][0] != 1:
            break
    return suivi.resultats()[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="nom du dossier dans runs/")
    parser.add_argument("--pilote", required=True, help="driver1 … driver4, ou champion")
    parser.add_argument("--circuit", default="example", help="circuit des vérifications")
    args = parser.parse_args()

    model = PPO.load(RACINE_RUNS / args.run / "model.zip", device="cpu")
    dossier = Path("submission") / args.pilote
    exporter(model, dossier)
    print(f"  exporté : {dossier}/ (model.onnx, model.onnx.data, agent.py, features.py)")

    lot = observations_reelles(model, args.circuit)
    with torch.no_grad():
        attendu = Politique(model.policy).eval()(torch.from_numpy(lot)).numpy()
    obtenu = onnxruntime.InferenceSession(str(dossier / "model.onnx")).run(None, {"obs": lot})[0]
    ecart = float(np.abs(attendu - obtenu).max())
    print(f"  ONNX ≡ PyTorch sur {len(lot)} observations réelles : écart max {ecart:.2e}")
    assert ecart < 1e-4, "l'ONNX ne reproduit pas la politique"

    voiture = course_avec_agent(dossier, args.circuit)
    etat = "arrivée" if voiture.a_termine else (voiture.cause_abandon or "temps écoulé")
    print(f"  course avec l'Agent livré ({args.circuit}) : {etat}, {voiture.tours} tour(s), "
          f"{voiture.chocs_mur} choc(s)")
    print(f"\n  reste à lancer : make verify DRIVER={args.pilote}")


if __name__ == "__main__":
    main()
