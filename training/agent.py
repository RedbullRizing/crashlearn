"""Pilote chargé au tournoi. Modèle commun, recopié par `exporter.py` dans
`submission/<pilote>/`, à côté de `model.onnx`, `model.onnx.data` et `features.py`.

N'importe que `os`, `numpy` et `onnxruntime` (`verify_submission.py`).
`features.py` est exécuté depuis ce dossier au lieu d'être importé : un
`import features` serait refusé, et partagerait `sys.modules` avec les agents
des autres équipes, chargés dans le même processus.
"""

import os

import numpy as np
import onnxruntime


class Agent:
    def __init__(self):
        # Chemins résolus depuis ce fichier, jamais depuis le cwd : le tournoi
        # charge plusieurs agents depuis des dossiers différents.
        here = os.path.dirname(os.path.abspath(__file__))
        self.model = onnxruntime.InferenceSession(os.path.join(here, "model.onnx"))
        self.entree = self.model.get_inputs()[0].name

        self.features = {}
        with open(os.path.join(here, "features.py")) as f:
            exec(f.read(), self.features)
        self.action_precedente = np.zeros(2, dtype=np.float32)

    def predict(self, obs: dict, info: dict) -> tuple[float, float]:
        if info.get("step_count", 0) == 0:   # nouvelle course
            self.action_precedente = np.zeros(2, dtype=np.float32)

        x = self.features["observation"](obs, self.action_precedente)
        action = self.model.run(None, {self.entree: x[None]})[0][0]
        self.action_precedente = np.clip(action, -1.0, 1.0).astype(np.float32)

        target_speed, steering = self.features["commande"](self.action_precedente)
        return float(target_speed), float(steering)
