from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
import sys
from app.confirmabot.hostinger_actions import perform_hostinger_actions
import time

import concurrent.futures

def login_to_hostinger(driver, email, password):
    try:
        if not email or not password:
            print("⚠️ Credenciales no proporcionadas.")
            messagebox.showerror(
                "Credenciales de Hostinger faltantes",
                "Debes ingresar tu email y contraseña de Hostinger.\n\nHazlo desde la interfaz de configuración y vuelve a ejecutar la aplicación."
            )
            sys.exit()

        print("🌐 Abriendo bandeja de entrada de Hostinger...")

        def open_hostinger():
            driver.get("https://mail.hostinger.com/?_task=mail&_mbox=INBOX.Confirmar")

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(open_hostinger)
            try:
                future.result(timeout=30)
            except concurrent.futures.TimeoutError:
                print("❌ Timeout: la página de Hostinger no respondió a tiempo.")
                return False

        # 🕐 Esperar un momento para que la página cargue completamente
        print("⏳ Esperando a que la página cargue completamente...")
        time.sleep(3)

        # 🔍 Verificar si hay captcha presente
        print("🔍 Verificando si hay captcha presente...")
        captcha_detected = False
        try:
            # Buscar el elemento del captcha
            captcha_element = driver.find_element(By.CSS_SELECTOR, "h1.zone-name-title.h1 img[src='/favicon.ico']")
            if captcha_element:
                captcha_detected = True
                print("⚠️ Captcha detectado. Esperando a que se resuelva...")
        except:
            print("✅ No se detectó captcha, procediendo con el login...")

        # ⏳ Si hay captcha, esperar a que desaparezca
        if captcha_detected:
            max_captcha_wait = 180  # 3 minutos máximo para resolver captcha
            captcha_start_time = time.time()
            
            while time.time() - captcha_start_time < max_captcha_wait:
                try:
                    # Verificar si el captcha sigue presente
                    captcha_element = driver.find_element(By.CSS_SELECTOR, "h1.zone-name-title.h1 img[src='/favicon.ico']")
                    print("⏳ Captcha aún presente, esperando 2 segundos...")
                    time.sleep(2)
                except:
                    print("✅ Captcha resuelto, procediendo con el login...")
                    break
            else:
                print("⏰ Timeout esperando que se resuelva el captcha. Continuando de todas formas...")

        # 🔍 Ahora buscar los elementos del formulario de login
        max_retries = 10
        global_start = time.time()
        for attempt in range(1, max_retries + 1):
            print(f"⏳ Intento número: {attempt}")

            # Timeout global de 5 min
            if time.time() - global_start > 300:
                print("⏰ Timeout global de 5 minutos alcanzado en login_to_hostinger. Abortando intento.")
                return False

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "rcmloginuser"))
                )
                break
            except:
                print(f"⏳ Esperando formulario de login... intento {attempt}/{max_retries}")
                time.sleep(1)
        else:
            print("❌ No se pudo cargar el formulario de login después de varios intentos.")
            return False

        # ✅ Sólo ahora podemos confirmar que el login es posible
        print("✅ Login automático comenzando...")

        user_input = driver.find_element(By.ID, "rcmloginuser")
        pass_input = driver.find_element(By.ID, "rcmloginpwd")
        login_button = driver.find_element(By.ID, "rcmloginsubmit")

        user_input.clear()
        user_input.send_keys(email)
        pass_input.clear()
        pass_input.send_keys(password)
        
        print("📝 Datos de login ingresados. Verificando si hay captcha antes de hacer clic...")
        
        # 🔍 Verificar captcha después de ingresar datos pero antes de hacer clic
        captcha_detected_after_input = False
        try:
            captcha_element = driver.find_element(By.CSS_SELECTOR, "h1.zone-name-title.h1 img[src='/favicon.ico']")
            if captcha_element:
                captcha_detected_after_input = True
                print("⚠️ Captcha detectado después de ingresar datos. Esperando a que se resuelva...")
        except:
            print("✅ No se detectó captcha después de ingresar datos.")

        # ⏳ Si hay captcha después de ingresar datos, esperar a que desaparezca
        if captcha_detected_after_input:
            max_captcha_wait = 180  # 3 minutos máximo para resolver captcha
            captcha_start_time = time.time()
            
            while time.time() - captcha_start_time < max_captcha_wait:
                try:
                    captcha_element = driver.find_element(By.CSS_SELECTOR, "h1.zone-name-title.h1 img[src='/favicon.ico']")
                    print("⏳ Captcha aún presente después de ingresar datos, esperando 2 segundos...")
                    time.sleep(2)
                except:
                    print("✅ Captcha resuelto después de ingresar datos, procediendo con el clic...")
                    break
            else:
                print("⏰ Timeout esperando que se resuelva el captcha después de ingresar datos. Continuando de todas formas...")

        # 👆 Ahora hacer clic en el botón de login
        login_button.click()
        print("🖱️ Clic en botón de login realizado.")

        # 🔍 Verificar captcha después del clic
        print("🔍 Verificando si hay captcha después del clic...")
        captcha_detected_after_click = False
        try:
            captcha_element = driver.find_element(By.CSS_SELECTOR, "h1.zone-name-title.h1 img[src='/favicon.ico']")
            if captcha_element:
                captcha_detected_after_click = True
                print("⚠️ Captcha detectado después del clic. Esperando a que se resuelva...")
        except:
            print("✅ No se detectó captcha después del clic.")

        # ⏳ Si hay captcha después del clic, esperar a que desaparezca
        if captcha_detected_after_click:
            max_captcha_wait = 180  # 3 minutos máximo para resolver captcha
            captcha_start_time = time.time()
            
            while time.time() - captcha_start_time < max_captcha_wait:
                try:
                    captcha_element = driver.find_element(By.CSS_SELECTOR, "h1.zone-name-title.h1 img[src='/favicon.ico']")
                    print("⏳ Captcha aún presente después del clic, esperando 2 segundos...")
                    time.sleep(2)
                except:
                    print("✅ Captcha resuelto después del clic, procediendo...")
                    break
            else:
                print("⏰ Timeout esperando que se resuelva el captcha después del clic. Continuando de todas formas...")

        print("✅ Login automático completado.")

        success = perform_hostinger_actions(driver)
        if success:
            print("✅ Acción completada después del login.")
        else:
            print("⚠️ No se pudo completar la acción después del login.")

        return success

    except Exception as e:
        print(f"❌ Error durante el login: {e}")
        return False
