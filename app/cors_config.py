from flask_cors import CORS

def setup_cors(app):
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://localhost:5174",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:5174"
                ]
            }
        },
        supports_credentials=True
    )

    return app
