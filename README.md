# Automatización Fichaje Bixpe v2.0.0 🚀

Script de automatización para fichar entrada/salida y pausas en la plataforma **Bixpe Control Horario**, equipado con un **Sistema Dual de Notificaciones en Tiempo Real (Telegram + Correo Electrónico SMTP)**.

---

## 📌 Arquitectura y Flujo Lógico del Sistema

```mermaid
flowchart TD
    %% Estilos
    classDef telegram fill:#0088cc,stroke:#fff,stroke-width:2px,color:#fff;
    classDef alert fill:#dc3545,stroke:#fff,stroke-width:2px,color:#fff;
    classDef success fill:#2ea043,stroke:#fff,stroke-width:2px,color:#fff;
    classDef hc fill:#28a745,stroke:#fff,stroke-width:2px,color:#fff;

    A([🕒 cron-job.org dispara a su hora]) --> B[🐙 GitHub Actions Inicia]

    subgraph GITHUB [Servidor de GitHub Actions]
        B --> C{¿Festivo o Finde?}
        C -- Sí --> D[Omitir acción]
        C -- No --> E[Python abre Bixpe]

        E --> F{¿Falla Web o Login?}
        F -- Sí --> G[📱 Telegram: ERROR BIXPE]:::telegram
        F -- No --> H{¿Cartel Vacaciones?}

        H -- Sí --> I[📱 Telegram: AVISO VACACIONES]:::telegram
        H -- No --> J[Script pulsa botón Fichar]

        J --> K{¿Fichaje OK?}
        K -- No --> G
        K -- Sí --> L{¿NOTIFICAR_EXITOS?}

        L -- "true" --> M[📱 Telegram: Fichaje Correcto]:::telegram
        L -- "false" --> N[🔇 Modo Silencioso]

        %% Convergencia al paso final Always
        D --> P[🌐 Enviar PING a Healthchecks <br><i>(Paso Always: se envía siempre que GitHub corra)</i>]
        G --> P
        I --> P
        M --> P
        N --> P
    end

    subgraph HEALTHCHECKS [El Vigilante Externo: Healthchecks.io]
        P -.->|Señal recibida a tiempo| HC_OK([🟢 Todo en orden: La infraestructura funcionó]):::hc
        HC_WAIT((⏳ Reloj esperando 10 min)) -.->|Pasa el tiempo sin señal <br><i>(Caída total de CronJob o GitHub)</i>| HC_ERR[📱 Telegram: ALARMA CAÍDA TOTAL]:::alert
    end
```

1. **cron-job.org**: Dispara la ejecución del workflow a la hora programada mediante la API de GitHub.
2. **GitHub Actions**: Ejecuta el script automatizado en Python con Playwright Chromium en modo *headless*.
3. **Bot Bixpe**: Realiza el inicio de sesión, verifica el estado (trabajo, festivo o vacaciones) y efectúa el fichaje.
4. **Sistema de Alertas Duales y Silenciosas**: Envía notificaciones de error/éxito por **Telegram** y **Correo Electrónico (Gmail SMTP)** según la configuración del usuario.
5. **Healthchecks.io (Vigilante)**: Monitoriza que la cadena se ejecute puntualmente y envía una alarma crítica si el disparador o GitHub sufren una caída.

---

## ✨ Características de la Versión 2.0.2

- ✅ **Fichaje Automático Completo**: Entrada (`START`), Inicio Pausa (`PAUSE`), Fin Pausa (`RESUME`) y Salida (`END`).
- 🔔 **Sistema Dual Real de Alertas**: Notificaciones coordinadas por Telegram (Markdown) y Email (Gmail SMTP `starttls`).
- 🤫 **Modo Silencioso y Monitorización**: Integración con Healthchecks.io para omitir notificaciones de éxito diarias, alertando por Telegram únicamente si hay errores o fallos en la infraestructura.
- 🌴 **Detección Automática de Vacaciones**: Reconoce la pantalla *"Vacaciones en curso"* de Bixpe, omite el fichaje y envía aviso de tranquilidad sin generar errores.
- 📅 **Control de Festivos y Fines de Semana**: Omisión automática de días festivos (`team_holidays.json`) y fines de semana.
- 🛡️ **Prevención de Falsos Positivos**: Triple mecanismo de espera (`networkidle` + espera dinámica de elementos + `wait_for_url`) para asegurar la verificación del estado real.
- 🧪 **Suite de Pruebas y Diagnóstico de Errores**: Permite simular escenarios de prueba (ciclo completo, contraseña incorrecta, error de red o cambios de interfaz) directamente desde GitHub Actions.

