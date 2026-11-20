from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string

def send_permission_email(user):
    subject = 'Cultura Viva Tacima - Permissão de Acervo Concedida'
    html_message = f"""
    <h2>Olá, {user.first_name or user.username}!</h2>
    <p>Você recebeu permissão especial para contribuir com o <strong>Acervo Digital de Tacima</strong>.</p>
    <p>Agora você pode adicionar fotos, vídeos e documentos históricos diretamente pela plataforma.</p>
    <p>Acesse sua conta e confira o menu "Acervo".</p>
    <br>
    <p>Atenciosamente,<br>Equipe Cultura Viva Tacima</p>
    """
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    to = user.email

    try:
        send_mail(subject, plain_message, from_email, [to], html_message=html_message)
    except Exception as e:
        print(f"Erro ao enviar email de permissão: {e}")

def send_artist_status_email(artista, status):
    if status == 'APPROVED':
        subject = 'Cultura Viva Tacima - Cadastro de Artista Aprovado!'
        html_message = f"""
        <h2>Parabéns, {artista.name}!</h2>
        <p>Seu cadastro como Artista/Agente Cultural foi <strong>APROVADO</strong>.</p>
        <p>Seu perfil agora está visível para toda a comunidade na seção de Artistas.</p>
        <br>
        <p>Continue compartilhando sua arte!</p>
        """
    elif status == 'REJECTED':
        subject = 'Cultura Viva Tacima - Atualização sobre seu Cadastro'
        html_message = f"""
        <h2>Olá, {artista.name}.</h2>
        <p>Informamos que seu cadastro como Artista/Agente Cultural precisa de ajustes e não foi aprovado neste momento.</p>
        <p>Entre em contato conosco para entender os motivos ou tente realizar o cadastro novamente com mais detalhes.</p>
        <br>
        <p>Atenciosamente,<br>Equipe Cultura Viva Tacima</p>
        """
    else:
        return

    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    if artista.user and artista.user.email:
         to = artista.user.email
    else:
        # Tenta pegar do contato se não tiver user (caso raro)
        return

    try:
        send_mail(subject, plain_message, from_email, [to], html_message=html_message)
    except Exception as e:
        print(f"Erro ao enviar email de status artista: {e}")

def send_custom_notification_email(user, title, message, action_url=None, action_text=None):
    subject = f'{title} - Cultura Viva Tacima'
    html_message = render_to_string('emails/notification.html', {
        'title': title,
        'message': message,
        'action_url': action_url,
        'action_text': action_text
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    try:
        send_mail(subject, plain_message, from_email, [to], html_message=html_message)
    except Exception as e:
        print(f"Erro ao enviar email de notificação customizada: {e}")

def send_group_status_email(grupo, status):
    if status == 'APPROVED':
        subject = 'Cultura Viva Tacima - Cadastro de Grupo Aprovado!'
        html_message = f"""
        <h2>Parabéns, {grupo.name}!</h2>
        <p>Seu cadastro como Grupo Cultural foi <strong>APROVADO</strong>.</p>
        <p>Seu perfil agora está visível para toda a comunidade na seção de Grupos.</p>
        <br>
        <p>Continue compartilhando sua arte!</p>
        """
    elif status == 'REJECTED':
        subject = 'Cultura Viva Tacima - Atualização sobre seu Cadastro'
        html_message = f"""
        <h2>Olá, {grupo.name}.</h2>
        <p>Informamos que seu cadastro como Grupo Cultural precisa de ajustes e não foi aprovado neste momento.</p>
        <p>Entre em contato conosco para entender os motivos ou tente realizar o cadastro novamente com mais detalhes.</p>
        <br>
        <p>Atenciosamente,<br>Equipe Cultura Viva Tacima</p>
        """
    else:
        return
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    lideres = grupo.get_lideres()
    for lider in lideres:
        if lider and lider.email:
            to = lider.email
            try:
                send_mail(subject, plain_message, from_email, [to], html_message=html_message)
            except Exception as e:
                print(f"Erro ao enviar email de status artista: {e}")
    try:
        send_mail(subject, plain_message, from_email, [to], html_message=html_message)
    except Exception as e:
        print(f"Erro ao enviar email de status artista: {e}")