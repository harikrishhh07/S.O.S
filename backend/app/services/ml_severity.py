"""Local ML severity estimator trained from the bundled campus hazard labels."""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_CLASSES = None

# The bundled training split is small and has very few high-severity samples.
# These domain anchors prevent dangerous hazards from collapsing into the
# majority severity while the dataset grows.
SAFETY_ANCHORS = [
    ("live exposed electrical wiring sparking electric shock", 5),
    ("fire smoke flames burning material immediate danger", 5),
    ("structural collapse imminent falling ceiling severe crack", 5),
    ("damaged ceiling panel exposing wires and pipes", 4),
    ("large structural crack likely to cause injury", 4),
    ("blocked emergency exit dangerous access obstruction", 4),
    ("small pothole broken tile minor inconvenience", 2),
    ("fallen leaves dry plants peeling paint cosmetic issue", 1),
]


def _load_model():
    global _MODEL, _MODEL_CLASSES
    if _MODEL is not None:
        return _MODEL, _MODEL_CLASSES

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.pipeline import FeatureUnion

        labels_path = Path(__file__).resolve().parents[2] / "training_data" / "labels.json"
        labels = json.loads(labels_path.read_text())
        examples = labels.get("train", [])
        texts = [
            " ".join(
                str(example.get(field, ""))
                for field in ("summary", "description", "location")
            )
            for example in examples
        ]
        targets = [int(example["severity"]) for example in examples]
        texts.extend(text for text, _ in SAFETY_ANCHORS)
        targets.extend(severity for _, severity in SAFETY_ANCHORS)
        if len(set(targets)) < 2:
            return None, None

        _MODEL = Pipeline([
            ("features", FeatureUnion([
                ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
                ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True)),
            ])),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ])
        _MODEL.fit(texts, targets)
        _MODEL_CLASSES = list(_MODEL.named_steps["classifier"].classes_)
        return _MODEL, _MODEL_CLASSES
    except Exception as exc:
        logger.warning("Local ML severity model unavailable: %s", exc)
        return None, None


def predict_severity(text: str) -> Optional[dict]:
    """Predict severity from report text and return score, confidence, and model name."""
    model, classes = _load_model()
    if model is None:
        return None

    probabilities = model.predict_proba([text or ""])[0]
    best_index = int(probabilities.argmax())
    return {
        "severity": int(classes[best_index]),
        "confidence": round(float(probabilities[best_index]), 4),
        "model": "tfidf-logistic-regression-safety-augmented",
    }