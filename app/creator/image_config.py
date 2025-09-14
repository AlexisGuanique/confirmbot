import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

def view_image(image_path, refresh_callback=None):
    """
    Abre una ventana para ver una imagen
    
    Args:
        image_path (str): Ruta de la imagen a mostrar
        refresh_callback (function): Función para refrescar la ventana principal después de eliminar
    """
    if not os.path.exists(image_path):
        messagebox.showerror("Error", f"La imagen no existe: {image_path}")
        return
    
    try:
        # Crear ventana para mostrar la imagen
        image_window = ctk.CTkToplevel()
        image_window.title(f"Vista de Imagen - {os.path.basename(image_path)}")
        image_window.geometry("500x400")
        image_window.configure(fg_color="#FFFFFF")
        
        # Centrar la ventana
        image_window.transient()
        image_window.grab_set()
        
        # Crear frame principal con scroll
        main_frame = ctk.CTkScrollableFrame(
            image_window,
            fg_color="transparent",
            scrollbar_button_color="#CCCCCC",
            scrollbar_button_hover_color="#AAAAAA"
        )
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cargar la imagen original
        original_image = Image.open(image_path)
        
        # Calcular tamaño máximo para la imagen (más pequeño)
        max_width, max_height = 300, 200
        
        # Redimensionar la imagen manteniendo proporción
        image = original_image.copy()
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convertir a CTkImage para evitar warnings
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
 
        # Información de la imagen
        info_text = f"Archivo: {os.path.basename(image_path)}"
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=("Arial", 12),
            text_color="black"
        )
        info_label.pack(pady=(0, 10))
        
        # Crear label para mostrar la imagen
        image_label = ctk.CTkLabel(
            main_frame,
            image=ctk_image,
            text="",  # Sin texto, solo imagen
            fg_color="transparent"
        )
        image_label.pack(pady=10)
        
        # Botón para eliminar imagen
        def delete_image():
            result = messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Estás seguro de que quieres eliminar esta imagen?\n\n{os.path.basename(image_path)}"
            )
            if result:
                if delete_image_file(image_path):
                    messagebox.showinfo("Éxito", "✅ Imagen eliminada correctamente.")
                    image_window.destroy()
                    # Refrescar la ventana principal si se proporciona el callback
                    if refresh_callback:
                        refresh_callback()
                else:
                    messagebox.showerror("Error", "❌ No se pudo eliminar la imagen.")
        
        delete_button = ctk.CTkButton(
            main_frame,
            text="🗑️ Eliminar Imagen",
            command=delete_image,
            fg_color="#dc3545",
            text_color="white",
            font=("Arial", 12),
            width=150,
            height=35
        )
        delete_button.pack(pady=(10, 20))
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir la imagen: {e}")


def load_image(image_name):
    """
    Permite al usuario cargar una imagen y la guarda en la carpeta /images
    
    Args:
        image_name (str): Nombre descriptivo de la imagen (para el archivo)
    
    Returns:
        str: Ruta de la imagen cargada o None si se canceló
    """
    try:
        # Crear carpeta /images si no existe
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Abrir diálogo para seleccionar imagen
        file_path = filedialog.askopenfilename(
            title=f"Cargar {image_name}",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("GIF", "*.gif"),
                ("BMP", "*.bmp"),
                ("TIFF", "*.tiff"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if not file_path:
            return None
        
        # Generar nombre de archivo basado en el nombre de la imagen
        # Convertir espacios y caracteres especiales a guiones bajos
        safe_name = image_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # Obtener extensión del archivo original
        file_extension = os.path.splitext(file_path)[1]
        
        # Crear nombre de archivo final
        final_filename = f"{safe_name}{file_extension}"
        final_path = os.path.join(images_dir, final_filename)
        
        # Copiar la imagen a la carpeta /images
        import shutil
        shutil.copy2(file_path, final_path)
        
        messagebox.showinfo("Éxito", f"✅ Imagen cargada correctamente:\n{final_filename}")
        
        return final_path
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la imagen: {e}")
        return None


def get_image_path(image_name):
    """
    Obtiene la ruta de una imagen si existe en la carpeta /images
    
    Args:
        image_name (str): Nombre descriptivo de la imagen
    
    Returns:
        str: Ruta de la imagen si existe, None si no existe
    """
    try:
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        
        if not os.path.exists(images_dir):
            return None
        
        # Buscar archivos que coincidan con el nombre
        safe_name = image_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # Buscar archivos con diferentes extensiones
        extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
        
        for ext in extensions:
            potential_path = os.path.join(images_dir, f"{safe_name}{ext}")
            if os.path.exists(potential_path):
                return potential_path
        
        return None
        
    except Exception as e:
        print(f"Error al buscar imagen: {e}")
        return None


def delete_image_file(image_path):
    """
    Elimina un archivo de imagen
    
    Args:
        image_path (str): Ruta de la imagen a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"✅ Imagen eliminada: {image_path}")
            return True
        else:
            print(f"❌ La imagen no existe: {image_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error al eliminar imagen: {e}")
        return False
