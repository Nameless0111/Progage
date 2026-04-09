from django.core.mail import get_connection, EmailMessage
from django.conf import settings

_connection = None

def get_smtp_connection():
    global _connection
    if _connection is None:
        _connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            fail_silently=False,
        )
        _connection.open()  # открываем один раз
    return _connection


def send_email(subject, body, to):
    connection = get_smtp_connection()

    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to],
        connection=connection,
    )

    email.send()
