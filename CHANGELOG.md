# Historial de Cambios

Todos los cambios notables de este proyecto se documentarán en este archivo.

## [2.0.0] - 2026-08-14

### Añadido
- **Sistema Dual Real de Notificaciones (Telegram + Email SMTP)**:
  - Módulo nativo `src/telegram_notifier.py` que envía notificaciones simultáneas por Telegram y por Correo Electrónico.
  - Integración SMTP directa con Gmail (`smtp.gmail.com:587` con `starttls()`) utilizando contraseñas de aplicación de Google de 16 caracteres.
  - Variables de entorno e inyección de secretos: `EMAIL_SENDER`, `EMAIL_PASSWORD` y `EMAIL_RECIPIENT`.
  - Reintento automático (*fallback*) a texto plano en Telegram si el mensaje contiene caracteres especiales en trazas de error (como `ERR_NAME_NOT_RESOLVED`).
- **Detección Automática de Pantalla de Vacaciones en Bixpe**:
  - El bot analiza el contenido del panel de Bixpe tras el inicio de sesión. Si detecta la notificación *"Vacaciones en curso"*, omite el fichaje sin generar error y envía el aviso `🌴 Fichaje Bixpe Omitido (Vacaciones)`.
- **Detección Estricta de Errores de Login**:
  - Verificación de la URL post-login para asegurar la salida de `auth2.bixpe.com/Account/Login`. Dispara `notify_error` y captura de pantalla `error_login_failed.png` si las credenciales son incorrectas.
- **Flujo de Pruebas Integrado (`TEST Full Cycle (Manual)`)**:
  - Menú desplegable interactivo en GitHub Actions para seleccionar modos de prueba: `full_cycle` (real), `wrong_password` (error de login), `wrong_url` (error de red) y `missing_button` (error de interfaz).
- **Control de Versiones y Etiquetas (Tags)**:
  - Etiqueta de respaldo de seguridad: `backup-pre-alertas`.
  - Etiqueta de versión de lanzamiento: `v2.0.0`.

### Cambiado
- Actualizados todos los flujos `.yml` de GitHub Actions (`clock_in.yml`, `break_start.yml`, `break_end.yml`, `clock_out.yml`, `test_full_cycle.yml`) para inyectar los 7 secretos de entorno.
- Actualizadas las guías `README.md` y `SETUP_GUIA.md` con los manuales completos de configuración de Telegram (vía BotFather y MissRose) y Gmail SMTP (vía App Passwords).

---

## [1.2.0] - 2026-01-22

### Añadido
- **Integración con cron-job.org**: Los workflows ahora se activan externamente mediante cron-job.org en lugar del scheduler interno de GitHub Actions. Esto proporciona mayor puntualidad (1-2 minutos vs 0-60 minutos de retraso).
- **Disparador `repository_dispatch`**: Los workflows aceptan eventos externos vía API de GitHub.
- **Disparador manual `workflow_dispatch`**: Permite ejecutar workflows manualmente desde la interfaz de GitHub.

### Cambiado
- **Eliminación de schedules internos**: Se eliminaron los cron schedules de GitHub Actions para evitar duplicación. Ahora solo cron-job.org dispara los workflows.
- **Selector PAUSE corregido**: Cambiado de `#btn-lunch-pause` a `#btn-pause-lunch` (selector correcto según el HTML de Bixpe).
- **Lógica de confirmación**: START y END requieren confirmación; PAUSE y RESUME no.

### Corregido
- **Comprobación de festivos siempre activa**: Los festivos definidos en `holidays.json` ahora se comprueban siempre, incluso con `--force`. El flag `--force` solo omite la comprobación de horario.

---

## [1.1.0] - 2026-01-21

### Añadido
- **Modo Simulación** (flag `--simulate`): Permite probar el flujo completo sin fichar realmente. El script hace clic en "Cancelar" en los diálogos de confirmación en lugar de "Confirmar".
- **Checklist de Diagnóstico Pre-Clic**: Registra información detallada sobre el estado del botón antes de hacer clic (tipo de etiqueta, visibilidad, dimensiones, detección de overlay).
- **Sondeo del DOM en Fallo**: Cuando no se encuentra un botón, el script lista todos los botones visibles para ayudar a diagnosticar problemas con selectores.

---

## [1.0.0] - 2026-01-18

### Añadido
- Implementación inicial del script de automatización de Bixpe.
- Workflows de GitHub Actions para entrada, inicio-pausa, fin-pausa, salida.
- Funcionalidad de comprobación de festivos.
- Configuración de horarios vía `schedule.json`.
