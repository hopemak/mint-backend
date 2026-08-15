with open('run.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any @app.before_request or @app.after_request blocks
import re
content = re.sub(r'\n@app\.before_request\ndef handle_preflight\(\):.*?(?=\n@app\.|\nif __name__|\nfrom |\nimport |\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n@app\.after_request\ndef after_request\(response\):.*?(?=\n@app\.|\nif __name__|\nfrom |\nimport |\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n{3,}', '\n\n', content)

with open('run.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('run.py repaired')
