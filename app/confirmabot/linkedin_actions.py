"""
Módulo para manejar acciones automatizadas en LinkedIn
"""

from app.confirmabot.confirm_bot import open_chrome_profile
from app.database.database import get_txt_email_by_id
from app.utils.human_behavior import (
    random_delay, fill_field_safely, click_button_safely,
    generate_random_password, generate_random_name, generate_random_lastname,
    DELAYS
)
from app.utils.captcha_handler import detect_and_handle_captcha
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from tkinter import messagebox
import time
import random

def process_linkedin_email(email_id):
    """Proceso principal de creación de cuenta en LinkedIn"""
    try:
        # Paso 1: Obtener email
        email_data = get_txt_email_by_id(email_id)
        if not email_data:
            messagebox.showerror("Email no encontrado", f"❌ No se encontró email con ID: {email_id}")
            return False
        
        email_text = email_data['email']
        print(f"📧 Email obtenido: {email_text}")
        
        # Paso 2: Abrir LinkedIn
        driver = open_chrome_profile(incognito_mode=True)
        random_delay(0.5, 1.5)
        driver.maximize_window()
        random_delay(1.0, 2.5)
        driver.get("https://www.linkedin.com/signup?_l=us&trk=guest_homepage-basic_nav-header-join.com/")
        
        # Paso 3: Configurar espera
        wait = WebDriverWait(driver, random.randint(*DELAYS['wait']))
        random_delay(0.56, 1.4)
        
        # Paso 4: Llenar email
        email_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "input[data-tracking-control-name='email-address']"
        )))
        fill_field_safely(driver, email_input, email_text, "Email")
        
        # Paso 5: Llenar contraseña
        password_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "input[data-tracking-control-name='registration-frontend_join-form-password']"
        )))
        password = generate_random_password()
        fill_field_safely(driver, password_input, password, "Contraseña")
        
        # Paso 6: Botón Agree & Join
        submit_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button[data-tracking-control-name='registration-frontend_join-form-submit']"
        )))
        click_button_safely(driver, submit_button, "Agree & Join")
        
        # Paso 7: Llenar nombre
        first_name_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "input[data-tracking-control-name='registration-frontend_join-form-name_first-name']"
        )))
        first_name = generate_random_name()
        fill_field_safely(driver, first_name_input, first_name, "Nombre")
        
        # Paso 8: Llenar apellido
        last_name_input = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "input[data-tracking-control-name='registration-frontend_join-form-name_last-name']"
        )))
        last_name = generate_random_lastname()
        fill_field_safely(driver, last_name_input, last_name, "Apellido")
        
        # Paso 9: Botón Continue
        continue_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button[data-tracking-control-name='registration-frontend_join-form-submit']"
        )))
        click_button_safely(driver, continue_button, "Continue")
        
        # Paso 10: Manejar captcha con reintentos
        print("🔍 Esperando captcha o verificación...")
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            print(f"🔄 Intento {retry_count + 1} de {max_retries}")
            
            # Esperar a que aparezca el captcha y observarlo hasta que se resuelva
            captcha_result = detect_and_handle_captcha(driver)
            
            if captcha_result == "completed":
                print("🎉 ¡Captcha completado exitosamente!")
                return True
            elif captcha_result == "errors_handled":
                print("⚠️ Error del captcha detectado y cerrado")
                retry_count += 1
                
                if retry_count < max_retries:
                    print("🔄 Reintentando...")
                    # Esperar un momento y volver a dar click en Continue
                    time.sleep(2)
                    try:
                        continue_button = wait.until(EC.element_to_be_clickable((
                            By.CSS_SELECTOR, "button[data-tracking-control-name='registration-frontend_join-form-submit']"
                        )))
                        click_button_safely(driver, continue_button, "Continue (reintento)")
                        time.sleep(2)
                    except Exception as e:
                        print(f"⚠️ Error al reintentar: {e}")
                        break
                else:
                    print("❌ Máximo de reintentos alcanzado. Finalizando proceso.")
                    return False
            elif captcha_result == "timeout":
                print("⏰ Timeout del captcha")
                return False
            else:
                print(f"❓ Estado inesperado del captcha: {captcha_result}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Error en process_linkedin_email: {e}")
        return False

def close_linkedin_window(driver):
    """Cierra la ventana de LinkedIn de forma segura"""
    try:
        if driver:
            driver.quit()
            print("🔒 Ventana de LinkedIn cerrada")
    except Exception as e:
        print(f"⚠️ Error al cerrar la ventana: {e}")

# Función para testing
if __name__ == "__main__":
    print("🧪 Probando función de LinkedIn...")
    success = process_linkedin_email(1)
    if success:
        print("✅ Prueba exitosa")
    else:
        print("❌ Prueba fallida")