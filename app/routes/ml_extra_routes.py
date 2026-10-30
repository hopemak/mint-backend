from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.ml.similarity import compare_ideas
from app.ml import success_logistic

ml_extra_bp = Blueprint("ml_extra_bp", __name__)
_TEXT_KEYS = ("title", "description", "problem", "solution", "summary")


def _idea_text(idea):
    return " ".join(str(idea.get(k) or "") for k in _TEXT_KEYS).strip()


@ml_extra_bp.route("/api/ml/idea-similarity", methods=["POST"])
@jwt_required()
def idea_similarity():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    return jsonify({"matches": compare_ideas(text, data.get("candidates") or [])}), 200


@ml_extra_bp.route("/api/ml/idea-duplicates", methods=["POST"])
@jwt_required()
def idea_duplicates():
    from app.routes.ideas import load_ideas
    data = request.get_json(silent=True) or {}
    text = _idea_text(data)
    if len(text) < 10:
        return jsonify({"error": "Send 'title' and 'description' (at least 10 characters)"}), 400
    ideas = load_ideas()
    if isinstance(ideas, dict):
        ideas = list(ideas.values())
    exclude = str(data.get("exclude_id") or "")
    cands = [{"id": i.get("id"), "title": i.get("title"), "text": _idea_text(i)}
             for i in ideas if isinstance(i, dict) and str(i.get("id")) != exclude]
    return jsonify({"matches": compare_ideas(text, cands), "compared_with": len(cands)}), 200


@ml_extra_bp.route("/api/ml/logreg-forecast", methods=["POST"])
@jwt_required()
def logreg_forecast():
    data = request.get_json(silent=True) or {}
    result = success_logistic.predict(data.get("features") or {})
    if result is None:
        return jsonify({"error": "logistic model not trained yet"}), 503
    return jsonify(result), 200
