import os
import shutil
import tempfile
from tkinter import messagebox

def clear_selenium_cache():
    """Elimina los perfiles temporales de Selenium y limpia caché."""
    temp_dir = tempfile.gettempdir()  # Carpeta temporal del sistema
    for folder in os.listdir(temp_dir):
        if 'selenium-profile' in folder:
            folder_path = os.path.join(temp_dir, folder)
            if os.path.isdir(folder_path):
                try:
                    shutil.rmtree(folder_path)  # Elimina la carpeta y su contenido
                    print(f"✅ Caché de Selenium eliminada: {folder_path}")
                except Exception as e:
                    print(f"❌ Error al eliminar la carpeta: {e}")
                    messagebox.showerror("Error", f"Error al eliminar la carpeta: {e}")

def clear_browser_cache():
    """Elimina los archivos temporales y caché del navegador."""
    try:
        # Limpiar caché en la carpeta temporal del sistema
        temp_dir = tempfile.gettempdir()
        files = os.listdir(temp_dir)
        
        for file in files:
            file_path = os.path.join(temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Elimina directorios no necesarios
                print(f"✅ Eliminado: {file_path}")
            except PermissionError:
                print(f"⚠️ No se puede eliminar (acceso denegado): {file_path}")
            except Exception as e:
                print(f"❌ Error al eliminar {file_path}: {e}")
        messagebox.showinfo("Éxito", "Cache y archivos temporales eliminados correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al limpiar la caché: {e}")


def clear_disk_space():
    """Limpia el espacio en disco eliminando archivos temporales."""
    # Limpiar archivos temporales de Windows
    temp_dirs = [
        r"C:\Windows\Temp",
        r"C:\Users\{user}\AppData\Local\Temp".format(user=os.getenv("USERNAME"))
    ]

    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)  # Asegura que la carpeta se vuelva a crear
                print(f"✅ Espacio liberado en: {temp_dir}")
            except Exception as e:
                print(f"❌ Error al limpiar {temp_dir}: {e}")
                messagebox.showerror("Error", f"Error al liberar espacio en {temp_dir}: {e}")
    messagebox.showinfo("Éxito", "Espacio en disco liberado correctamente.")
