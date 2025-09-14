import os
import sys
import pyautogui
import time
from app.creator.image_config import get_image_path

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def find_image(image_path, confidence=0.7):
    """Busca una imagen en la pantalla y devuelve su ubicación si la encuentra."""
    image_path = get_resource_path(image_path)
    try:
        if not os.path.exists(image_path):
            print(f"⚠️ La imagen no existe: {image_path}")
            return None

        location = pyautogui.locateCenterOnScreen(
            image_path, confidence=confidence, grayscale=True)
        if location:
            print(f"✅ Imagen detectada: {image_path} en {location}")
            return location
        else:
            print(f"❌ Imagen no encontrada: {image_path}")

    except Exception as e:
        print(f"⚠️ Error detectando {image_path}: {e}")
    return None

def find_creator_image(image_name, confidence=0.7):
    """Busca una imagen del creator por su nombre."""
    image_path = get_image_path(image_name)
    if image_path:
        return find_image(image_path, confidence)
    return None

def image_exists(image_path, confidence=0.7):
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
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)  # Esperar a que llegue
        
        if double_click:
            # Doble click
            pyautogui.click(button=button)
            time.sleep(0.15)  # Delay entre clicks
            pyautogui.click(button=button)
        else:
            # Click simple
            pyautogui.click(button=button)
        
        return True
        
    except ValueError as e:
        print(f"⚠️ Error parseando coordenadas '{coordinates}': {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error haciendo click en coordenadas '{coordinates}': {e}")
        return False