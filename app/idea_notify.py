"""Tell an innovator when an admin decides on their idea (in-app bell + email).
Best-effort only: nothing here raises, so it can never block a review."""
import logging
from html import escape
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

logger = logging.getLogger(__name__)

REASON_LABELS = {
    'duplicate': 'Duplicate idea',
    'plagiarism': 'Plagiarism',
    'harmful_content': 'Illegal or harmful content',
    'incomplete': 'Incomplete submission',
    'not_feasible': 'Not feasible',
    'out_of_scope': 'Out of scope',
    'low_impact': 'Low impact',
    'other': 'Other',
}

# decision -> (bell title, email heading, header colour, intro sentence)
DECISIONS = {
    'approved': ('Idea approved', 'Your idea was approved', '#2E7D32',
                 'Congratulations! Your idea has been approved.'),
    'revision_requested': ('Revision requested', 'Revision requested', '#F9A825',
                           'The reviewer asks you to improve your idea and resubmit.'),
    'rejected': ('Idea not approved', 'Update on your idea', '#F44336',
                 'After careful review, we are unable to approve your idea at this time.'),
}


def attach_owner(idea):
    """Remember who submitted the idea, only when a valid login token is sent."""
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid:
            idea['owner_id'] = str(uid)
    except Exception as exc:
        logger.warning('attach_owner failed: %s', exc)


def notify_idea_decision(idea):
    try:
        owner_id = idea.get('owner_id')
        if not owner_id:
            return  # older ideas have no owner, so nobody to notify
        review = idea.get('review') or {}
        decision = review.get('decision') or idea.get('status')
        if decision not in DECISIONS:
            return
        bell_title, heading, colour, intro = DECISIONS[decision]
        title = idea.get('title') or 'your idea'
        comment = (review.get('comment') or '').strip()
        label = REASON_LABELS.get(review.get('reason_code')) if decision == 'rejected' else None
        reason = f'{label}: {comment}' if label and comment else (label or comment)

        # 1) In-app notification (the bell cuts the text at 300 characters)
        try:
            from app.notifications import notify
            message = f'"{title}". {reason}' if reason else f'"{title}"'
            notify(owner_id, bell_title, message, '/idea-submission')
        except Exception as exc:
            logger.warning('idea notification failed: %s', exc)

        # 2) Email with the full reason
        try:
            from app.admin_guard import _find_user
            from app.email import email_service
            user = _find_user(str(owner_id))
            to_email = user.get('email') if user else None
            if not to_email:
                return
            name = (user.get('name') or user.get('full_name')
                    or user.get('first_name') or 'Innovator')
            reason_html = ''
            if reason:
                reason_html = (
                    '<div style="background:#f5f5f5;padding:15px;border-radius:5px;'
                    f'border-left:4px solid {colour};"><p><strong>Reviewer\'s reason:</strong></p>'
                    f'<p>{escape(reason)}</p></div>'
                )
            html = f"""
            <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <div style="background:{colour}; padding:20px; text-align:center;">
                <h1 style="color:white;">{escape(heading)}</h1>
              </div>
              <div style="padding:30px;">
                <h2>Dear {escape(str(name))},</h2>
                <p>Your idea <strong>{escape(title)}</strong> has been reviewed.</p>
                <p>{escape(intro)}</p>
                {reason_html}
                <p>You can see your ideas on the MInT Innovation Incubator Platform.</p>
                <p>Best regards,<br><strong>MInT Innovation Incubator</strong></p>
              </div>
            </body></html>
            """
            email_service.send_email(to_email=to_email, subject=f'{bell_title}: {title}',
                                     html_content=html, to_name=str(name))
        except Exception as exc:
            logger.warning('idea decision email failed: %s', exc)
    except Exception as exc:
        logger.warning('notify_idea_decision failed: %s', exc)
