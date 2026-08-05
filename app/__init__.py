from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    
    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # JWT
    JWTManager(app)
    
    # Register blueprints
    register_blueprints(app)
    
    @app.route('/api/health')
    def health():
        return {'status': 'OK', 'message': 'Backend is running!'}
    
    @app.route('/')
    def index():
        return {
            'name': 'Mint Innovation Platform API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    logger.info("🚀 Backend initialized successfully")
    return app

def register_blueprints(app):
    """Register all blueprints"""
    
    blueprints = [
        ('auth', 'auth_bp', '/api/auth'),
        ('users', 'users_bp', '/api/users'),
        ('startups', 'startups_bp', '/api/startups'),
        ('funding', 'funding_bp', '/api/funding'),
        ('grants', 'grants_bp', '/api/grants'),
        ('ml', 'ml_bp', '/api/ml'),
        ('mentors', 'mentors_bp', '/api/mentors'),
        ('dashboard', 'dashboard_bp', '/api/dashboard'),
        ('documents', 'documents_bp', '/api/documents'),
        ('audit', 'audit_bp', '/api/audit'),
        ('evaluation', 'evaluation_bp', '/api/evaluations'),
        ('public_ml', 'public_ml_bp', None),
        ('ideas', 'ideas_bp', None),
    ]
    
    for module_name, bp_name, url_prefix in blueprints:
        try:
            module = __import__(f'app.routes.{module_name}', fromlist=[bp_name])
            bp = getattr(module, bp_name)
            if url_prefix:
                app.register_blueprint(bp, url_prefix=url_prefix)
            else:
                app.register_blueprint(bp)
            logger.info(f"✅ Registered blueprint: {module_name}")
        except ImportError as e:
            logger.warning(f"⚠️ Could not register {module_name}: {e}")
