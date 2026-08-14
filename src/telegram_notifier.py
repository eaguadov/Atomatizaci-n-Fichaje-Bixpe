import os
import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_telegram_message(message_text):
    """
    Sends a Markdown-formatted message to Telegram using TELEGRAM_TOKEN and TELEGRAM_CHAT_ID.
    Includes automatic fallback to plain text if Telegram rejects Markdown formatting.
    """
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[Telegram Notifier] TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no configurados en variables de entorno. Omitiendo notificación.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("[Telegram Notifier] Notificación enviada con éxito a Telegram.")
                return True
    except urllib.error.HTTPError as he:
        print(f"[Telegram Notifier] Error HTTP al enviar Markdown ({he.code}). Reintentando como texto plano...")
        # Fallback to plain text if Telegram rejects special Markdown characters like _
        plain_text = message_text.replace("*", "").replace("`", "")
        fallback_payload = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": plain_text
        }).encode("utf-8")
        try:
            req_fb = urllib.request.Request(url, data=fallback_payload)
            with urllib.request.urlopen(req_fb, timeout=10) as resp_fb:
                if resp_fb.status == 200:
                    print("[Telegram Notifier] Notificación enviada con éxito como texto plano.")
                    return True
        except Exception as e_fb:
            print(f"[Telegram Notifier] Error al enviar notificación fallback a Telegram: {e_fb}")
            return False
    except Exception as e:
        print(f"[Telegram Notifier] Error al enviar notificación a Telegram: {e}")
        return False

def send_email_message(subject, message_text):
    """
    Sends an email using Gmail SMTP (smtp.gmail.com:587) with starttls().
    Reads EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECIPIENT.
    Falls back gracefully if sender/recipient aren't explicitly defined.
    """
    sender = os.environ.get("EMAIL_SENDER") or os.environ.get("BIXPE_EMAIL")
    password = os.environ.get("EMAIL_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT") or sender

    if not sender or not password or not recipient:
        print("[Email Notifier] EMAIL_SENDER / BIXPE_EMAIL, EMAIL_PASSWORD o EMAIL_RECIPIENT no configurados. Omitiendo correo.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(message_text, "plain", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print(f"[Email Notifier] Correo electrónico enviado con éxito a {recipient}.")
        return True
    except Exception as e:
        print(f"[Email Notifier] Error al enviar correo electrónico vía SMTP: {e}")
        return False

def dispatch_dual_notification(subject, message_text):
    """Dispatches notifications via both Telegram and Email."""
    tg_status = send_telegram_message(message_text)
    email_status = send_email_message(subject, message_text)
    return tg_status or email_status

def notify_success(action, is_simulation=False):
    action_labels = {
        "START": "Entrada (Inicio de Jornada)",
        "PAUSE": "Pausa para Comer (Inicio)",
        "RESUME": "Reanudación tras Comida",
        "END": "Salida (Fin de Jornada)"
    }
    label = action_labels.get(action, action)
    icon = "🧪" if is_simulation else "✅"
    mode_text = "[MODO SIMULACIÓN]" if is_simulation else ""
    
    subject = f"✅ Fichaje Bixpe Completado {mode_text} - {label}"
    msg = (
        f"{icon} FICHAJE BIXPE COMPLETADO {icon}\n\n"
        f"📌 Acción: {label}\n"
        f"⚙️ Estado: Correcto {mode_text}\n"
        f"🤖 Bot: Automatización Bixpe"
    )
    return dispatch_dual_notification(subject, msg)

def notify_vacation(action=""):
    subject = "🌴 Fichaje Bixpe Omitido - Vacaciones en Curso"
    msg = (
        f"🌴 FICHAJE BIXPE OMITIDO (VACACIONES) 🌴\n\n"
        f"📌 Acción: {action if action else 'Control Horario'}\n"
        f"ℹ️ Detalle: Se detectó 'Vacaciones en curso' en la web de Bixpe.\n"
        f"🏖️ Disfruta de tu descanso."
    )
    return dispatch_dual_notification(subject, msg)

def notify_holiday_or_weekend(reason="Festivo o Fin de semana"):
    subject = f"📅 Fichaje Bixpe Omitido - {reason}"
    msg = (
        f"📅 FICHAJE BIXPE OMITIDO 📅\n\n"
        f"ℹ️ Detalle: Hoy es {reason}. No se requiere fichaje.\n"
        f"😴 Que tengas un buen día de descanso."
    )
    return dispatch_dual_notification(subject, msg)

def notify_error(action, error_detail):
    subject = f"⚠️ ERROR EN FICHAJE BIXPE - {action}"
    msg = (
        f"⚠️ ERROR EN FICHAJE BIXPE ⚠️\n\n"
        f"📌 Acción Intentada: {action}\n"
        f"❌ Detalle del Error: {error_detail}\n"
        f"🔔 Por favor, verifica el estado en la web de Bixpe o en los logs de GitHub Actions."
    )
    return dispatch_dual_notification(subject, msg)
