from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.ml.idea_classifier import classify_idea, model_info

classify_bp = Blueprint("classify_bp", __name__)


@classify_bp.route("/api/ml/classify-idea", methods=["POST"])
@jwt_required()
def classify():
    data = request.get_json(silent=True) or {}
    text = " ".join(str(data.get(k, "")) for k in ("title", "description", "text")).strip()
    if len(text) < 10:
        return jsonify({"error": "Send 'description' with at least 10 characters"}), 400
    return jsonify(classify_idea(text)), 200


@classify_bp.route("/api/ml/classify-idea/info", methods=["GET"])
@jwt_required()
def info():
    return jsonify(model_info()), 200
