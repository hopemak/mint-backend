import os

candidates = ['run.py', 'app.py', 'main.py', 'wsgi.py', 'app/__init__.py']
app_file = None
for c in candidates:
    if os.path.exists(c):
        app_file = c
        break

print('Found:', app_file)

if app_file:
    with open(app_file, 'r') as f:
        content = f.read()
    
    if 'handle_preflight' not in content:
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if 'app = Flask(' in line:
                insert_idx = i + 1
        
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
        
        with open(app_file, 'w') as f:
            f.write(content)
        print('CORS handlers added')
    else:
        print('CORS handlers already present')
