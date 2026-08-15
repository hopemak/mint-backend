with open('app/routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "/codes/send" in content:
    print("send endpoint already exists")
else:
    old = """@admin_bp.route('/codes/requests', methods=['GET', 'OPTIONS'])
@jwt_required()
def list_requests():"""

    new = """@admin_bp.route('/codes/send', methods=['POST', 'OPTIONS'])
@jwt_required()
def send_institution_code():
    \"\"\"Generate code and email it directly to user\"\"\"
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    code = f\"MINT-{secrets.token_hex(4).upper()}\"
    
    codes_coll = get_collection('institution_codes')
    if codes_coll:
        codes_coll.insert_one({
            'code': code,
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        })
    else:
        _memory_codes.append({
            'code': code,
            'used': False,
            'created_at': datetime.utcnow().isoformat()
        })

    emailed = False
    try:
        from app.email import EmailService
        svc = EmailService()
        if svc.enabled:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            sg = SendGridAPIClient(svc.api_key)
            message = Mail(
                from_email=svc.from_email,
                to_emails=email,
                subject='Your MInT Institution Access Code',
                html_content=f'<p>Your institution code is: <strong>{code}</strong></p><p>Use this to register at MInT Innovation Platform.</p>'
            )
            sg.send(message)
            emailed = True
    except Exception as e:
        print('Email failed:', e)

    return jsonify({
        'success': True,
        'code': code,
        'email': email,
        'emailed': emailed,
        'message': 'Code sent via email!' if emailed else f'Code generated: {code} (email not configured - copy manually)'
    }), 201


@admin_bp.route('/codes/requests', methods=['GET', 'OPTIONS'])
@jwt_required()
def list_requests():"""

    content = content.replace(old, new)

    with open('app/routes/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added /codes/send endpoint")
