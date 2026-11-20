from home.models import ChangePasswordToken


def generate_change_password_token(email):
    token = ChangePasswordToken.objects.create(email=email)
    return token.token
