"""In-app notifications. notify() never raises, so it can't break a request."""
import logging
import uuid
from datetime import datetime
from app.database import get_collection, USERS_COLLECTION

logger = logging.getLogger(__name__)


def notify(user_id, title, message='', link=None):
    try:
        coll = get_collection('notifications')
        if coll is None or not user_id:
            return
        coll.insert_one({'_id': str(uuid.uuid4()), 'user_id': user_id, 'title': str(title)[:120],
                         'message': str(message)[:300], 'link': link, 'read': False,
                         'created_at': datetime.utcnow().isoformat()})
    except Exception as exc:
        logger.warning('notify failed: %s', exc)


def notify_admins(title, message='', link=None):
    try:
        users = get_collection(USERS_COLLECTION)
        if users is None:
            return
        for u in users.find({'role': 'admin', 'status': 'active'}):
            notify(u['_id'], title, message, link)
    except Exception as exc:
        logger.warning('notify_admins failed: %s', exc)
