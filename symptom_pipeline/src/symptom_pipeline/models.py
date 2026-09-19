"""Training harness for the candidate-edge discrepancy classifier.

Recommended v1 architecture (design doc section 3): a gradient-boosted
classifier over candidate-edge features. A regularized-logistic baseline is
also provided as the interpretable minimum comparison point. Both output

    q(e) = probability that candidate e disagrees with the blueprint,
           given the report and documented graph

as a raw (uncalibrated) score; see `calibration.py` for turning that into a
calibrated probability and a suspect prefix.

No trained model artifact ships with this package: training needs the
causal dataset from `datasets.py`, which needs `simulation.py`, which is not
implemented yet (see that module's docstring). This module's training and
inference code is real and unit-testable on synthetic feature/label data
today (see `tests/test_models.py`); only the "get real data" step is
missing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

from .features import NUMERIC_FEATURE_FIELDS, CandidateFeatures

GBM_MODEL_VERSION = "0.1.0-gbm"
LOGISTIC_MODEL_VERSION = "0.1.0-logistic"


def _row_dict(f: CandidateFeatures) -> dict:
    row = {col: float(getattr(f, col)) for col in NUMERIC_FEATURE_FIELDS}
    # One-hot encoded at the point of use via DictVectorizer, so the
    # vocabulary is fit once at training time and frozen for inference.
    row[f"source_type={f.source_type}"] = 1.0
    row[f"target_type={f.target_type}"] = 1.0
    return row


@dataclass
class DiscrepancyModel:
    vectorizer: DictVectorizer
    classifier: object
    version: str

    def predict_raw(self, features: list[CandidateFeatures]) -> np.ndarray:
        """Raw (uncalibrated) P(discordant) per candidate, in `features`
        order. Never trust these as calibrated probabilities directly --
        pass through `calibration.Calibrator.apply` first.
        """
        x = self.vectorizer.transform([_row_dict(f) for f in features])
        return self.classifier.predict_proba(x)[:, 1]


def train_gbm(
    features: list[CandidateFeatures],
    labels: list[bool],
    n_estimators: int = 200,
    max_depth: int = 3,
    learning_rate: float = 0.05,
    random_state: int = 0,
) -> DiscrepancyModel:
    vectorizer = DictVectorizer(sparse=True)
    x = vectorizer.fit_transform([_row_dict(f) for f in features])
    y = np.asarray(labels, dtype=int)
    clf = GradientBoostingClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=random_state,
    )
    clf.fit(x, y)
    return DiscrepancyModel(vectorizer=vectorizer, classifier=clf, version=GBM_MODEL_VERSION)


def train_logistic_baseline(
    features: list[CandidateFeatures],
    labels: list[bool],
    C: float = 1.0,
    random_state: int = 0,
) -> DiscrepancyModel:
    vectorizer = DictVectorizer(sparse=True)
    x = vectorizer.fit_transform([_row_dict(f) for f in features])
    y = np.asarray(labels, dtype=int)
    clf = LogisticRegression(max_iter=1000, C=C, random_state=random_state)
    clf.fit(x, y)
    return DiscrepancyModel(vectorizer=vectorizer, classifier=clf, version=LOGISTIC_MODEL_VERSION)
