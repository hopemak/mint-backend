import os
import re

candidates = ['run.py', 'app.py', 'main.py', 'wsgi.py', 'app/__init__.py']
app_file = None
for c in candidates:
    if os.path.exists(c):
        app_file = c
        break

print('Found app file:', app_file)

with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove ALL @app.before_request and @app.after_request blocks
content = re.sub(r'\n@app\.before_request\ndef handle_preflight\(\):.*?(?=\n@app\.|\nif __name__|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n@app\.after_request\ndef after_request\(response\):.*?(?=\n@app\.|\nif __name__|\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n{3,}', '\n\n', content)

# Find app = Flask( and insert CORS AFTER it
lines = content.split('\n')
insert_idx = None
for i, line in enumerate(lines):
    if 'app = Flask(' in line:
        insert_idx = i + 1
        break

if insert_idx:
    handler = """
@app.before_request
def handle_preflight():
    from flask import request, make_response
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
"""
    lines.insert(insert_idx, handler)
    content = '\n'.join(lines)
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print('CORS fixed successfully')
else:
    print('ERROR: Could not find app = Flask(')
