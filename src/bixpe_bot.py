import os
import sys
import json
import time
import argparse
from datetime import datetime, date
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

try:
    from telegram_notifier import (
        notify_success,
        notify_vacation,
        notify_holiday_or_weekend,
        notify_error
    )
except ImportError:
    try:
        from src.telegram_notifier import (
            notify_success,
            notify_vacation,
            notify_holiday_or_weekend,
            notify_error
        )
    except ImportError:
        def notify_success(*args, **kwargs): pass
        def notify_vacation(*args, **kwargs): pass
        def notify_holiday_or_weekend(*args, **kwargs): pass
        def notify_error(*args, **kwargs): pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass # In CI/CD dotenv might not be needed/installed, or managed differently

def load_holidays():
    """Carga los festivos/vacaciones del empleado desde el archivo maestro en GitHub."""
    holidays = []
    
    empleado = os.environ.get("EMPLEADO", "").strip()
    if not empleado:
        print("Aviso: Variable EMPLEADO no configurada. No se verificarán festivos personalizados.")
        return holidays

    try:
        import urllib.request
        github_repo = os.environ.get("GITHUB_REPOSITORY", "eaguadov/Atomatizaci-n-Fichaje-Bixpe").strip()
        urls_to_try = [
            f"https://raw.githubusercontent.com/{github_repo}/main/team_holidays.json"
        ]
        if github_repo.lower() != "eaguadov/atomatizaci-n-fichaje-bixpe":
            urls_to_try.append("https://raw.githubusercontent.com/eaguadov/Atomatizaci-n-Fichaje-Bixpe/main/team_holidays.json")

        team_data = None
        for url in urls_to_try:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        team_data = json.loads(response.read().decode('utf-8'))
                        break
            except Exception:
                continue

        if team_data and empleado in team_data:
            emp_holidays = team_data[empleado]
            if isinstance(emp_holidays, dict):
                holidays.extend(emp_holidays.keys())
            elif isinstance(emp_holidays, list):
                holidays.extend(emp_holidays)
            print(f"Festivos de {empleado} sincronizados desde el archivo maestro ({len(holidays)} días).")
        elif team_data:
            print(f"Aviso: El empleado '{empleado}' no se encontró en el calendario maestro.")
        else:
            print(f"Aviso: No se pudo descargar el calendario maestro desde GitHub.")
    except Exception as e:
        print(f"Aviso: Error durante la descarga del calendario maestro: {e}")
            
    return holidays

def is_holiday_or_weekend(holidays):
    """Checks if today is a weekend or a holiday."""
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    # Check Weekend (5=Saturday, 6=Sunday)
    if today.weekday() >= 5:
        print(f"Today is weekend ({today.strftime('%A')}). Skipping.")
        return True
        
    # Check Holiday
    if today_str in holidays:
        print(f"Today is a holiday ({today_str}). Skipping.")
        return True
        
    return False

