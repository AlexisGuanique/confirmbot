import os
import sys
import pyautogui
import time
import random
import string
import pyperclip
from faker import Faker
from app.creator.image_config import get_image_path
from app.utils.path_utils import get_base_path

def get_resource_path(relative_path):
    """
    Obtiene la ruta de un recurso tanto en desarrollo como en ejecutable.
    Esta función es específica para recursos que van dentro del ejecutable.
    Para archivos de usuario (imágenes, cuentas), usar get_base_path().
    """
    if getattr(sys, 'frozen', False):
        # Si estamos ejecutando desde un ejecutable (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Si estamos en desarrollo, usar el directorio raíz del proyecto
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def find_image(image_path, confidence=0.7, silent=False):
    """Busca una imagen en la pantalla y devuelve su ubicación si la encuentra."""
    image_path = get_resource_path(image_path)
    try:
        if not os.path.exists(image_path):
            #if not silent:
            #    print(f"⚠️ La imagen no existe: {image_path}")
            return None

        location = pyautogui.locateCenterOnScreen(
            image_path, confidence=confidence, grayscale=True)
        
        if location:
            #if not silent:
            #    print(f"✅ Imagen detectada: {image_path} en {location}")
            return location
        else:
            #if not silent:
            #    print(f"❌ Imagen no encontrada: {image_path}")
            pass

    except Exception as e:
        #if not silent:
        #    print(f"⚠️ Error detectando {image_path}: {e}")
        pass
    return None

def find_creator_image(image_name, confidence=0.7):
    """Busca una imagen del creator por su nombre."""
    image_path = get_image_path(image_name)
    if image_path:
        return find_image(image_path, confidence)
    return None

def image_exists(image_path, confidence=0.7):
    """Verifica si una imagen existe en la pantalla."""
    location = find_image(image_path, confidence)
    return location is not None

def creator_image_exists(image_name, confidence=0.7):
    """Verifica si una imagen del creator existe en la pantalla."""
    location = find_creator_image(image_name, confidence)
    return location is not None

def click_coordinates(coordinates, double_click=False, button='left'):
    """
    Hace click o doble click en coordenadas específicas
    """
    try:
        # Parsear las coordenadas del formato "EjeXxEjeY"
        if 'x' not in coordinates:
            print(f"⚠️ Formato de coordenadas inválido: {coordinates}")
            return False
        
        x_str, y_str = coordinates.split('x')
        x = int(x_str)
        y = int(y_str)
        
        # Configurar pyautogui
        pyautogui.PAUSE = 0.01
        pyautogui.FAILSAFE = False
        
        # Mover mouse a la posición
        #print(f"🖱️ Moviendo mouse a coordenadas: {x}, {y}")
        pyautogui.moveTo(x, y, duration=0.5)  # Movimiento más lento
        time.sleep(0.3)  # Esperar más tiempo a que llegue
        
        # Verificar que el mouse llegó a la posición correcta
        current_pos = pyautogui.position()
        #print(f"📍 Posición actual del mouse: {current_pos}")
        
        # Verificar si está cerca de la posición objetivo (tolerancia de 5 píxeles)
        if abs(current_pos.x - x) <= 5 and abs(current_pos.y - y) <= 5:
            #print("✅ Mouse en posición correcta, haciendo click")
            if double_click:
                # Doble click
                pyautogui.click(button=button)
                time.sleep(0.15)  # Delay entre clicks
                pyautogui.click(button=button)
            else:
                # Click simple
                pyautogui.click(button=button)
        else:
            #print(f"⚠️ Mouse no llegó a la posición correcta. Objetivo: ({x}, {y}), Actual: ({current_pos.x}, {current_pos.y})")
            return False
        
        return True
        
    except ValueError as e:
        print(f"⚠️ Error parseando coordenadas '{coordinates}': {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error haciendo click en coordenadas '{coordinates}': {e}")
        return False

def type_text(text):
    """
    Escribe texto usando el portapapeles (copiar y pegar)
    """
    try:
        # Guardar el contenido actual del portapapeles
        original_clipboard = pyperclip.paste()
        
        # Copiar el texto al portapapeles
        pyperclip.copy(text)
        time.sleep(0.1)  # Pequeña pausa para asegurar que se copió
        
        # Pegar usando Ctrl+V
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)  # Pequeña pausa después de pegar
        
        # Restaurar el contenido original del portapapeles
        pyperclip.copy(original_clipboard)
        
        #print(f"✅ Texto pegado: {text}")
        return True
    except Exception as e:
        print(f"⚠️ Error pegando texto '{text}': {e}")
        return False

def press_key(key):
    """
    Presiona una tecla específica
    """
    try:
        pyautogui.press(key)
        #print(f"✅ Tecla presionada: {key}")
        return True
    except Exception as e:
        print(f"⚠️ Error presionando tecla '{key}': {e}")
        return False

def generate_random_password(length=12):
    """
    Genera una contraseña aleatoria
    """
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def wait_for_image(image_path, max_attempts=10, delay_between_attempts=1, confidence=0.7, silent=False):

    if not silent:
        print(f"🔍 Iniciando observador para imagen: {os.path.basename(image_path)}")
        print(f"📊 Configuración: {max_attempts} intentos, {delay_between_attempts}s entre intentos")
    
    for attempt in range(1, max_attempts + 1):
        #if not silent:
        #    print(f"🔎 Intento {attempt}/{max_attempts}...")
        
        location = find_image(image_path, confidence, silent)
        if location:
            if not silent:
                print(f"✅ ¡Imagen encontrada en el intento {attempt}!")
            return location
        
        if attempt < max_attempts:
            #if not silent:
            #    print(f"⏳ Esperando {delay_between_attempts}s antes del siguiente intento...")
            time.sleep(delay_between_attempts)
    
    if not silent:
        print(f"❌ No se encontró la imagen después de {max_attempts} intentos")
    return None

def wait_for_creator_image(image_name, max_attempts=10, delay_between_attempts=1, confidence=0.7, silent=False):

    image_path = get_image_path(image_name)
    if not image_path:
        if not silent:
            print(f"❌ No se encontró la imagen del creator: {image_name}")
        return None
    
    return wait_for_image(image_path, max_attempts, delay_between_attempts, confidence, silent)

def generate_random_name():
    """
    Genera un nombre aleatorio usando faker
    """
    fake = Faker('es_ES')  # Usar español de España para nombres más comunes
    name = fake.first_name()
    return name

def generate_random_lastname():
    """
    Genera un apellido aleatorio usando faker
    """
    fake = Faker('es_ES')  # Usar español de España para apellidos más comunes
    lastname = fake.last_name()
    return lastname

def get_clipboard_content():
    """
    Obtiene el contenido del portapapeles
    """
    try:
        content = pyperclip.paste()
        return content
    except Exception as e:
        print(f"❌ Error obteniendo contenido del portapapeles: {e}")
        return ""