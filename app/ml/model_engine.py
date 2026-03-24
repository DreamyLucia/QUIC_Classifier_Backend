import torch
import numpy as np
import joblib
from typing import Dict, Any, Optional
import os


class TemporalCNN(torch.nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.conv = torch.nn.Sequential(
            torch.nn.Conv1d(1, 16, 5),
            torch.nn.ReLU(),
            torch.nn.AvgPool1d(3),
            torch.nn.Conv1d(16, 32, 5),
            torch.nn.ReLU()
        )
        self.fc = torch.nn.Sequential(
            torch.nn.Linear(32 + 4, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, num_classes)
        )

    def forward(self, temporal, stats):
        x = self.conv(temporal.unsqueeze(1))
        x = torch.mean(x, dim=2)
        return self.fc(torch.cat([x, stats], dim=1))


class PayloadCNN(torch.nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.conv = torch.nn.Sequential(
            torch.nn.Conv1d(1, 8, 3),
            torch.nn.ReLU(),
            torch.nn.AvgPool1d(3),
            torch.nn.Conv1d(8, 16, 5),
            torch.nn.ReLU(),
            torch.nn.AvgPool1d(2),
            torch.nn.Conv1d(16, 32, 5),
            torch.nn.ReLU()
        )
        self.fc = torch.nn.Sequential(
            torch.nn.Linear(32 + 4, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, num_classes)
        )

    def forward(self, payload, stats):
        x = self.conv(payload.unsqueeze(1))
        x = torch.mean(x, dim=2)
        return self.fc(torch.cat([x, stats], dim=1))


class ModelEngine:
    def __init__(self, time_model_path: str, byte_model_path: str, nb_clf_path: Optional[str] = None):
        self.num_classes = 8
        self.class_names = ['Nkiri', 'bilibili', 'edge', 'kwai',
                            'tencentnews', 'tencentvideo', 'tiktok', 'xiaohongshu']

        self.time_features_dim = 120
        self.byte_features_dim = 900
        self.stat_features_dim = 4

        self.device = torch.device('cpu')

        self.time_model = TemporalCNN(self.num_classes).to(self.device)
        self.byte_model = PayloadCNN(self.num_classes).to(self.device)

        if os.path.exists(time_model_path):
            self.time_model.load_state_dict(torch.load(time_model_path, map_location=self.device))
            self.time_model.eval()

        if os.path.exists(byte_model_path):
            self.byte_model.load_state_dict(torch.load(byte_model_path, map_location=self.device))
            self.byte_model.eval()

        self.nb_clf = None
        if nb_clf_path and os.path.exists(nb_clf_path):
            self.nb_clf = joblib.load(nb_clf_path)

    def _get_probs(self, model, x, stats):
        model.eval()
        with torch.no_grad():
            outputs = model(torch.FloatTensor(x).to(self.device),
                            torch.FloatTensor(stats).to(self.device))
            return torch.softmax(outputs, dim=1).cpu().numpy()

    def predict(self, features: np.ndarray) -> Dict[str, Any]:
        time_feat = features[:self.time_features_dim].reshape(1, -1)
        byte_feat = features[self.time_features_dim:self.time_features_dim + self.byte_features_dim].reshape(1, -1)
        stats_feat = features[-self.stat_features_dim:].reshape(1, -1)

        time_probs = self._get_probs(self.time_model, time_feat, stats_feat)
        byte_probs = self._get_probs(self.byte_model, byte_feat, stats_feat)

        if self.nb_clf is not None:
            ensemble_feat = np.concatenate([time_probs, byte_probs], axis=1)
            pred_id = self.nb_clf.predict(ensemble_feat)[0]
            probs = (time_probs[0] + byte_probs[0]) / 2
        else:
            probs = (time_probs[0] + byte_probs[0]) / 2
            pred_id = np.argmax(probs)

        confidence = probs[pred_id]

        return {
            'label': self.class_names[pred_id],
            'label_id': int(pred_id),
            'confidence': float(confidence),
            'probabilities': probs.tolist()
        }