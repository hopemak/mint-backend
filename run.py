from dotenv import load_dotenv
load_dotenv()

import os
from app import create_app
from flask_cors import CORS

app = create_app()

# SINGLE CORS configuration - NO duplicates
CORS(app, resources={r'/api/*': {'origins': '*', 'supports_credentials': True}}, expose_headers=['Content-Type', 'Authorization'])

app.url_map.strict_slashes = False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
