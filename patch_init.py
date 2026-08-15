import re

with open('app/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any old broken CORS handlers
content = re.sub(r'\n@app\.before_request\ndef handle_preflight\(\):.*?(?=\n@app\.|\nfrom |\nimport |\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n@app\.after_request\ndef after_request\(response\):.*?(?=\n@app\.|\nfrom |\nimport |\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n{3,}', '\n\n', content)

# Insert CORS AFTER app = Flask(__name__)
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
    with open('app/__init__.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('CORS added to app/__init__.py')
else:
    print('ERROR: app = Flask( not found')
