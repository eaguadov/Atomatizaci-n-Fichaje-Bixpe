# Guía de Configuración Completa - Automatización Fichaje Bixpe v2.0.0

Esta guía te permitirá configurar tu propia automatización de fichaje en Bixpe con el **sistema dual de alertas en tiempo real por Telegram y Correo Electrónico (Gmail SMTP)**.

---

## 📋 Requisitos Previos

- Cuenta activa en **Bixpe Control Horario** (email y contraseña).
- Cuenta de **GitHub** (gratuita).
- Cuenta de **Telegram** (para recibir alertas instantáneas).
- Cuenta de **Gmail** con Verificación en dos pasos (para recibir notificaciones por correo).
- Cuenta en **cron-job.org** (gratuita, para disparar los fichajes puntualmente).

---

## 🚀 Paso 1: Crear cuenta y hacer Fork en GitHub

1. Entra en [https://github.com/signup](https://github.com/signup) y crea tu cuenta.
2. Ve al repositorio principal: [https://github.com/eaguadov/Atomatizaci-n-Fichaje-Bixpe](https://github.com/eaguadov/Atomatizaci-n-Fichaje-Bixpe).
3. Haz clic en el botón **"Fork"** (arriba a la derecha).
4. Mantén el nombre y pulsa **"Create fork"**.

Ahora tienes tu propia copia en: `https://github.com/TU_USUARIO/Atomatizaci-n-Fichaje-Bixpe`

---

## 🔑 Paso 2: Configurar los 7 Secrets en GitHub

Los *Secrets* almacenan tus credenciales e integraciones de forma segura.

1. Ve a tu fork: `https://github.com/TU_USUARIO/Atomatizaci-n-Fichaje-Bixpe`.
2. Haz clic en **Settings** → **Secrets and variables** → **Actions**.
3. Haz clic en **"New repository secret"** para cada uno de los 7 secretos listados a continuación:

### Tabla de Secrets de GitHub Actions

| Nombre del Secret | Descripción | Ejemplo / Formato |
|-------------------|-------------|-------------------|
| `BIXPE_EMAIL` | Tu correo electrónico de acceso a Bixpe | `usuario@empresa.com` |
| `BIXPE_PASSWORD` | Tu contraseña de Bixpe | `MiPassword123` |
| `TELEGRAM_TOKEN` | Token del Bot creado con BotFather | `123456789:ABCdefGHIjklMNOpqrs` |
| `TELEGRAM_CHAT_ID` | Tu ID numérico de chat de Telegram | `987654321` |
| `EMAIL_SENDER` | Dirección de Gmail desde la que se enviará el correo | `tu_correo@gmail.com` |
| `EMAIL_PASSWORD` | Contraseña de Aplicación de 16 letras de Google | `abcd efgh ijkl mnop` |
| `EMAIL_RECIPIENT` | Dirección de correo donde quieres recibir los avisos | `tu_correo@gmail.com` |

---

## 📲 Paso 3: Configuración de Notificaciones por Telegram

Sigue estos 3 sencillos pasos para crear tu Bot y vincularlo:

### 3.1. Crear el Bot en Telegram
1. En Telegram, busca al usuario oficial verificado **`@BotFather`** e inicia el chat.
2. Envía el comando `/newbot`.
3. Asignale un nombre y un nombre de usuario (debe terminar en `bot`, ej: `MiFichajeBixpe_bot`).
4. **Copia el Token** que te proporciona BotFather (ej: `123456789:ABC...`). Este es tu **`TELEGRAM_TOKEN`**.

### 3.2. Obtener tu Chat ID (Método oficial y privado)
1. **IMPORTANTE**: Busca tu propio bot recién creado (ej: `@MiFichajeBixpe_bot`) e inicia el chat pulsando **Iniciar** o enviándole un mensaje inicial (ej: `Hola`). Esto es indispensable para que tu bot tenga permiso para enviarte mensajes.
2. Abre tu navegador web y accede a la siguiente URL, reemplazando `<TELEGRAM_TOKEN>` por el token largo que te dio BotFather en el paso anterior:
   ```text
   https://api.telegram.org/bot<TELEGRAM_TOKEN>/getUpdates
   ```
3. En la respuesta en pantalla (formato JSON), busca el fragmento `"chat"` o `"from"`. Verás un campo `"id"` con un número (ej: `987654321`). Ese número de 9 o 10 dígitos es tu **`TELEGRAM_CHAT_ID`**.

> 💡 *Nota: Si la página web se muestra vacía (`{"ok":true,"result":[]}`), es porque no has enviado el mensaje de saludo a tu bot en el Paso 1. Envíale un mensaje, refresca la página de la API y aparecerá.*

#### Método Alternativo (Bot de terceros):
Puedes buscar al bot **`@MissRose_bot`** en Telegram, iniciar un chat con ella y enviarle el comando `/id`. Ella te devolverá tu número de ID.
*⚠️ **Advertencia de privacidad:** Al interactuar con bots de terceros como MissRose, estás compartiendo tus metadatos (ID de usuario, nombre y mensajes) con sus servidores externos. El método oficial a través de la API (`getUpdates`) es 100% privado y seguro.*

### 3.3. Guardar los Secretos en GitHub
Añade `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID` en la sección **Settings > Secrets and variables > Actions** de tu repositorio.

---

## 📧 Paso 4: Configuración de Notificaciones por Email (Gmail SMTP)

Para que Gmail permita enviar correos automáticos por el puerto seguro 587 (SMTP `starttls`), debes generar una contraseña de aplicación:

### 4.1. Generar la Contraseña de Aplicación en Google
1. Inicia sesión en tu cuenta de Google (debe tener la **Verificación en dos pasos** activada).
2. Accede directamente al panel de contraseñas de aplicaciones de Google: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Escribe un nombre identificativo (por ejemplo: `GitHub Bixpe Bot`) y pulsa en **Crear**.
4. **Copia el código de 16 letras** que aparecerá en pantalla (ej: `abcd efgh ijkl mnop`).

### 4.2. Guardar los Secrets en GitHub
Añade en **Settings > Secrets and variables > Actions** de GitHub:
- `EMAIL_SENDER`: Tu dirección de Gmail.
- `EMAIL_PASSWORD`: Las 16 letras de la contraseña de aplicación sin espacios.
- `EMAIL_RECIPIENT`: La dirección de correo donde quieres recibir las alertas.

---

## ⏰ Paso 5: Configurar los Cron Jobs en cron-job.org

Para que el fichaje se ejecute con máxima puntualidad (~1 minuto de precisión), se utiliza [cron-job.org](https://cron-job.org).

### 5.1. Crear Personal Access Token (PAT) en GitHub
1. Ve a: [https://github.com/settings/tokens](https://github.com/settings/tokens).
2. Haz clic en **Generate new token (classic)**.
3. Nombre: `cron-job-bixpe`. Marca solo el scope **`repo`**.
4. Copia el token generado (`ghp_...`).

### 5.2. Configuración en cron-job.org
Crea **6 jobs** en cron-job.org apuntando a la URL de tu repositorio:
```text
https://api.github.com/repos/TU_USUARIO/Atomatizaci-n-Fichaje-Bixpe/dispatches
```

**Configuración común (Pestaña ADVANCED):**
- **Request Method**: `POST`
- **Headers**:
  - `Authorization`: `Bearer ghp_TU_TOKEN_PAT`
  - `Accept`: `application/vnd.github.v3+json`
  - `Content-Type`: `application/json`

**Los 6 Jobs a crear:**

| Job | Días | Hora | Body JSON |
|-----|------|------|-----------|
| Clock In (L-J) | Lun, Mar, Mié, Jue | 08:30 | `{"event_type": "clock_in"}` |
| Clock In (V) | Vie | 08:00 | `{"event_type": "clock_in"}` |
| Break Start (L-J) | Lun, Mar, Mié, Jue | 14:00 | `{"event_type": "break_start"}` |
| Break End (L-J) | Lun, Mar, Mié, Jue | 15:00 | `{"event_type": "break_end"}` |
| Clock Out (L-J) | Lun, Mar, Mié, Jue | 18:00 | `{"event_type": "clock_out"}` |
| Clock Out (V) | Vie | 14:00 | `{"event_type": "clock_out"}` |

---

## 🌴 Paso 6: Gestión de Vacaciones y Festivos

### Días de Vacaciones / Festivos Locales (`team_holidays.json`)
Los festivos y vacaciones de todo el equipo se gestionan de forma centralizada a través del archivo maestro `team_holidays.json`. Consulta el **Paso 8** para configurar tu variable `EMPLEADO` y recibir automáticamente los días libres desde el calendario corporativo.

### Vacaciones Registradas en la Web de Bixpe
Si estás de vacaciones y Bixpe muestra el mensaje *"Vacaciones en curso"*, el bot lo detecta automáticamente, omite el fichaje sin dar error y te envía una notificación de tranquilidad: `🌴 Fichaje Bixpe Omitido (Vacaciones)`.

## 🤫 Paso 7: Modo Silencioso y Vigilante de Caídas (Opcional)

Si deseas recibir alertas **sólo cuando hay un error** y evitar los mensajes de éxito diarios:

1. Ve a **Settings > Secrets and variables > Actions > Variables** (Ojo, pestaña *Variables*, no Secrets).
2. Crea una variable llamada `NOTIFICAR_EXITOS` y ponle el valor `false`.

**Monitorización de Infraestructura (Healthchecks.io)**
Al silenciar los éxitos, necesitas asegurarte de que el sistema se está ejecutando (por si falla GitHub o cron-job). Para ello, integramos un "vigilante":
1. Crea una cuenta gratuita en [Healthchecks.io](https://healthchecks.io) y vincula tu Telegram en la pestaña *Integrations*.
2. Crea 4 Checks (Entrada, Inicio Pausa, Fin Pausa, Salida) configurados con tu horario y 10 minutos de gracia.
3. Copia sus *Ping URLs* únicas.
4. Añádelas como **Secrets** en tu repositorio GitHub con estos nombres exactos:
   - `HC_URL_START`
   - `HC_URL_PAUSE`
   - `HC_URL_RESUME`
   - `HC_URL_END`

De esta forma, si el fichaje va bien, el bot guardará silencio en Telegram, pero enviará un toque interno a Healthchecks. Si el bot ni siquiera llega a arrancar o se cae internet, Healthchecks se dará cuenta y te avisará por Telegram.

---

## 🏖️ Paso 8: Sincronización Automática de Vacaciones del Equipo

El proyecto cuenta con un calendario maestro centralizado (`team_holidays.json`) sincronizado con el Excel corporativo. Para activarlo en tu fork:

1. Ve a **Settings > Secrets and variables > Actions > Variables**.
2. Crea una nueva variable llamada **`EMPLEADO`**.
3. En el valor, escribe tu nombre **exactamente** como aparece en el Excel de la empresa (por ejemplo: `Antonio`, `Carlos`, `Oscar`, `Eusebio`).

**¿Cómo actualizar las vacaciones? (Tienes 2 opciones):**
* **Opción A (Autónoma - Lanzador en tu PC):** Si clonas el repositorio en tu ordenador del trabajo, puedes hacer doble clic en **`Actualizar_Vacaciones.bat`** (o crearle un acceso directo en tu escritorio). El script leerá el Excel de la empresa y actualizará tu propio repositorio de GitHub al instante.
* **Opción B (Sin instalar nada - Sync Fork):** Cuando el responsable del proyecto actualice el calendario global, solo tienes que entrar a tu GitHub y pulsar el botón **"Sync Fork" > "Update branch"**.

El bot consultará automáticamente tu lista de días libres antes de fichar y cancelará la jornada cuando estés de descanso o festivo.

---

## 🧪 Paso 9: Pruebas Manuales y Simulación de Errores

Puedes realizar pruebas manuales directamente desde la interfaz web de GitHub Actions:

1. Ve a la pestaña **Actions** en tu repositorio.
2. Selecciona **`TEST Full Cycle (Manual)`**.
3. Haz clic en **Run workflow**, elige la rama `main` y selecciona el **Modo de prueba**:
   - 🟢 `full_cycle`: Fichaje real (Entrada -> Pausa -> Fin Pausa -> Salida).
   - 🔴 `wrong_password`: Simula contraseña incorrecta para verificar la alerta de error.
   - 🔴 `wrong_url`: Simula fallo de red / servidor no disponible.
   - 🔴 `missing_button`: Simula cambio de interfaz o botón no encontrado.

---

## ❓ Solución de Problemas Frecuentes

| Síntoma | Causa Probable | Solución |
|---------|----------------|----------|
| Telegram no recibe mensajes | `TELEGRAM_TOKEN` o `CHAT_ID` mal puestos o bot no saludado | Revisa los secrets y asegúrate de haber enviado un `/start` o saludo a tu bot en Telegram. |
| Email da error `535 Bad Credentials` | Se introdujo la contraseña habitual de Gmail en lugar de la Contraseña de Aplicación | Genera una contraseña de aplicación de 16 letras en [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). |
| Error 401 en cron-job.org | Token PAT de GitHub caducado o mal copiado | Revisa la cabecera `Authorization: Bearer ghp_...` en cron-job.org. |
