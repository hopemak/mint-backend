with open('app/__init__.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 15-30 (the broken CORS handlers outside the function)
# But let's be smart about it — remove any @app.before_request or @app.after_request
# that appears BEFORE 'def create_app():'
new_lines = []
inside_create_app = False
skip_until_next_def = False
for i, line in enumerate(lines):
    if 'def create_app():' in line:
        inside_create_app = True
    
    # If we see @app. before create_app, skip those lines
    if not inside_create_app and '@app.' in line:
        skip_until_next_def = True
        continue
    
    if skip_until_next_def and line.strip() and not line.startswith(' '):
        skip_until_next_def = False
    
    if skip_until_next_def:
        continue
    
    new_lines.append(line)

content = ''.join(new_lines)

# Now find 'app = Flask(__name__)' inside create_app and insert CORS after it
lines = content.split('\n')
new_lines = []
inserted = False
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'app = Flask(__name__)' in line and not inserted:
        indent = '    '  # 4 spaces inside create_app
        handler = [
            '',
            indent + '@app.before_request',
            indent + 'def handle_preflight():',
            indent + '    from flask import request, make_response',
            indent + '    if request.method == "OPTIONS":',
            indent + '        response = make_response()',
            indent + '        response.headers.add("Access-Control-Allow-Origin", "*")',
            indent + '        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")',
            indent + '        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")',
            indent + '        return response',
            '',
            indent + '@app.after_request',
            indent + 'def after_request(response):',
            indent + '    response.headers.add("Access-Control-Allow-Origin", "*")',
            indent + '    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")',
            indent + '    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")',
            indent + '    return response',
        ]
        new_lines.extend(handler)
        inserted = True

with open('app/__init__.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('Fixed app/__init__.py')
