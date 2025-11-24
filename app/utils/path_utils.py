import os
import sys

def get_base_path():
    """
    Obtiene la ruta base correcta tanto en desarrollo como en el ejecutable.
    
    Returns:
        str: Ruta base donde se encuentra el ejecutable o el directorio de desarrollo
    """
    if getattr(sys, 'frozen', False):
        # Si estamos ejecutando desde un ejecutable (PyInstaller)
        # sys.executable apunta al ejecutable, así que obtenemos su directorio
        return os.path.dirname(sys.executable)
    else:
        # Si estamos en desarrollo, usar el directorio raíz del proyecto
        return os.path.abspath(".")

def get_images_path():
    """
    Obtiene la ruta de la carpeta de imágenes.
    En desarrollo: app/creator/images (primero) o ./images (fallback)
    En ejecutable: ./images (al lado del ejecutable)
    
    Returns:
        str: Ruta de la carpeta de imágenes
    """
    if getattr(sys, 'frozen', False):
        # Si estamos ejecutando desde un ejecutable (PyInstaller)
        return os.path.join(get_base_path(), "images")
    else:
        # Si estamos en desarrollo, buscar primero en app/creator/images
        dev_images_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "creator", "images")
        if os.path.exists(dev_images_path):
            return dev_images_path
        else:
            # Fallback a ./images si no existe la carpeta de desarrollo
            return os.path.join(get_base_path(), "images")

def get_browser_images_path(browser_name):
    """
    Obtiene la ruta de la carpeta de imágenes para un navegador específico.
    
    Args:
        browser_name (str): Nombre del navegador
    
    Returns:
        str: Ruta de la carpeta de imágenes del navegador
    """
    # Limpiar el nombre del navegador para usarlo como nombre de directorio
    # Reemplazar caracteres especiales y espacios
    safe_name = browser_name.strip()
    safe_name = safe_name.replace(" ", "_")
    safe_name = safe_name.replace("/", "_")
    safe_name = safe_name.replace("\\", "_")
    safe_name = safe_name.replace(":", "_")
    safe_name = safe_name.replace("*", "_")
    safe_name = safe_name.replace("?", "_")
    safe_name = safe_name.replace('"', "_")
    safe_name = safe_name.replace("<", "_")
    safe_name = safe_name.replace(">", "_")
    safe_name = safe_name.replace("|", "_")
    
    # Obtener la ruta base de imágenes
    base_images_path = get_images_path()
    
    # Crear ruta del navegador
    browser_images_path = os.path.join(base_images_path, safe_name)
    
    return browser_images_path

def get_linkedin_accounts_path():
    """
    Obtiene la ruta de la carpeta de cuentas de LinkedIn.
    En desarrollo: ./linkedin_accounts
    En ejecutable: ./linkedin_accounts (al lado del ejecutable)
    
    Returns:
        str: Ruta de la carpeta de cuentas de LinkedIn
    """
    return os.path.join(get_base_path(), "linkedin_accounts")

def ensure_directory_exists(directory_path):
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        directory_path (str): Ruta del directorio a crear
        
    Returns:
        bool: True si el directorio existe o se creó exitosamente
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error al crear directorio {directory_path}: {e}")
        return False
