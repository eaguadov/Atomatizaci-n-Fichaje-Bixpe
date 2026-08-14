# Automatización Fichaje Bixpe v2.0.0 🚀

Script de automatización para fichar entrada/salida y pausas en la plataforma **Bixpe Control Horario**, equipado con un **Sistema Dual de Notificaciones en Tiempo Real (Telegram + Correo Electrónico SMTP)**.

---

## 📌 Arquitectura del Sistema

```text
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   cron-job.org  │ ──▶  │  GitHub Actions │ ──▶  │  Bixpe Platform │ ──▶  │ Telegram & Email│
│  (Disparador)   │      │ (Bot Playwright)│      │    (Fichaje)    │      │ (Notificación)  │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

1. **cron-job.org**: Dispara la ejecución del workflow a la hora programada mediante la API de GitHub.
2. **GitHub Actions**: Ejecuta el script automatizado en Python con Playwright Chromium en modo *headless*.
3. **Bot Bixpe**: Realiza el inicio de sesión, verifica el estado (trabajo, festivo o vacaciones) y efectúa el fichaje.
4. **Sistema Dual de Alertas**: Envía notificaciones al instante por **Telegram** y por **Correo Electrónico (Gmail SMTP)** con el resultado del fichaje o alertas ante cualquier error.

---

## ✨ Características de la Versión 2.0.0

- ✅ **Fichaje Automático Completo**: Entrada (`START`), Inicio Pausa (`PAUSE`), Fin Pausa (`RESUME`) y Salida (`END`).
- 🔔 **Sistema Dual Real de Alertas**: Notificaciones coordinadas por Telegram (Markdown) y Email (Gmail SMTP `starttls`).
- 🌴 **Detección Automática de Vacaciones**: Reconoce la pantalla *"Vacaciones en curso"* de Bixpe, omite el fichaje y envía aviso de tranquilidad sin generar errores.
- 📅 **Control de Festivos y Fines de Semana**: Omisión automática de días festivos (`holidays.json`) y fines de semana.
- 🛡️ **Prevención de Falsos Positivos**: Triple mecanismo de espera (`networkidle` + 10s estabilidad + `wait_for_url`) para asegurar la verificación del estado real.
- 🧪 **Suite de Pruebas y Diagnóstico de Errores**: Permite simular escenarios de prueba (ciclo completo, contraseña incorrecta, error de red o cambios de interfaz) directamente desde GitHub Actions.

---

## ⚙️ Configuración de Secretos en GitHub Actions

Para utilizar el sistema completo, debes añadir los 7 secretos en **Settings > Secrets and variables > Actions**:

| Secret | Descripción | Requerido para |
|--------|-------------|----------------|
| `BIXPE_EMAIL` | Email de acceso a Bixpe | Fichaje |
| `BIXPE_PASSWORD` | Contraseña de acceso a Bixpe | Fichaje |
| `TELEGRAM_TOKEN` | Token del Bot creado en `@BotFather` | Notificaciones Telegram |
| `TELEGRAM_CHAT_ID` | ID de usuario/chat obtenido en `@MissRose_bot` | Notificaciones Telegram |
| `EMAIL_SENDER` | Dirección de Gmail emisora | Notificaciones Email |
| `EMAIL_PASSWORD` | Contraseña de Aplicación de 16 letras de Google | Notificaciones Email |
| `EMAIL_RECIPIENT` | Dirección de correo receptora de los avisos | Notificaciones Email |

---

## 📖 Guía Paso a Paso para Nuevos Usuarios

Si quieres desplegar tu propia copia del sistema, sigue la guía detallada:
👉 **[Guía Completa de Configuración (SETUP_GUIA.md)](SETUP_GUIA.md)**

---

## 💻 Uso Manual y Comandos CLI

Puedes ejecutar el bot manualmente desde consola local:

```bash
# Fichar entrada
python src/bixpe_bot.py --action START --force

# Iniciar pausa comida
python src/bixpe_bot.py --action PAUSE --force

# Finalizar pausa comida
python src/bixpe_bot.py --action RESUME --force

# Fichar salida
python src/bixpe_bot.py --action END --force

# Modo simulación (sin confirmar modal en Bixpe)
python src/bixpe_bot.py --action START --simulate
```

---

## 📁 Estructura del Repositorio

| Archivo / Directorio | Descripción |
|----------------------|-------------|
| `src/bixpe_bot.py` | Script principal de automatización con Playwright |
| `src/telegram_notifier.py` | Módulo de notificaciones duales (Telegram + Gmail SMTP) |
| `holidays.json` | Calendario de días festivos y vacaciones |
| `schedule.json` | Configuración de horarios por tipo de jornada |
| `.github/workflows/` | Flujos de trabajo de GitHub Actions |
| `SETUP_GUIA.md` | Guía completa paso a paso para usuarios y forks |
| `CHANGELOG.md` | Historial de versiones del proyecto |

---

## 📜 Licencia

Este proyecto está bajo la Licencia **MIT**.
