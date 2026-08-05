"""
Document API - File upload and management
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

documents_bp = Blueprint('documents', __name__)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx',
    'ppt', 'pptx',
    'xls', 'xlsx',
    'png', 'jpg', 'jpeg',
    'txt', 'csv'
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_documents_data():
    try:
        with open('./data/documents.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {'documents': []}


def save_documents_data(data):
    os.makedirs('./data', exist_ok=True)
    with open('./data/documents.json', 'w') as f:
        json.dump(data, f, indent=2)


@documents_bp.route('', methods=['GET'])
@jwt_required()
def list_documents():
    """List all documents uploaded by the logged-in user."""
    user_id = get_jwt_identity()

    documents_data = get_documents_data()

    docs = [
        d for d in documents_data['documents']
        if d['user_id'] == user_id
    ]

    docs.sort(
        key=lambda x: x.get('uploaded_at', ''),
        reverse=True
    )

    return jsonify({
        'success': True,
        'data': docs
    }), 200


@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    extension = file.filename.rsplit('.', 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'File type .{extension} not allowed'}), 400

    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    file.save(file_path)

    documents_data = get_documents_data()

    document = {
        'document_id': f'DOC-{len(documents_data["documents"]) + 1:04d}',
        'user_id': user_id,
        'filename': filename,
        'unique_filename': unique_filename,
        'file_path': file_path,
        'file_size': os.path.getsize(file_path),
        'file_type': extension,
        'document_type': request.form.get('document_type', 'general'),
        'startup_id': request.form.get('startup_id'),
        'uploaded_at': datetime.utcnow().isoformat()
    }

    documents_data['documents'].append(document)
    save_documents_data(documents_data)

    return jsonify({
        'success': True,
        'message': 'Document uploaded',
        'data': document
    }), 201


@documents_bp.route('/<document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    documents_data = get_documents_data()

    for doc in documents_data['documents']:
        if doc['document_id'] == document_id:

            if request.args.get('download') == 'true':
                return send_file(doc['file_path'], as_attachment=True)

            return jsonify({
                'success': True,
                'data': doc
            }), 200

    return jsonify({'error': 'Document not found'}), 404


@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    user_id = get_jwt_identity()

    documents_data = get_documents_data()

    for i, doc in enumerate(documents_data['documents']):
        if doc['document_id'] == document_id:

            if doc['user_id'] != user_id:
                return jsonify({'error': 'Unauthorized'}), 403

            if os.path.exists(doc['file_path']):
                os.remove(doc['file_path'])

            documents_data['documents'].pop(i)
            save_documents_data(documents_data)

            return jsonify({
                'success': True,
                'message': 'Document deleted'
            }), 200

    return jsonify({'error': 'Document not found'}), 404