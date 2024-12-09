from django.conf import settings
from django.core.mail import send_mail
import os

import structlog

logger = structlog.get_logger("base.mails")


def send_alyx_mail(to, subject, text=""):
    if settings.DISABLE_MAIL or os.getenv("DISABLE_MAIL", None):
        logger.warning("Mails are disabled by DISABLE_MAIL.")
        return
    if not to:
        return
    if to and not isinstance(to, (list, tuple)):
        to = [to]
    to = [_ for _ in to if _]
    if not to:
        return
    text += "\n\n--\nMessage sent automatically - please do not reply."
    try:
        send_mail(
            "[alyx] " + subject,
            text,
            settings.SUBJECT_REQUEST_EMAIL_FROM,
            to,
            fail_silently=True,
        )
        logger.info("Mail sent to %s.", ", ".join(to))
        return True
    except Exception as e:
        logger.warning("Mail failed: %s", e)
        return False
