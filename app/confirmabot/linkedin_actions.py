"""
Módulo para manejar acciones automatizadas en LinkedIn
"""

from app.confirmabot.confirm_bot import open_chrome_profile
import time

def open_linkedin_window():
    """
    Abre una ventana de Chrome en LinkedIn para realizar acciones
    
    Returns:
        WebDriver: Instancia del navegador configurado
    """
    try:
        print("🌐 Abriendo ventana de LinkedIn...")
        
        # Inicializar el navegador con la configuración del bot
        driver = open_chrome_profile(incognito_mode=True)
        
        # Maximizar la ventana
        driver.maximize_window()
        
        # Navegar a LinkedIn
        print("📱 Navegando a LinkedIn...")
        driver.get("https://www.linkedin.com/signup?_l=us&trk=guest_homepage-basic_nav-header-join.com/")
        
        # Esperar un momento para que cargue la página
        time.sleep(3)
        
        print("✅ Ventana de LinkedIn abierta exitosamente")
        return driver
        
    except Exception as e:
        print(f"❌ Error al abrir LinkedIn: {e}")
        return None

def close_linkedin_window(driver):
    """
    Cierra la ventana de LinkedIn de forma segura
    
    Args:
        driver: Instancia del WebDriver a cerrar
    """
    try:
        if driver:
            driver.quit()
            print("🔒 Ventana de LinkedIn cerrada")
    except Exception as e:
        print(f"⚠️ Error al cerrar la ventana: {e}")

# Función principal para testing
if __name__ == "__main__":
    print("🧪 Probando funciones de LinkedIn...")
    
    # Abrir ventana
    driver = open_linkedin_window()
    
    if driver:
        print("✅ Prueba exitosa - LinkedIn abierto")
        
        # Esperar un poco para ver la página
        time.sleep(5)
        
        # Cerrar ventana
        close_linkedin_window(driver)
    else:
        print("❌ Prueba fallida")
