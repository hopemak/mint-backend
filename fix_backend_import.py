import glob, os

base = os.path.expanduser('~/Documents/Mint-incubator/mint-platform')
matches = glob.glob(os.path.join(base, '**/ideas.py'), recursive=True)

if matches:
    path = matches[0]
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if jwt_required is imported
    if 'jwt_required' not in content:
        # Add the import after the existing imports
        content = content.replace(
            'from flask import Blueprint, request, jsonify',
            'from flask import Blueprint, request, jsonify\nfrom flask_jwt_extended import jwt_required'
        )
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('✅ Added jwt_required import to ideas.py')
    else:
        print('jwt_required already imported')
else:
    print('ideas.py not found')
