import os
import urllib.parse
import urllib.request

def send_telegram_message(message_text):
    """
    Sends a Markdown-formatted message to Telegram using TELEGRAM_TOKEN and TELEGRAM_CHAT_ID.
    Uses standard urllib to avoid extra package dependencies.
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
    except Exception as e:
        print(f"[Telegram Notifier] Error al enviar notificación a Telegram: {e}")
        return False

def notify_success(action, is_simulation=False):
    action_labels = {
        "START": "Entrada (Inicio de Jornada)",
        "PAUSE": "Pausa para Comer (Inicio)",
        "RESUME": "Reanudación tras Comida",
        "END": "Salida (Fin de Jornada)"
    }
    label = action_labels.get(action, action)
    icon = "🧪" if is_simulation else "✅"
    mode_text = "*[MODO SIMULACIÓN]*" if is_simulation else ""
    
    msg = (
        f"{icon} *FICHAJE BIXPE COMPLETADO* {icon}\n\n"
        f"📌 *Acción:* {label}\n"
        f"⚙️ *Estado:* Correcto {mode_text}\n"
        f"🤖 *Bot:* Automatización Bixpe"
    )
    return send_telegram_message(msg)

def notify_vacation(action=""):
    msg = (
        f"🌴 *FICHAJE BIXPE OMITIDO (VACACIONES)* 🌴\n\n"
        f"📌 *Acción:* {action if action else 'Control Horario'}\n"
        f"ℹ️ *Detalle:* Se detectó 'Vacaciones en curso' en Bixpe.\n"
        f"🏖️ Disfruta de tu descanso."
    )
    return send_telegram_message(msg)

def notify_holiday_or_weekend(reason="Festivo o Fin de semana"):
    msg = (
        f"📅 *FICHAJE BIXPE OMITIDO* 📅\n\n"
        f"ℹ️ *Detalle:* Hoy es {reason}. No se requiere fichaje.\n"
        f"😴 Que tengas un buen día de descanso."
    )
    return send_telegram_message(msg)

def notify_error(action, error_detail):
    msg = (
        f"⚠️ *ERROR EN FICHAJE BIXPE* ⚠️\n\n"
        f"📌 *Acción Intentada:* {action}\n"
        f"❌ *Detalle del Error:* {error_detail}\n"
        f"🔔 Por favor, verifica el estado en la web de Bixpe o en GitHub Actions."
    )
    return send_telegram_message(msg)
