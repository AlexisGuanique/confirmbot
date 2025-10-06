from faker import Faker
import time
import random
import string
import pyautogui
from app.database.database import get_click_coordinates, get_nopecha_key
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import sys
from tkinter import messagebox
from app.confirmabot.utils.proxy_tool_safe import SafeProxyController as ProxyController

fake = Faker()

def generate_custom_username():

    word = fake.word().lower()
    number = random.randint(0, 600)
    letters = ''.join(random.choices(string.ascii_lowercase, k=4))
    return f"{word}{number}{letters}"

def generate_secure_password(length=10):

    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def mail_actions(driver, domain, enable_proxy=True, force_disable_proxy=False):
    try:
        # 👉 Abrir Google para mantener la ventana visible y luego ejecutar los clics
        #driver.get("https://www.google.com/")
        # Asegurar que la ventana esté maximizada y en foco antes de los clics


        #driver.switch_to.window(driver.current_window_handle)
        #time.sleep(3)  # Esperar a que se dibuje la ventana

        # 👉 Ejecutar clicks automáticos antes de ir a 33mail
        #global_start = time.time()

        #coords = get_click_coordinates()
        #api_key = get_nopecha_key()

        # Validar configuración
        #if not coords or not api_key:
        #    messagebox.showerror(
        #        "Configuración faltante",
        #        "⚠️ Debes configurar las coordenadas y la NopeCHA API key antes de ejecutar el bot."
        #    )
        #    try:
        #        driver.quit()
        #    except Exception:
        #        pass
        #    return False, None

        #if coords:
        #    c1 = coords.get("first_click")
        #    c2 = coords.get("second_click")
        #    c3 = coords.get("third_click")
        #    c4 = coords.get("fourth_click")

        #    for idx, coord_str in enumerate([c1, c2, c3], start=1):
        #        if coord_str and "x" in coord_str:
        #            if time.time() - global_start > 300:
        #                print("⏰ Timeout global de 5 minutos en mail_actions. Abortando.")
        #                driver.quit()
        #                return False, None
        #            x_str, y_str = coord_str.replace(" ", "").split("x")
        #            try:
        #                x, y = int(x_str), int(y_str)
        #                print(f"🖱️ Click {idx} en ({x}, {y})")
        #                pyautogui.click(x, y)
        #                time.sleep(1)
        #            except ValueError:
        #                print(f"⚠️ Coordenada inválida: {coord_str}")

            # Pegamos texto después del tercer click
        #    paste_text = api_key
        #    pyperclip.copy(paste_text)
        #    pyautogui.hotkey("ctrl", "v")
        #    print("📋 Texto pegado.")
        #    time.sleep(2)

        #    # Cuarto click después de pegar el texto
        #    if c4 and "x" in c4:
        #        try:
        #            x4, y4 = map(int, c4.replace(" ", "").split("x"))
        #            print(f"🖱️ Click 4 en ({x4}, {y4}) después de pegar texto")
        #            pyautogui.click(x4, y4)
        #            time.sleep(1)
        #        except ValueError:
        #            print(f"⚠️ Coordenada inválida: {c4}")

        # 🌐 ACTIVAR PROXY ANTES de abrir la página de 33mail (sin cambiar configuración)
        #print("🌐 Activando proxy antes de abrir 33mail...")
        #proxy_controller = ProxyController()
        #try:
            # Solo activar el proxy sin cambiar la configuración existente
            #proxy_controller.enable_proxy_only()
            #proxy_controller.refresh_internet_settings()
            
            # Verificar que el proxy esté realmente activo
            #print("🔍 Verificando que el proxy esté activo...")
            #enabled, server, port = proxy_controller.get_proxy_status()
            #if enabled and server:
                #print(f"✅ Proxy confirmado activo: {server}")
            #else:
                #print("⚠️ Proxy no se activó correctamente, reintentando...")
                #proxy_controller.enable_proxy_only()
                #proxy_controller.refresh_internet_settings()
                #time.sleep(3)  # Esperar más tiempo en el segundo intento
                
        #finally:
        #    proxy_controller.close()
        
        # Esperar tiempo suficiente para que el proxy se active completamente
        #print("⏳ Esperando que el proxy se active completamente...")
        #time.sleep(8)  # Esperar que el proxy se active antes de abrir la página

        print("🌐 Abriendo 33mail para crear cuenta...")
        driver.get("https://www.33mail.com/signup")
        print("🔄 Refrescando la página...")
        driver.refresh()
        #time.sleep(2)
        #driver.refresh()
        time.sleep(2)
        print("📨 Iniciando acciones en la página de 33mail...")
        #try:
        #   driver.maximize_window()
        #except Exception:
        #   pass

        # 🌐 DESACTIVAR PROXY temporalmente para resolver captcha
        #print("🌐 Desactivando proxy temporalmente para resolver captcha...")
        #proxy_controller = ProxyController()
        #try:
            #proxy_controller.disable_proxy()
            #proxy_controller.refresh_internet_settings()
            #print("✅ Proxy desactivado temporalmente")
        #finally:
            #proxy_controller.close()
        #time.sleep(2)  # Esperar que se desactive

        # ✋ Esperar a que la extensión resuelva el reCAPTCHA ANTES de rellenar el formulario
        try:
            WebDriverWait(driver, 180).until(
                lambda d: d.execute_script(
                    "return (typeof grecaptcha !== 'undefined' && grecaptcha.getResponse().length > 0);"
                )
            )
            print("🔑 Token de reCAPTCHA detectado (grecaptcha.getResponse()).")
        except TimeoutException:
            print("⚠️ No se detectó token de reCAPTCHA mediante grecaptcha.getResponse(). Se intentará verificar textarea oculto…")
            try:
                WebDriverWait(driver, 60).until(
                    lambda d: d.execute_script(
                        "var t=document.querySelector('textarea[name=\"g-recaptcha-response\"]'); return t && t.value.trim().length>0;"
                    )
                )
                print("🔑 Token de reCAPTCHA detectado en textarea oculto.")
            except TimeoutException:
                print("⚠️ No se detectó el token de reCAPTCHA dentro del tiempo límite. Continuaremos, pero el servidor podría rechazar el registro.")

        # ✅ Asegurarse de que desaparezca el overlay de captcha
        try:
            overlay_locator = (By.CSS_SELECTOR, 'div[style*="z-index: 2000000000"]')
            WebDriverWait(driver, 120).until(EC.invisibility_of_element_located(overlay_locator))
            print("✅ Captcha resuelto, overlay desapareció.")
        except TimeoutException:
            print("⚠️ Timeout esperando que desaparezca overlay de captcha. Podría interferir posteriormente.")

        # 🌐 REACTIVAR PROXY antes de llenar los inputs (si está habilitado y no forzado a deshabilitar)
        if enable_proxy and not force_disable_proxy:
            print("🌐 Reactivando proxy antes de llenar formulario...")
            try:
                proxy_controller = ProxyController()
                # Solo reactivar el proxy sin cambiar la configuración existente
                success = proxy_controller.enable_proxy_only()
                if success:
                    proxy_controller.refresh_internet_settings()
                    print("✅ Proxy activado (versión segura)")
                    
                    # Esperar tiempo mínimo para que el proxy se reactive
                    print("⏳ Esperando que el proxy se reactive...")
                    time.sleep(1)  # Reducido a 1 segundo
                    print("✅ Proxy listo, continuando con el formulario...")
                else:
                    print("⚠️ No se pudo activar proxy, continuando sin proxy...")
                proxy_controller.close()
                
            except Exception as e:
                print(f"⚠️ Error con proxy: {e}, continuando sin proxy...")
        else:
            if force_disable_proxy:
                print("⏭️ Proxy deshabilitado forzadamente (para evitar cuelgues)")
            else:
                print("⏭️ Proxy deshabilitado por configuración")

        # 👉 Generar datos
        username = generate_custom_username()
        username2 = generate_custom_username()
        second_username = generate_custom_username()
        final_email = f"{second_username}@{username}.33mail.com"  # Email que se guarda en BD
        generated_email = f"{username2}{domain}"  # Email usado en formulario para buscar URL
        password = generate_secure_password()

        wait = WebDriverWait(driver, 30)

        # 👉 Email destino
        input_email = wait.until(EC.presence_of_element_located((By.ID, "lbl-13")))
        input_email.clear()
        input_email.send_keys(generated_email)

        # 👉 Username
        input_username = wait.until(EC.presence_of_element_located((By.ID, "lbl-14")))
        input_username.clear()
        input_username.send_keys(username)

        # 👉 Contraseña
        input_password = wait.until(EC.presence_of_element_located((By.ID, "lbl-15")))
        input_password.clear()
        input_password.send_keys(password)

        # 👉 Confirmar contraseña
        input_password_confirm = wait.until(EC.presence_of_element_located((By.ID, "lbl-16")))
        input_password_confirm.clear()
        input_password_confirm.send_keys(password)

        print(f"✅ Formulario completado - Email: {generated_email}, Username: {username}")

        submit_button_xpath = '//input[@type="submit" and @value="Continue signup"]'
        submit_button = wait.until(EC.presence_of_element_located((By.XPATH, submit_button_xpath)))

        # Hacer scroll hasta el botón
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(0.5)

        # Intentar hacer clic con reintentos por si algún overlay residual intercepta el clic
        for attempt in range(5):
            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, submit_button_xpath)))
                submit_button.click()
                print("✅ Formulario enviado correctamente")
                break
            except ElementClickInterceptedException:
                time.sleep(2)
        else:
            raise Exception("No se pudo hacer clic en el botón de continuar tras múltiples intentos.")

        # Esperar a que desaparezca el botón O se cargue alguna señal de éxito
        wait_success = WebDriverWait(driver, 60)
        try:
            wait_success.until(
                EC.any_of(
                    EC.invisibility_of_element_located((By.XPATH, submit_button_xpath)),
                    EC.presence_of_element_located((By.XPATH, '//a[@href="/dashboard"]'))
                )
            )
            print("✅ Registro completado exitosamente")
            
            # 🌐 DESACTIVAR PROXY después del éxito (si estaba habilitado)
            if enable_proxy:
                print("🌐 Desactivando proxy después del éxito...")
                proxy_controller = ProxyController()
                try:
                    proxy_controller.disable_proxy()
                    proxy_controller.refresh_internet_settings()
                finally:
                    proxy_controller.close()
                time.sleep(1)  # Esperar un momento para que el proxy se desactive
            
        except TimeoutException:
            # 🌐 DESACTIVAR PROXY incluso si hay timeout (por seguridad, si estaba habilitado)
            if enable_proxy:
                print("🌐 Desactivando proxy por timeout...")
                proxy_controller = ProxyController()
                try:
                    proxy_controller.disable_proxy()
                    proxy_controller.refresh_internet_settings()
                finally:
                    proxy_controller.close()
            raise Exception("Timeout esperando confirmación de registro.")

        return True, final_email, generated_email

    except Exception as e:
        print(f"❌ Error durante las acciones en mail: {e}")
        # 🌐 DESACTIVAR PROXY en caso de error (por seguridad)
        print("🌐 Desactivando proxy por error...")
        try:
            proxy_controller = ProxyController()
            try:
                proxy_controller.disable_proxy()
                proxy_controller.refresh_internet_settings()
            finally:
                proxy_controller.close()
        except:
            pass  # Ignorar errores al desactivar proxy
        return False, None, None