---

## ⚙️ Configuración de Secretos y Variables en GitHub Actions

En **Settings > Secrets and variables > Actions**:

### 🔒 Secrets del Repositorio
| Secret | Descripción | Requerido para |
|--------|-------------|----------------|
| `BIXPE_EMAIL` | Email de acceso a Bixpe | Fichaje |
| `BIXPE_PASSWORD` | Contraseña de acceso a Bixpe | Fichaje |
| `TELEGRAM_TOKEN` | Token del Bot creado en `@BotFather` | Notificaciones Telegram |
| `TELEGRAM_CHAT_ID` | ID numérico de chat privado de Telegram | Notificaciones Telegram |
| `EMAIL_SENDER` | Dirección de Gmail emisora | Notificaciones Email |
| `EMAIL_PASSWORD` | Contraseña de Aplicación de 16 letras de Google | Notificaciones Email |
| `EMAIL_RECIPIENT` | Dirección de correo receptora de los avisos | Notificaciones Email |
| `HC_URL_START` | *(Opcional)* URL de ping de Healthchecks para Entrada | Vigilante Healthchecks |
| `HC_URL_PAUSE` | *(Opcional)* URL de ping de Healthchecks para Inicio Pausa | Vigilante Healthchecks |
| `HC_URL_RESUME` | *(Opcional)* URL de ping de Healthchecks para Fin Pausa | Vigilante Healthchecks |
| `HC_URL_END` | *(Opcional)* URL de ping de Healthchecks para Salida | Vigilante Healthchecks |

### 🎛️ Variables de Repositorio (Opcionales / Personalización)

Configúralas en **Settings > Secrets and variables > Actions > Variables**:

| Variable | Descripción | Valor por defecto | Ejemplo |
|----------|-------------|-------------------|---------|
| `NOTIFICAR_EXITOS` | Si se establece en `false`, suprime los avisos diarios de Telegram cuando todo va bien (modo silencioso). | `true` | `false` |
| `EMPLEADO` | Nombre del empleado (tal como figura en el Excel de la empresa). Permite sincronizar automáticamente festivos y vacaciones desde el calendario maestro `team_holidays.json`. | *(vacío / no se verifican festivos)* | `Eusebio` o `Antonio` |

---

## 🏖️ Sincronización Automática de Vacaciones (Excel -> GitHub)

El repositorio incluye un sistema para sincronizar las vacaciones de todo el equipo directamente desde el Excel corporativo:
* **`Actualizar_Vacaciones.bat`**: Lanzador para Windows (doble clic). Lee el Excel de la unidad compartida y actualiza el archivo maestro en GitHub.
* **`team_holidays.json`**: Archivo maestro centralizado con el calendario de todo el equipo etiquetado (`V`, `V25`, `FL`, `FA`, `F`).
* **Compañeros / Forks**: Solo deben configurar su variable `EMPLEADO` con su nombre exacto en GitHub y sincronizar su fork. El bot leerá los festivos en tiempo real.

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
| `team_holidays.json` | Calendario maestro centralizado de festivos y vacaciones del equipo |
| `schedule.json` | Configuración de horarios por tipo de jornada |
| `Actualizar_Vacaciones.bat` | Lanzador Windows (doble clic) para sincronizar el Excel con GitHub |
| `scripts/actualizar_vacaciones.py` | Script que lee el Excel corporativo y genera `team_holidays.json` |
| `.github/workflows/` | Flujos de trabajo de GitHub Actions |
| `SETUP_GUIA.md` | Guía completa paso a paso para usuarios y forks |
| `CHANGELOG.md` | Historial de versiones del proyecto |

---

## 📜 Licencia

Este proyecto está bajo la Licencia **MIT**.