def run_automation(email, password, action, headless=True, dry_run=False, target_url="https://worktime.bixpe.com/", test_missing_button=False):
    p = sync_playwright().start()
    try:
        # Launch with specific args to avoid detection/rendering issues
        browser = p.chromium.launch(
            headless=headless, 
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled" 
            ],
            ignore_default_args=["--enable-automation"]
        )
        
        # Use a standard User-Agent to avoid being blocked as a bot
        # Also grant geolocation permissions as Bixpe might require them to show the clock-in buttons
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            permissions=['geolocation'],
            geolocation={'latitude': 41.651304749576475, 'longitude': -0.9345988765123099}, # Zaragoza
            viewport={'width': 1280, 'height': 720},
            locale='es-ES'
        )
        page = context.new_page()
        page.set_default_timeout(60000) # Increase default timeout to 60s
        
        # Capture console logs to debug JS errors
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        
        # Capture network failures to identify sources
        page.on("requestfailed", lambda request: print(f"Request failed: {request.url} - {request.failure}"))
        
        print(f"Navigating to {target_url} (con reintentos automáticos)...")
        max_nav_retries = 3
        for attempt in range(1, max_nav_retries + 1):
            try:
                page.goto(target_url, timeout=30000)
                break
            except Exception as ne:
                clean_err = str(ne).split("\n")[0]
                print(f"Intento {attempt}/{max_nav_retries} de carga fallido ({target_url}): {clean_err}")
                if attempt < max_nav_retries:
                    time.sleep(3)
                else:
                    print(f"Error fatal tras {max_nav_retries} intentos cargando la página web.")
                    notify_error(action, f"No se pudo cargar la web de Bixpe ({target_url}) tras {max_nav_retries} intentos: {clean_err}")
                    try:
                        page.screenshot(path="error_navigation.png")
                    except:
                        pass
                    browser.close()
                    p.stop()
                    sys.exit(1)
        
        # Handle Cookies if present
        try:
            if page.is_visible("text=Aceptar todas", timeout=5000):
                page.click("text=Aceptar todas")
            elif page.is_visible("text=Aceptar", timeout=5000):
                page.click("text=Aceptar")
            elif page.is_visible("button[id*='cookie']", timeout=5000):
                 page.click("button[id*='cookie']")
        except:
            pass # Ignore if no cookies found
            
        # Login
        print("Logging in...")
        try:
            # HTML source confirms id="emailLogin" and id="passwordLogin" per user docs
            # Fallbacks kept just in case, but prioritized
            email_selectors = ['#emailLogin', '#Username', 'input[name="Username"]', 'input[placeholder="Email"]']
            password_selectors = ['#passwordLogin', '#Password', 'input[name="Password"]']
            submit_selectors = ['#btn-loginSubmit', 'button[type="submit"]', 'text=Iniciar sesión']
            
            # Fill Email
            email_filled = False
            for selector in email_selectors:
                try:
                    if page.is_visible(selector, timeout=2000):
                        page.fill(selector, email)
                        email_filled = True
                        print(f"Filled email using: {selector}")
                        break
                except:
                    continue
            
            if not email_filled:
                print("Could not find email field. Dumping HTML snippet...")
                print(page.inner_html("body")[:500])
                # Screenshot for debug
                page.screenshot(path="debug_no_email.png")
                raise Exception("Email field not found. Checked: " + ", ".join(email_selectors))

            # Fill Password
            for selector in password_selectors:
                try:
                    if page.is_visible(selector, timeout=2000):
                        page.fill(selector, password)
                        print(f"Filled password using: {selector}")
                        break
                except:
                    continue

            # Click Login
            clicked = False
            for selector in submit_selectors:
                try:
                    if page.is_visible(selector, timeout=2000):
                        page.click(selector)
                        print(f"Clicked login button: {selector}")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                 # Last resort: press Enter
                 page.press('input[type="password"]', 'Enter')
                 print("Pressed Enter to login")
            
            # Wait for dashboard to load
            print("Waiting for dashboard to load (espera dinámica)...")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                print("Network idle reached.")
            except:
                print("Warning: Network idle timeout. Proceeding con espera de elementos...")
            
            # Dynamic Wait for dashboard element instead of hardcoded 10s sleep
            dashboard_selectors = [
                "#btn-start-workday",
                "#btn-stop-workday",
                "#btn-pause-lunch",
                "#btn-resume-workday",
                "a[href*='logout']",
                "#main-content"
            ]
            try:
                found_dashboard_element = False
                for sel in dashboard_selectors:
                    if page.is_visible(sel, timeout=2000):
                        found_dashboard_element = True
                        print(f"Panel de control detectado rápidamente por el elemento: {sel}")
                        break
                if not found_dashboard_element:
                    page.wait_for_selector(", ".join(dashboard_selectors), timeout=10000, state="attached")
                    print("Panel detectado mediante selector de seguridad.")
            except Exception as de:
                print(f"Espera dinámica finalizada/tolerada (verificando URL): {de}")

            # Extra safety check: Try waiting for redirection to worktime.bixpe.com
            try:
                page.wait_for_url(lambda u: "auth2.bixpe.com" not in u.lower(), timeout=5000)
            except:
                pass # If timeout occurs, page.url check below will handle login failure safely

            print("Login wait finished. Checking URL...")
            print(f"Post-login URL: {page.url}")

            # Check if login failed (URL still on login page)
            if "account/login" in page.url.lower() or "auth2.bixpe.com" in page.url.lower():
                print("❌ [BIXPE] Error de autenticación: El inicio de sesión falló.")
                page.screenshot(path="error_login_failed.png")
                notify_error(action, "Error durante inicio de sesión en Bixpe: Usuario o contraseña incorrectos.")
                browser.close()
                p.stop()
                sys.exit(1)

            # Captura de pantalla del panel tras login exitoso (diagnóstico)
            page.screenshot(path=f"dashboard_{action}_{time.strftime('%Y%m%d_%H%M%S')}.png")
            print("📸 Captura del panel guardada para diagnóstico.")

            # Check if Bixpe displays "Vacaciones en curso" on dashboard
            # IMPORTANTE: Usar inner_text("body") para leer SOLO el texto visible,
            # NO page.content() que incluye el código JavaScript donde estas
            # cadenas existen como literals aunque el usuario NO esté de vacaciones.
            try:
                visible_text = page.inner_text("body").lower()
                if ("vacaciones en curso" in visible_text or "estarás de vacaciones" in visible_text) and not test_missing_button:
                    print("🌴 [BIXPE] Detectado: 'Vacaciones en curso' en el texto visible de Bixpe.")
                    page.screenshot(path=f"vacaciones_{action}_{time.strftime('%Y%m%d_%H%M%S')}.png")
                    notify_on_success = str(os.environ.get("NOTIFY_ON_SUCCESS", "true")).lower() == "true"
                    if notify_on_success:
                        notify_vacation(action)
                    else:
                        print("Modo silencioso activado. Omitiendo notificación de vacaciones por Telegram.")
                    browser.close()
                    p.stop()
                    sys.exit(0)
            except Exception as ve:
                print(f"Warning checking vacation status: {ve}")

        except Exception as e:
            print(f"Error during login: {e}")
            print(f"Current URL: {page.url}")
            print(f"Page Title: {page.title()}")
            page.screenshot(path="error_login.png")
            notify_error(action, f"Error durante inicio de sesión: {e}")
            # Dump HTML for debugging
            with open("debug_login.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("Saved debug_login.html. Please verify selectors.")
            sys.exit(1)
    finally:
        pass  # Ensures try block is properly closed

    # Selectors based on Action
    print(f"Performing action: {action}")
    
    # Define selector lists
    # Define selector lists per User Documentation
    # START: #btn-start-workday (Modal: Yes/Cancel)
    # PAUSE: #btn-lunch-pause (No Modal)
    # RESUME: #btn-resume-workday (No Modal)
    # END: #btn-stop-workday (Modal: Yes/Cancel)
    
    # IMPORTANT: Only use button/div selectors, NOT SVG icons (.fa-*) as they don't have .click()
    selectors_map = {
        "START": ["#btn-start-workday"],
        "PAUSE": ["#btn-pause-lunch"],
        "RESUME": ["#btn-resume-workday"],
        "END": ["#btn-stop-workday"]
    }
    
    target_selectors = ["#btn-inexistente-fantasma-999"] if test_missing_button else selectors_map.get(action, [])
    
    # 1. FIND THE BUTTON
    found_selector = None
    for sel in target_selectors:
        try:
            # Quick check if it exists in DOM
            if page.evaluate(f"!!document.querySelector('{sel}')"):
                print(f"Selector found in DOM: {sel}")
                # Check visibility
                if page.is_visible(sel):
                    print(f"Selector is visible: {sel}")
                    found_selector = sel
                    break
                else:
                    print(f"Selector exists but HIDDEN: {sel}")
                    visible_text = page.inner_text("body").lower()
                    if "vacaciones en curso" in visible_text or "estarás de vacaciones" in visible_text:
                        print("🌴 [BIXPE] Botón oculto por vacaciones en curso.")
                        page.screenshot(path=f"vacaciones_btn_{action}_{time.strftime('%Y%m%d_%H%M%S')}.png")
                        notify_vacation(action)
                        browser.close()
                        p.stop()
                        sys.exit(0)
                    else:
                        print(">>> Botón no visible directamente. Intentando interacción o diagnósticos de visibilidad...")
        except Exception as e:
            print(f"Check failed for {sel}: {e}")
            
    if not found_selector:
        print(f"ERROR: Target button for {action} not found.")
        print("--- DOM PROBE: VISIBLE BUTTONS ---")
        try:
            # JavaScript to extract details of all visible buttons
            buttons_info = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button, a.btn, div.btn')).map(el => {
                    const rect = el.getBoundingClientRect();
                    const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
                    return {
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        text: el.innerText.substring(0, 20).replace(/\\n/g, ''),
                        visible: isVisible
                    };
                }).filter(b => b.visible);
            }""")
            
            for b in buttons_info:
                print(f"Found: <{b['tag']} id='{b['id']}' class='{b['className']}'> Text: '{b['text']}'")
                
        except Exception as e:
            print(f"DOM Probe failed: {e}")
            
        print("--------------------------------")

        # Emergency dump
        print("Dumping HTML...")
        try:
            with open(f"debug_fail_{action}.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"Saved debug_fail_{action}.html")
        except Exception as e:
            print(f"Could not save HTML dump: {e}")
            
        page.screenshot(path=f"error_no_btn_{action}.png")
        notify_error(action, f"No se encontró el botón para {action} en la pantalla de Bixpe.")
        browser.close()
        p.stop()
        sys.exit(1)

    # ---------------------------------------------------------
    # DIAGNOSTIC CHECKLIST (Per User Request)
    # ---------------------------------------------------------
    print("\n--- PRE-CLICK DIAGNOSTIC CHECKLIST ---")
    
    # 1. Overlay Check
    try:
        overlay_visible = page.evaluate("() => { const el = document.querySelector('#processing-text'); return el && (el.offsetWidth > 0 || window.getComputedStyle(el).display !== 'none'); }")
        print(f"[Check 1] Overlay '#processing-text' visible? {overlay_visible}")
    except:
        print("[Check 1] Overlay '#processing-text' not found in DOM.")

    # 2. Target Button Properties
    if found_selector:
        try:
            btn_info = page.evaluate(f"""() => {{
                const el = document.querySelector('{found_selector}');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                
                // Check what element is at the button's center (Click Interception Check)
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const topEl = document.elementFromPoint(centerX, centerY);
                
                return {{
                    tagName: el.tagName,
                    display: window.getComputedStyle(el).display,
                    visibility: window.getComputedStyle(el).visibility,
                    rect: rect,
                    opacity: window.getComputedStyle(el).opacity,
                    coveredBy: topEl ? (topEl.id || topEl.className || topEl.tagName) : 'None'
                }};
            }}""")
            
            if btn_info:
                print(f"[Check 2] Button Tag: {btn_info['tagName']} (Expected: DIV or BUTTON)")
                print(f"[Check 3] Visibility: {btn_info['display']} / {btn_info['visibility']} / Opacity: {btn_info['opacity']}")
                print(f"[Check 4] Dimensions: {btn_info['rect']}")
                print(f"[Check 5] Element at Click Point: {btn_info['coveredBy']}")
                
                if btn_info['coveredBy'] and btn_info['coveredBy'] not in found_selector:
                     print(f"    WARNING: Button might be covered by '{btn_info['coveredBy']}'!")
            else:
                print("[Check 2] Button info could not be retrieved.")
        except Exception as e:
            print(f"Diagnostic failed: {e}")
    print("------------------------------------------\n")

    # 2. CLICK THE BUTTON
    # IMPLEMENTING TECHNICAL FIXES (Strategies A, B, C)
    try:
        # Strategy A: Smart Wait for "Ghost Layer"
        print("Strategy A: Waiting for '#processing-text' overlay to disappear...")
        try:
            # Wait short time for it to possibly appear/disappear
            page.wait_for_selector("#processing-text", state="hidden", timeout=5000)
            print("Overlay cleared.")
        except Exception as e:
            print(f"Overlay wait warning (might not exist): {e}")

        # Strategy C: The "Nuclear Option" (JavaScript Dispatch)
        # We prioritize this because the element is a DIV and might have tooltips/overlays
        print(f"Strategy C: Attempting JS Click on: {found_selector}")
        page.evaluate(f"document.querySelector('{found_selector}').click()")
        print("JS click command sent.")
        
        # Fallback Strategy B: Force Click if JS didn't trigger navigation/modal
        # We wait a split second to see if something happens
        time.sleep(1)
        
    except Exception as e:
        print(f"FATAL ERROR clicking button: {e}")
        print(">>> Click failed. Taking error screenshot and exiting.")
        page.screenshot(path=f"error_click_{action}_{time.strftime('%Y%m%d_%H%M%S')}.png")
        notify_error(action, f"Fallo al pulsar el botón en Bixpe: {e}")
        browser.close()
        p.stop()
        sys.exit(1)  # Exit with error code

    # Continue to confirmation check

    # 3. HANDLE CONFIRMATION (START and END require confirmation)
    if action in ["START", "END"]:
        print("Checking for confirmation dialog...")
        time.sleep(1) # Slight delay for modal animation
        
        # Decide whether to Confirm or Cancel based on Simulation Mode
        if dry_run: # Simulation mode requested by user
             print("[SIMULATION] Simulation mode active. searching for CANCEL button...")
             # Look for swal2-cancel or general cancel
             confirm_selector_js = "button.swal2-cancel, button.cancel"
             action_verb = "CANCELLED"
        else:
             print("Check for CONFIRM button...")
             # Look for swal2-confirm or general confirm
             confirm_selector_js = "button.swal2-confirm, button.confirm"
             action_verb = "CONFIRMED"

        confirm_script = f"""
            (() => {{
                const btns = document.querySelectorAll('{confirm_selector_js}');
                for (const btn of btns) {{
                    if (btn.offsetParent !== null) {{
                        btn.click();
                        return true;
                    }}
                }}
                return false;
            }})()
        """
        try:
            if page.evaluate(confirm_script):
                print(f"Confirmation dialog {action_verb} successfully.")
                time.sleep(2)
            else:
                print("No confirmation dialog found (or not needed).")
        except Exception as e:
            print(f"Confirmation check error: {e}")
            page.screenshot(path=f"error_confirm_{action}_{time.strftime('%Y%m%d_%H%M%S')}.png")
            notify_error(action, f"Error en diálogo de confirmación: {e}")
            try:
                browser.close()
            except:
                pass
            p.stop()
            sys.exit(1)
    else:
        print(f"Action {action} requires no confirmation interaction.")

    # Success Screenshot
    page.screenshot(path=f"screenshot_{action}_{time.strftime('%Y%m%d_%H%M%S')}.png")
    
    # Notify Success or Simulation via Telegram (silenced if NOTIFY_ON_SUCCESS is false)
    notify_on_success = str(os.environ.get("NOTIFY_ON_SUCCESS", "true")).lower() == "true"
    if notify_on_success:
        notify_success(action, is_simulation=dry_run)
    else:
        print(f"Modo silencioso activado. Omitiendo notificación de éxito por Telegram para la acción {action}.")

    # Cleanup resources
    try:
        browser.close()
    except:
        pass
    p.stop()
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["START", "PAUSE", "RESUME", "END"], required=True)
    parser.add_argument("--visible", action="store_true", help="Run with visible browser for debugging")
    parser.add_argument("--force", action="store_true", help="Ignore schedule and holiday checks")
    parser.add_argument("--simulate", action="store_true", help="Perform login/nav, click action, but CANCEL the confirmation modal.")
    parser.add_argument("--dry-run", action="store_true", help="(Legacy) Alias for --simulate")
    parser.add_argument("--url", default="https://worktime.bixpe.com/", help="Target URL for Bixpe automation")
    parser.add_argument("--test-missing-button", action="store_true", help="Simulate a missing button error for testing")
    args = parser.parse_args()
    
    # Unify simulation flags
    is_simulation = args.simulate or args.dry_run

    # Cargar festivos desde el archivo maestro en GitHub
    holidays = load_holidays()

    # ALWAYS check holidays/weekends (even with --force)
    # --force only skips schedule/time checks, not holiday checks
    if is_holiday_or_weekend(holidays):
        print("Exiting: Today is a holiday or weekend.")
        notify_on_success = str(os.environ.get("NOTIFY_ON_SUCCESS", "true")).lower() == "true"
        if notify_on_success:
            notify_holiday_or_weekend("Fin de semana o festivo programado")
        else:
            print("Modo silencioso activado. Omitiendo notificación de festivo por Telegram.")
        sys.exit(0)

    # Load Schedule
    schedule_file = os.path.join(os.path.dirname(__file__), "..", "schedule.json")
    try:
        with open(schedule_file, 'r') as f:
            schedule_config = json.load(f)
    except FileNotFoundError:
        print("Warning: schedule.json not found. Using defaults.")
        schedule_config = {}

    if not args.force:
        # Validate Action for Today
        today = date.today()
        # 0-4 is Mon-Fri. 4 is Friday.
        is_friday = today.weekday() == 4
        
        day_key = "friday" if is_friday else "mon_thu"
        day_schedule = schedule_config.get(day_key, {})
        
        # Map CLI arg to JSON key
        action_map = {
            "START": "start",
            "PAUSE": "break_start",
            "RESUME": "break_end",
            "END": "end"
        }
        
        config_key = action_map.get(args.action)
        if config_key:
            if day_schedule.get(config_key) is None:
                print(f"Action {args.action} is not scheduled for today ({day_key}). Skipping.")
                sys.exit(0)
            else:
                print(f"Executing {args.action} for {day_key} (Scheduled: {day_schedule.get(config_key)})")

    email = os.environ.get("BIXPE_EMAIL")
    password = os.environ.get("BIXPE_PASSWORD")

    if not email or not password:
        # Fallback for local testing if env vars not set (remove in production!)
        email = input("Enter Bixpe Email: ") if args.visible else None
        password = input("Enter Bixpe Password: ") if args.visible else None
    
    if not email or not password:
        print("Error: BIXPE_EMAIL and BIXPE_PASSWORD environment variables must be set.")
        sys.exit(1)

    try:
        run_automation(email, password, args.action, headless=not args.visible, dry_run=is_simulation, target_url=args.url, test_missing_button=args.test_missing_button)
    except Exception as e:
        print(f"Error fatal inesperado en la automatización: {e}")
        sys.exit(1)
