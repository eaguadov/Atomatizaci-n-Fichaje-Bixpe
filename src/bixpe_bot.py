import os
import sys
import json
import time
import argparse
from datetime import datetime, date
from playwright.sync_api import sync_playwright

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

def load_holidays(json_path):
    """Loads holidays from the JSON file."""
    try:
        with open(json_path, 'r') as f:
            holidays = json.load(f)
        return holidays
    except FileNotFoundError:
        print(f"Warning: {json_path} not found. No holidays loaded.")
        return []

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

def run_automation(email, password, action, headless=True, dry_run=False, target_url="https://worktime.bixpe.com/"):
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
        
        print(f"Navigating to {target_url}...")
        try:
            page.goto(target_url, timeout=30000)
        except Exception as ne:
            print(f"Error cargando la página web ({target_url}): {ne}")
            notify_error(action, f"No se pudo cargar la web de Bixpe ({target_url}): {ne}")
            page.screenshot(path="error_navigation.png")
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
            print("Waiting for dashboard to load (networkidle)...")
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
                print("Network idle reached.")
            except:
                print("Warning: Network idle timeout. Proceeding...")
            
            # Explicit safety sleep to prevent crashes on dynamic loads
            print("Sleeping 10s (via Playwright) to ensure dashboard stability...")
            page.wait_for_timeout(10000)
            print("Login wait finished. Checking URL...")
            print(f"Post-login URL: {page.url}")

            # Check if Bixpe displays "Vacaciones en curso" on dashboard
            try:
                body_content = page.content().lower()
                if "vacaciones en curso" in body_content or "estarás de vacaciones" in body_content:
                    print("🌴 [BIXPE] Detectado: 'Vacaciones en curso' en la interfaz de Bixpe.")
                    notify_vacation(action)
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
    
    target_selectors = selectors_map.get(action, [])
    
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
                    body_text = page.content().lower()
                    if "vacaciones" in body_text:
                        print("🌴 [BIXPE] Botón oculto por vacaciones en curso.")
                        notify_vacation(action)
                        browser.close()
                        p.stop()
                        sys.exit(0)
                    else:
                        print(">>> Error: El botón está oculto y no estás de vacaciones.")
                        notify_error(action, f"El botón '{sel}' está oculto en la interfaz.")
                        page.screenshot(path=f"error_btn_hidden_{action}.png")
                        browser.close()
                        p.stop()
                        sys.exit(1)
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
        if not dry_run:
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
    
    # Notify Success or Simulation via Telegram
    notify_success(action, is_simulation=dry_run)

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
    args = parser.parse_args()
    
    # Unify simulation flags
    is_simulation = args.simulate or args.dry_run

    # Load holidays
    holidays_file = os.path.join(os.path.dirname(__file__), "..", "holidays.json")
    holidays = load_holidays(holidays_file)

    # ALWAYS check holidays/weekends (even with --force)
    # --force only skips schedule/time checks, not holiday checks
    if is_holiday_or_weekend(holidays):
        print("Exiting: Today is a holiday or weekend.")
        notify_holiday_or_weekend("Fin de semana o festivo programado")
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
        run_automation(email, password, args.action, headless=not args.visible, dry_run=is_simulation, target_url=args.url)
    except Exception as e:
        print(f"Error fatal inesperado en la automatización: {e}")
        sys.exit(1)
