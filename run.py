
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from flask_cors import CORS

app = create_app()

# SINGLE CORS configuration - NO duplicates
CORS(app, resources={r'/api/*': {'origins': '*', 'supports_credentials': True}}, expose_headers=['Content-Type', 'Authorization'])

app.url_map.strict_slashes = False

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
