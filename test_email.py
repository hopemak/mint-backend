"""
Test Email System
"""

import os
from dotenv import load_dotenv
from app.email import email_service, send_welcome_email, send_funding_approved_email

load_dotenv()

print("=" * 60)
print("📧 Testing Email System")
print("=" * 60)

print(f"\n📊 Email Service Status:")
print(f"   Enabled: {email_service.enabled}")
print(f"   From: {email_service.from_email}")
print(f"   API Key Present: {bool(os.environ.get('SENDGRID_API_KEY'))}")

# Test sending a welcome email (simulated if no API key)
print("\n📧 Sending test welcome email...")
success = send_welcome_email(
    user_email="test@example.com",
    user_name="Test User"
)

if email_service.enabled:
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
else:
    print("   ⚠️ Email disabled - email would have been sent")

print("\n📧 Testing funding approval email...")
success = send_funding_approved_email(
    user_email="test@example.com",
    user_name="Test User",
    startup_name="AgriTech Solutions",
    amount=350000,
    request_id="FR-0001"
)

if email_service.enabled:
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
else:
    print("   ⚠️ Email disabled - email would have been sent")

print("\n" + "=" * 60)
print("✅ Email test complete!")
print("=" * 60)
