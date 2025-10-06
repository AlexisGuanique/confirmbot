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

def wait_for_33mail_header(driver, confirmation_url, timeout_seconds=120):
    """
    Espera hasta que aparezca el header de 33mail en la página con reintentos automáticos
    
    Args:
        driver: WebDriver de Selenium
        confirmation_url: URL específica a recargar si no aparece el header
        timeout_seconds: Tiempo máximo de espera en segundos (default: 120)
    
    Returns:
        bool: True si encuentra el header, False si timeout
    """
    import time
    
    print(f"⏳ Esperando header de 33mail (timeout: {timeout_seconds}s)...")
    start_time = time.time()
    last_reload_time = start_time
    reload_interval = 60  # Recargar cada 60 segundos si no aparece
    
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
        
        # Verificar si necesita recargar la URL específica
        current_time = time.time()
        time_since_last_reload = current_time - last_reload_time
        
        if time_since_last_reload >= reload_interval:
            print("🔄 Recargando URL de confirmación...")
            try:
                driver.get(confirmation_url)
                last_reload_time = current_time
            except Exception as e:
                print(f"⚠️ Error al recargar URL: {e}")
                last_reload_time = current_time
        
        # Esperar 2 segundos antes del siguiente intento
        time.sleep(2)
    
    print(f"⏰ Timeout: No se encontró el header de 33mail en {timeout_seconds} segundos")
    return False

def login_to_hostinger(driver, email, password, final_email=None):
    """
    Nueva función simplificada que usa wait_for_confirmation_email para extraer URLs automáticamente
    
    Args:
        driver: WebDriver de Selenium
        email: Email de Hostinger
        password: Contraseña de Hostinger
        final_email: Email de destino que se está intentando confirmar (opcional)
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
        if final_email:
            print(f"🎯 Buscando email de confirmación para: {final_email}")
        else:
            print("⏳ Esperando nuevos emails de 33mail.com...")
        
        # Usar la función automatizada para extraer la URL
        success, confirmation_url = wait_for_confirmation_email(email, password, final_email, timeout_seconds=45)
        
        if success and confirmation_url:
            print(f"✅ ¡URL de confirmación encontrada!")
            print(f"🔗 URL: {confirmation_url}")
            print(f"📋 URL extraída exitosamente del último email no leído de 33mail.com")
            
            # Abrir la URL de confirmación en el navegador
            print(f"🌐 Abriendo URL de confirmación en el navegador...")
            driver.get(confirmation_url)
            
            # Esperar a que aparezca el header de 33mail (máximo 2 minutos)
            print("🔍 Esperando a que aparezca el header de 33mail...")
            header_found = wait_for_33mail_header(driver, confirmation_url, timeout_seconds=120)
            
            if header_found:
                print("✅ Header de 33mail encontrado - Email confirmado exitosamente!")
                return True
            else:
                print("❌ Timeout: No se pudo encontrar el header de 33mail en 2 minutos")
                return False
        else:
            if final_email:
                print(f"❌ No se encontró ninguna URL de confirmación de 33mail.com para '{final_email}' en 45 segundos")
                print(f"💡 Verifica que tengas emails de 33mail.com dirigidos a '{final_email}' en tu carpeta 'Confirmar' o bandeja de entrada")
            else:
                print(f"❌ No se encontró ninguna URL de confirmación de 33mail.com en 45 segundos")
                print(f"💡 Verifica que tengas emails de 33mail.com en tu carpeta 'Confirmar' o bandeja de entrada")
            return False

    except Exception as e:
        print(f"❌ Error durante el proceso automatizado: {e}")
        return False
