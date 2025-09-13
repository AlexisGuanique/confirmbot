from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
import sys
try:
    from app.confirmabot.hostinger_actions import wait_for_confirmation_email
except ImportError:
    from hostinger_actions import wait_for_confirmation_email
import time

import concurrent.futures

def wait_for_33mail_header(driver, timeout_seconds=60):
    """
    Espera hasta que aparezca el header de 33mail en la página
    
    Args:
        driver: WebDriver de Selenium
        timeout_seconds: Tiempo máximo de espera en segundos (default: 60)
    
    Returns:
        bool: True si encuentra el header, False si timeout
    """
    import time
    
    print(f"⏳ Esperando header de 33mail (timeout: {timeout_seconds}s)...")
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        try:
            # Buscar el elemento header con el logo de 33mail
            header_element = driver.find_element(By.CSS_SELECTOR, "header[data-reactid='.0.1']")
            
            # Verificar que contiene el logo de 33mail
            logo_element = header_element.find_element(By.CSS_SELECTOR, "strong.logo a[href='/']")
            
            if logo_element and "33mail" in logo_element.text:
                print("✅ Header de 33mail encontrado!")
                return True
                
        except Exception as e:
            # Elemento no encontrado, continuar esperando
            pass
        
        # Esperar 2 segundos antes del siguiente intento
        time.sleep(2)
        
        # Mostrar progreso cada 10 segundos
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0 and elapsed > 0:
            print(f"⏱️ Esperando header... ({elapsed}s/{timeout_seconds}s)")
    
    print(f"⏰ Timeout: No se encontró el header de 33mail en {timeout_seconds} segundos")
    return False

def login_to_hostinger(driver, email, password):
    """
    Nueva función simplificada que usa wait_for_confirmation_email para extraer URLs automáticamente
    """
    try:
        if not email or not password:
            print("⚠️ Credenciales no proporcionadas.")
            messagebox.showerror(
                "Credenciales de Hostinger faltantes",
                "Debes ingresar tu email y contraseña de Hostinger.\n\nHazlo desde la interfaz de configuración y vuelve a ejecutar la aplicación."
            )
            sys.exit()

        print("🔍 Iniciando proceso automatizado de extracción de URL de confirmación...")
        print("⏳ Esperando nuevos emails de 33mail.com...")
        
        # Usar la función automatizada para extraer la URL
        success, confirmation_url = wait_for_confirmation_email(timeout_seconds=45)
        
        if success and confirmation_url:
            print(f"✅ ¡URL de confirmación encontrada!")
            print(f"🔗 URL: {confirmation_url}")
            print(f"📋 URL extraída exitosamente del último email no leído de 33mail.com")
            
            # Abrir la URL de confirmación en el navegador
            print(f"🌐 Abriendo URL de confirmación en el navegador...")
            driver.get(confirmation_url)
            
            # Esperar a que aparezca el header de 33mail (máximo 1 minuto)
            print("🔍 Esperando a que aparezca el header de 33mail...")
            header_found = wait_for_33mail_header(driver, timeout_seconds=60)
            
            if header_found:
                print("✅ Header de 33mail encontrado - Email confirmado exitosamente!")
                return True
            else:
                print("❌ Timeout: No se pudo encontrar el header de 33mail en 1 minuto")
                return False
        else:
            print(f"❌ No se encontró ninguna URL de confirmación de 33mail.com en 45 segundos")
            print(f"💡 Verifica que tengas emails de 33mail.com en tu carpeta 'Confirmar' o bandeja de entrada")
            return False

    except Exception as e:
        print(f"❌ Error durante el proceso automatizado: {e}")
        return False
