import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_email(to_email: str, subject: str, html_content: str):
    """
    Envía un correo electrónico usando SMTP de Gmail (o el configurado).
    """
    try:
        sender_email = settings.EMAIL_USER
        password = settings.EMAIL_PASSWORD
        smtp_server = settings.EMAIL_HOST
        smtp_port = int(settings.EMAIL_PORT)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM or sender_email
        message["To"] = to_email

        # Convertir el contenido HTML a objeto MIME
        part = MIMEText(html_content, "html")
        message.attach(part)

        # Conectar al servidor SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() # Seguridad
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, message.as_string())
            
        print(f"✅ Correo enviado a {to_email}")
        return True

    except Exception as e:
        print(f"❌ Error enviando correo a {to_email}: {e}")
        return False

def send_verification_email(to_email: str, code: str):
    subject = "Código de Verificación - AdopPet"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #FF5722;">Bienvenido a AdopPets 🐾</h2>
        <p>Tu código de verificación es:</p>
        <div style="background-color: #f4f4f4; padding: 15px; font-size: 24px; font-weight: bold; text-align: center; border-radius: 8px;">
            {code}
        </div>
        <p>Si no solicitaste este código, ignora este mensaje.</p>
    </div>
    """
    return send_email(to_email, subject, html_content)


def send_password_reset_email(to_email: str, link: str):
    subject = "Recuperar Contraseña - AdopPet"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #FF5722;">Recuperación de Contraseña</h2>
        <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente botón:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="background-color: #FF5722; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Restablecer Contraseña
            </a>
        </div>
        <p>O copia y pega este enlace en tu navegador:</p>
        <p><a href="{link}">{link}</a></p>
        <p>Este enlace expirará pronto.</p>
    </div>
    """
    return send_email(to_email, subject, html_content)
