"""
Email Notification Service
"""

import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, TemplateId
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Email notification service using SendGrid"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('EMAIL_FROM', 'notifications@mint.gov')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'MInT Innovation Platform')
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            self.client = SendGridAPIClient(self.api_key)
            logger.info("✅ Email service initialized")
        else:
            logger.warning("⚠️ Email service disabled (no API key)")
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   to_name: Optional[str] = None, template_id: Optional[str] = None,
                   template_data: Optional[Dict] = None) -> bool:
        """Send an email"""
        if not self.enabled:
            logger.info(f"📧 Email would be sent to {to_email}: {subject}")
            logger.info(f"📧 Content: {html_content[:100]}...")
            return True
        
        try:
            from_email = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email, to_name) if to_name else To(to_email)
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                html_content=html_content
            )
            
            if template_id and template_data:
                message.template_id = template_id
                message.dynamic_template_data = template_data
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ Email send failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            return False
    
    # =============================================
    # TEMPLATED EMAILS
    # =============================================
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1D4241; padding: 20px; text-align: center;">
                <h1 style="color: white;">🏛️ Welcome to MInT</h1>
            </div>
            <div style="padding: 30px;">
                <h2>Hello {user_name},</h2>
                <p>Welcome to the <strong>MInT Innovation Management Platform</strong>!</p>
                <p>You are now part of an ecosystem that connects innovators, mentors, investors, and the Ministry of Innovation & Technology.</p>
                <h3>What you can do:</h3>
                <ul>
                    <li>✅ Submit your startup for evaluation</li>
                    <li>✅ Get AI-powered feedback and scoring</li>
                    <li>✅ Apply for funding and grants</li>
                    <li>✅ Connect with mentors</li>
                    <li>✅ Track your progress</li>
                </ul>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>📧 Your Email:</strong> {user_email}</p>
                    <p><strong>🔑 Role:</strong> {user_name.split()[-1] if len(user_name.split()) > 1 else 'User'}</p>
                </div>
                <p>If you have any questions, please contact us at <a href="mailto:support@mint.gov">support@mint.gov</a></p>
                <p>Best regards,<br><strong>MInT Innovation Team</strong></p>
            </div>
            <div style="background: #1D4241; padding: 20px; text-align: center; color: white;">
                <p style="font-size: 12px;">&copy; 2024 Ministry of Innovation & Technology</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(
            to_email=user_email,
            subject="🏛️ Welcome to MInT Innovation Platform!",
            html_content=html_content,
            to_name=user_name
        )
    
    def send_funding_approved_email(self, user_email: str, user_name: str, 
                                     startup_name: str, amount: float, request_id: str) -> bool:
        """Send funding approval email"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #00C853; padding: 20px; text-align: center;">
                <h1 style="color: white;">✅ Funding Approved!</h1>
            </div>
            <div style="padding: 30px;">
                <h2>Dear {user_name},</h2>
                <p>We are pleased to inform you that your funding request for <strong>{startup_name}</strong> has been <strong>APPROVED</strong>!</p>
                <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; border-left: 4px solid #00C853;">
                    <p><strong>💰 Approved Amount:</strong> ${amount:,.2f}</p>
                    <p><strong>📋 Request ID:</strong> {request_id}</p>
                    <p><strong>📅 Date:</strong> {__import__('datetime').datetime.utcnow().strftime('%B %d, %Y')}</p>
                </div>
                <h3>Next Steps:</h3>
                <ol>
                    <li>📄 Review and sign the funding agreement</li>
                    <li>🏦 Provide your bank account details</li>
                    <li>🤝 Meet with your assigned mentor</li>
                    <li>📊 Submit monthly progress reports</li>
                </ol>
                <p>Our team will contact you within 48 hours to guide you through the process.</p>
                <p>Best regards,<br><strong>MInT Funding Team</strong></p>
            </div>
            <div style="background: #1D4241; padding: 20px; text-align: center; color: white;">
                <p style="font-size: 12px;">&copy; 2024 Ministry of Innovation & Technology</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(
            to_email=user_email,
            subject=f"✅ Funding Approved for {startup_name}!",
            html_content=html_content,
            to_name=user_name
        )
    
    def send_funding_rejected_email(self, user_email: str, user_name: str,
                                     startup_name: str, reason: str) -> bool:
        """Send funding rejection email"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #F44336; padding: 20px; text-align: center;">
                <h1 style="color: white;">📋 Funding Request Update</h1>
            </div>
            <div style="padding: 30px;">
                <h2>Dear {user_name},</h2>
                <p>Thank you for your funding request for <strong>{startup_name}</strong>.</p>
                <p>After careful review, we are unable to approve your request at this time.</p>
                <div style="background: #ffebee; padding: 15px; border-radius: 5px; border-left: 4px solid #F44336;">
                    <p><strong>📋 Reason:</strong></p>
                    <p>{reason}</p>
                </div>
                <h3>What you can do:</h3>
                <ul>
                    <li>📝 Address the issues identified</li>
                    <li>🔄 Resubmit with improvements</li>
                    <li>🤝 Schedule a consultation with our team</li>
                </ul>
                <p>We encourage you to reapply after addressing the feedback.</p>
                <p>Best regards,<br><strong>MInT Funding Team</strong></p>
            </div>
            <div style="background: #1D4241; padding: 20px; text-align: center; color: white;">
                <p style="font-size: 12px;">&copy; 2024 Ministry of Innovation & Technology</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(
            to_email=user_email,
            subject=f"📋 Funding Request Update for {startup_name}",
            html_content=html_content,
            to_name=user_name
        )
    
    def send_grant_approved_email(self, user_email: str, user_name: str,
                                   grant_name: str, amount: float) -> bool:
        """Send grant approval email"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2196F3; padding: 20px; text-align: center;">
                <h1 style="color: white;">🎯 Grant Approved!</h1>
            </div>
            <div style="padding: 30px;">
                <h2>Dear {user_name},</h2>
                <p>Congratulations! Your application for <strong>{grant_name}</strong> has been <strong>APPROVED</strong>!</p>
                <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196F3;">
                    <p><strong>💰 Amount:</strong> ${amount:,.2f}</p>
                    <p><strong>📅 Date:</strong> {__import__('datetime').datetime.utcnow().strftime('%B %d, %Y')}</p>
                </div>
                <h3>Next Steps:</h3>
                <ol>
                    <li>📄 Accept the grant terms</li>
                    <li>📊 Submit project plan</li>
                    <li>📈 Start your project</li>
                </ol>
                <p>Best regards,<br><strong>MInT Grants Team</strong></p>
            </div>
            <div style="background: #1D4241; padding: 20px; text-align: center; color: white;">
                <p style="font-size: 12px;">&copy; 2024 Ministry of Innovation & Technology</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(
            to_email=user_email,
            subject=f"🎯 Grant Approved: {grant_name}",
            html_content=html_content,
            to_name=user_name
        )
    
    def send_mentor_assigned_email(self, user_email: str, user_name: str,
                                    mentor_name: str, mentor_expertise: str) -> bool:
        """Send mentor assignment email"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #FF9800; padding: 20px; text-align: center;">
                <h1 style="color: white;">🤝 Mentor Assigned!</h1>
            </div>
            <div style="padding: 30px;">
                <h2>Dear {user_name},</h2>
                <p>We are excited to inform you that <strong>{mentor_name}</strong> has been assigned as your mentor!</p>
                <div style="background: #fff3e0; padding: 15px; border-radius: 5px; border-left: 4px solid #FF9800;">
                    <p><strong>👨‍🏫 Mentor:</strong> {mentor_name}</p>
                    <p><strong>🔬 Expertise:</strong> {mentor_expertise}</p>
                </div>
                <h3>What to expect:</h3>
                <ul>
                    <li>📅 Weekly mentorship sessions</li>
                    <li>📋 Guidance on your startup</li>
                    <li>🤝 Introductions to industry contacts</li>
                    <li>📈 Strategic advice</li>
                </ul>
                <p>Your mentor will contact you within 48 hours to schedule your first session.</p>
                <p>Best regards,<br><strong>MInT Mentorship Team</strong></p>
            </div>
            <div style="background: #1D4241; padding: 20px; text-align: center; color: white;">
                <p style="font-size: 12px;">&copy; 2024 Ministry of Innovation & Technology</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(
            to_email=user_email,
            subject=f"🤝 Mentor Assigned: {mentor_name}",
            html_content=html_content,
            to_name=user_name
        )
    
    def send_evaluation_complete_email(self, user_email: str, user_name: str,
                                        startup_name: str, score: float, status: str) -> bool:
        """Send evaluation complete email"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #9C27B0; padding: 20px; text-align: center;">
                <h1 style="color: white;">📊 Evaluation Complete</h1>
            </div>
            <div style="padding: 30px;">
                <h2>Dear {user_name},</h2>
                <p>The AI evaluation for <strong>{startup_name}</strong> is now complete!</p>
                <div style="background: #f3e5f5; padding: 15px; border-radius: 5px; border-left: 4px solid #9C27B0;">
                    <p><strong>📊 Overall Score:</strong> {score:.1f}/100</p>
                    <p><strong>📋 Status:</strong> {status}</p>
                </div>
                <p>Please log in to view the full evaluation report including SWOT analysis, risk assessment, and recommendations.</p>
                <p>Best regards,<br><strong>MInT Evaluation Team</strong></p>
            </div>
            <div style="background: #1D4241; padding: 20px; text-align: center; color: white;">
                <p style="font-size: 12px;">&copy; 2024 Ministry of Innovation & Technology</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(
            to_email=user_email,
            subject=f"📊 Evaluation Complete for {startup_name}",
            html_content=html_content,
            to_name=user_name
        )

# Singleton instance
email_service = EmailService()

# Helper functions
def send_welcome_email(user_email: str, user_name: str) -> bool:
    return email_service.send_welcome_email(user_email, user_name)

def send_funding_approved_email(user_email: str, user_name: str, startup_name: str, amount: float, request_id: str) -> bool:
    return email_service.send_funding_approved_email(user_email, user_name, startup_name, amount, request_id)

def send_funding_rejected_email(user_email: str, user_name: str, startup_name: str, reason: str) -> bool:
    return email_service.send_funding_rejected_email(user_email, user_name, startup_name, reason)

def send_grant_approved_email(user_email: str, user_name: str, grant_name: str, amount: float) -> bool:
    return email_service.send_grant_approved_email(user_email, user_name, grant_name, amount)

def send_mentor_assigned_email(user_email: str, user_name: str, mentor_name: str, mentor_expertise: str) -> bool:
    return email_service.send_mentor_assigned_email(user_email, user_name, mentor_name, mentor_expertise)

def send_evaluation_complete_email(user_email: str, user_name: str, startup_name: str, score: float, status: str) -> bool:
    return email_service.send_evaluation_complete_email(user_email, user_name, startup_name, score, status)
