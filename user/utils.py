from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from dotenv import load_dotenv


def send_password_reset_email(user, request):
    from .models import PasswordResetCode
    code_obj, _ = PasswordResetCode.objects.get_or_create(user=user)
    code_obj.code = get_random_string(length=8)
    code_obj.save()

    domain = request.get_host()
    link = f"http://{domain}/reset-password?code={code_obj.code}"

    message = f"""
    Hello {user.first_name},

    Use the following link and code to reset your password:
    Link: {link}
    Code: {code_obj.code}

    This code will expire in 30 minutes.

    Regards,
    Kuriftu Support Team
    """

    send_mail(
        "Kuriftu - Password Reset",
        message,
        "no-reply@kuriftu.com",
        [user.email],
        fail_silently=False,
    )