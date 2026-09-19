import numpy as np

from symptom_pipeline.features import CandidateFeatures
from symptom_pipeline.models import train_gbm, train_logistic_baseline


def _synthetic_features_and_labels(n: int = 60, seed: int = 0):
    rng = np.random.RandomState(seed)
    features = []
    labels = []
    for i in range(n):
        # A discrepancy is more likely when the candidate is unclaimed AND
        # close to the reported location -- a signal the model should be
        # able to pick up on this toy synthetic data.
        is_claimed = bool(rng.randint(0, 2))
        min_dist = int(rng.randint(0, 5))
        label = (not is_claimed) and (min_dist <= 1)
        features.append(
            CandidateFeatures(
                source_id=f"S{i}",
                target_id=f"T{i}",
                relation="feeds",
                source_type="AHU" if i % 2 == 0 else "VAV",
                target_type="VAV" if i % 2 == 0 else "HVAC_Zone",
                is_claimed=is_claimed,
                source_distance_from_report=min_dist,
                target_distance_from_report=min_dist + 1,
                min_endpoint_distance_from_report=min_dist,
                reachable_from_report=True,
                shares_location_with_report=False,
                n_other_spaces_named=0,
                direction_too_hot=True,
                direction_too_cold=False,
                direction_alternating=False,
                direction_unknown=False,
                airflow_weak=False,
                airflow_absent=False,
                airflow_unknown=False,
                supply_air_warm=False,
                supply_air_cool=False,
                supply_air_unknown=True,
                persistence_intermittent=False,
                persistence_startup_only=False,
                onset_today=False,
                onset_unknown=False,
                other_spaces_checked=True,
                operating_heating=False,
                operating_cooling=True,
            )
        )
        labels.append(label)
    return features, labels


def test_train_gbm_predicts_probabilities_in_range():
    features, labels = _synthetic_features_and_labels()
    model = train_gbm(features, labels, n_estimators=20)
    preds = model.predict_raw(features)
    assert len(preds) == len(features)
    assert all(0.0 <= p <= 1.0 for p in preds)


def test_train_gbm_separates_synthetic_signal_better_than_chance():
    features, labels = _synthetic_features_and_labels(n=200, seed=1)
    model = train_gbm(features, labels, n_estimators=50)
    preds = model.predict_raw(features)
    positive_mean = float(np.mean([p for p, y in zip(preds, labels) if y]))
    negative_mean = float(np.mean([p for p, y in zip(preds, labels) if not y]))
    assert positive_mean > negative_mean


def test_train_logistic_baseline_runs_and_predicts():
    features, labels = _synthetic_features_and_labels()
    model = train_logistic_baseline(features, labels)
    preds = model.predict_raw(features)
    assert all(0.0 <= p <= 1.0 for p in preds)


def test_unseen_categorical_value_does_not_crash_inference():
    features, labels = _synthetic_features_and_labels()
    model = train_gbm(features, labels, n_estimators=10)
    novel = features[0]
    novel_with_new_type = CandidateFeatures(**{**novel.__dict__, "source_type": "NeverSeenBeforeType"})
    preds = model.predict_raw([novel_with_new_type])
    assert 0.0 <= preds[0] <= 1.0
