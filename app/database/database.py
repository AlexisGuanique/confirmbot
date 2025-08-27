import os
import sys
import sqlite3



if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(
        __file__), "..", ".."))

DB_DIR = os.path.join(BASE_DIR, "app", "database")
DB_PATH = os.path.join(DB_DIR, "cookies.db")


def create_database():
    os.makedirs(DB_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        print(f"⚠️ Base de datos no encontrada en {DB_PATH}. Creando una nueva...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 🔹 Crear tabla de usuario
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY,  
                name TEXT NOT NULL,      
                lastname TEXT NOT NULL,  
                access_token TEXT NOT NULL 
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS bot_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iterations INTEGER NOT NULL
            )
            '''
        )

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                email_hostinger TEXT,
                password_hostinger TEXT
            );
            '''
        )

        # 🔹 Tabla para almacenar las coordenadas de 5 clics
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                first_click TEXT NOT NULL,
                second_click TEXT NOT NULL,
                third_click TEXT NOT NULL,
                fourth_click TEXT NOT NULL,
                fifth_click TEXT NOT NULL
            )
            '''
        )


        # 🔹 Tabla para almacenar la clave de NopeCHA
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS nopecha_key (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                api_key TEXT NOT NULL
            )
            '''
        )

        # 🔹 Tabla para almacenar correos del archivo .txt
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS txt_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        # 🔹 Tabla para almacenar el User Agent
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS user_agent (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_agent_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        conn.commit()
        conn.close()
        print(f"✅ Base de datos lista en {DB_PATH}")

    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")


#! FUNCIONES DE USERS
def save_user(user_data):

    try:
        conn = sqlite3.connect(DB_PATH)  # Usar ruta fija
        cursor = conn.cursor()

        # Insertar o reemplazar el usuario en la tabla
        cursor.execute(
            '''
            INSERT OR REPLACE INTO user (id, name, lastname, access_token)
            VALUES (?, ?, ?, ?)
            ''',
            (user_data["id"], user_data["name"],
             user_data["lastname"], user_data["access_token"])
        )

        conn.commit()
        # print(f"Usuario {user_data['name']} {
        #   user_data['lastname']} guardado exitosamente.")
    except sqlite3.IntegrityError as e:
        print(f"Error: No se pudo guardar el usuario. Detalles: {e}")
    finally:
        conn.close()


def get_logged_in_user():

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener al primer usuario registrado en la tabla `user`
        cursor.execute(
            "SELECT id, name, lastname, access_token FROM user LIMIT 1")
        user = cursor.fetchone()

        if user:
            user_data = {
                "id": user[0],
                "name": user[1],
                "lastname": user[2],
                "access_token": user[3]
            }
            return user_data
        else:
            # print("No hay ningún usuario logueado en la base de datos.")
            return None

    except sqlite3.Error as e:
        print(f"Error al obtener el usuario logueado: {e}")
        return None
    finally:
        conn.close()


def delete_logged_in_user():

    user = get_logged_in_user()

    if not user:
        print("No hay ningún usuario logueado para eliminar.")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Eliminar el usuario por su ID
        cursor.execute("DELETE FROM user WHERE id = ?", (user["id"],))
        conn.commit()
        # print(f"Usuario {user['name']} {user['lastname']} eliminado exitosamente de la base de datos.")
        return True

    except sqlite3.Error as e:
        print(f"Error al eliminar el usuario: {e}")
        return False
    finally:
        conn.close()


def clear_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Eliminar la tabla 'cookies' si existe
        cursor.execute('DROP TABLE IF EXISTS cookies')
        conn.commit()

        # Crear la tabla nuevamente
        cursor.execute('''
            CREATE TABLE cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie TEXT NOT NULL,
                email TEXT,
                password TEXT
            )
        ''')
        conn.commit()

        # print(
        #     f"Base de datos limpiada y reiniciada exitosamente en {DB_PATH}.")
    except Exception as e:
        print(f"Error al limpiar la base de datos: {e}")
    finally:
        conn.close()



def save_bot_settings(iterations):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificamos si ya hay una configuración guardada
        cursor.execute("SELECT id FROM bot_settings LIMIT 1")
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE bot_settings
                SET iterations = ?
                WHERE id = ?
            ''', (iterations, existing[0]))
        else:
            cursor.execute('''
                INSERT INTO bot_settings (iterations)
                VALUES (?)
            ''', (iterations,))

        conn.commit()
        conn.close()
        print("✅ Configuración de iteraciones guardada.")
        return True

    except Exception as e:
        print(f"❌ Error al guardar iteraciones: {e}")
        return False

def get_bot_settings():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT iterations FROM bot_settings LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"iterations": row[0]}
        else:
            return None
    except Exception as e:
        print(f"❌ Error al obtener configuración: {e}")
        return None



def save_emails(email, email_hostinger, password_hostinger):
    """Guarda un único email con las credenciales de Hostinger."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO emails (email, email_hostinger, password_hostinger)
            VALUES (?, ?, ?)
        ''', (email.strip(), email_hostinger, password_hostinger))

        conn.commit()
        conn.close()
        print(f"✅ Registro guardado: {email}")
        return True

    except Exception as e:
        print(f"❌ Error al guardar email y credenciales: {e}")
        return False


def get_all_emails():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT email, email_hostinger, password_hostinger FROM emails")
        rows = cursor.fetchall()
        conn.close()
        return [{"email": row[0], "email_hostinger": row[1], "password_hostinger": row[2]} for row in rows]
    except Exception as e:
        print(f"❌ Error al obtener emails: {e}")
        return []


def get_email_by_id(id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT email, email_hostinger, password_hostinger FROM emails WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "email": row[0],
                "email_hostinger": row[1],
                "password_hostinger": row[2]
            }
        return None
    except Exception as e:
        print(f"❌ Error al obtener el registro con ID {id}: {e}")
        return None



def clear_emails():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM emails")

        cursor.execute("DELETE FROM sqlite_sequence WHERE name='emails'")

        conn.commit()
        conn.close()
        print("✅ Todos los dominios fueron eliminados y los IDs reiniciados.")
        return True
    except Exception as e:
        print(f"❌ Error al eliminar dominios: {e}")
        return False




def get_email_count():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emails")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"❌ Error al contar emails: {e}")
        return 0



def _format_coord(value):
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"{value[0]} x {value[1]}"
    return str(value)


def save_partial_coordinates(coordinates_dict):
    """
    Guarda coordenadas específicas sin afectar las demás.
    
    Args:
        coordinates_dict (dict): Diccionario con las coordenadas a actualizar
                               Ejemplo: {"fourth_click": "200 x 300", "fifth_click": "400 x 500"}
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Construir la consulta SQL dinámicamente
        update_fields = []
        values = []
        
        for coord_name, coord_value in coordinates_dict.items():
            if coord_name in ["first_click", "second_click", "third_click", "fourth_click", "fifth_click"]:
                update_fields.append(f"{coord_name} = ?")
                values.append(_format_coord(coord_value))
        
        if not update_fields:
            print("❌ No se proporcionaron coordenadas válidas para actualizar.")
            return False
        
        # Construir y ejecutar la consulta UPDATE
        sql_query = f"UPDATE actions SET {', '.join(update_fields)} WHERE id = 1"
        
        # Ejecutar la consulta con solo los valores de las coordenadas
        cursor.execute(sql_query, values)
        
        # Verificar si se actualizó alguna fila
        if cursor.rowcount == 0:
            # Si no hay fila existente, crear una nueva
            print("📝 No existe registro previo. Creando nuevo registro...")
            
            # Crear registro con coordenadas por defecto
            default_coords = [""] * 5
            for coord_name, coord_value in coordinates_dict.items():
                coord_index = {"first_click": 0, "second_click": 1, "third_click": 2, 
                             "fourth_click": 3, "fifth_click": 4}[coord_name]
                default_coords[coord_index] = _format_coord(coord_value)
            
            return save_click_coordinates(default_coords)
        
        conn.commit()
        conn.close()
        
        updated_coords = ", ".join(coordinates_dict.keys())
        print(f"✅ Coordenadas actualizadas exitosamente: {updated_coords}")
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar coordenadas parciales: {e}")
        return False


def save_first_three_coordinates(coordinates):
    """
    Función de conveniencia para guardar solo first_click, second_click y third_click.
    
    Args:
        coordinates (list): Lista con exactamente 3 coordenadas [first, second, third]
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    if len(coordinates) != 3:
        print("❌ Debes proporcionar exactamente 3 coordenadas.")
        return False
    
    # Obtener coordenadas existentes para mantener fourth_click y fifth_click
    existing_coords = get_click_coordinates()
    
    # Preparar todas las coordenadas
    all_coords = [
        _format_coord(coordinates[0]),      # first_click
        _format_coord(coordinates[1]),      # second_click
        _format_coord(coordinates[2]),      # third_click
        existing_coords.get("fourth_click", "") if existing_coords else "",  # mantener fourth_click
        existing_coords.get("fifth_click", "") if existing_coords else ""    # mantener fifth_click
    ]
    
    # Usar la función existente para guardar
    return save_click_coordinates(all_coords)


def save_fourth_fifth_coordinates(fourth_coord, fifth_coord):
    """
    Función de conveniencia para guardar solo fourth_click y fifth_click.
    
    Args:
        fourth_coord: Coordenada para fourth_click (formato "200 x 300" o [200, 300])
        fifth_coord: Coordenada para fifth_click (formato "400 x 500" o [400, 500])
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    return save_partial_coordinates({
        "fourth_click": fourth_coord,
        "fifth_click": fifth_coord
    })


def save_click_coordinates(coordinates):

    if len(coordinates) != 5:
        print("❌ Debes proporcionar exactamente 5 coordenadas.")
        return False

    c1, c2, c3, c4, c5 = map(_format_coord, coordinates)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("REPLACE INTO actions (id, first_click, second_click, third_click, fourth_click, fifth_click) VALUES (1, ?, ?, ?, ?, ?)",
                       (c1, c2, c3, c4, c5))

        conn.commit()
        conn.close()
        print("✅ Coordenadas guardadas exitosamente.")
        return True

    except Exception as e:
        print(f"❌ Error al guardar coordenadas: {e}")
        return False


def get_click_coordinates():
    """Devuelve un diccionario con las 5 coordenadas almacenadas o None."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT first_click, second_click, third_click, fourth_click, fifth_click FROM actions WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            "first_click": row[0],
            "second_click": row[1],
            "third_click": row[2],
            "fourth_click": row[3],
            "fifth_click": row[4]
        }

    except Exception as e:
        print(f"❌ Error al obtener coordenadas: {e}")
        return None


# =================================
#         NOPECHA KEY
# =================================

def save_nopecha_key(api_key: str):
    """Guarda o reemplaza la clave de NopeCHA."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "REPLACE INTO nopecha_key (id, api_key) VALUES (1, ?)",
            (api_key.strip(),)
        )

        conn.commit()
        conn.close()
        print("✅ NopeCHA key guardada.")
        return True

    except Exception as e:
        print(f"❌ Error al guardar NopeCHA key: {e}")
        return False


def get_nopecha_key():
    """Obtiene la clave de NopeCHA almacenada."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT api_key FROM nopecha_key WHERE id = 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener la clave de NopeCHA: {e}")
        return None


# ================= FUNCIONES PARA CORREOS DEL ARCHIVO .TXT =================

def save_txt_emails(emails_list):
    """
    Guarda una lista de correos en la tabla txt_emails.
    
    Args:
        emails_list (list): Lista de correos electrónicos
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        emails_guardados = 0
        emails_duplicados = 0
        
        for email in emails_list:
            try:
                cursor.execute(
                    "INSERT INTO txt_emails (email) VALUES (?)",
                    (email,)
                )
                emails_guardados += 1
            except sqlite3.IntegrityError:
                # El correo ya existe (UNIQUE constraint)
                emails_duplicados += 1
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Se guardaron {emails_guardados} correos nuevos")
        if emails_duplicados > 0:
            print(f"⚠️ Se ignoraron {emails_duplicados} correos duplicados")
        
        return emails_guardados > 0
        
    except Exception as e:
        print(f"❌ Error al guardar correos del archivo .txt: {e}")
        return False


def get_txt_emails_count():
    """
    Obtiene el total de correos almacenados en txt_emails.
    
    Returns:
        int: Número total de correos almacenados
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM txt_emails")
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        print(f"❌ Error al obtener el conteo de correos: {e}")
        return 0


def get_txt_email_by_id(email_id):
    """
    Obtiene un correo específico por su ID.
    
    Args:
        email_id (int): ID del correo a obtener
    
    Returns:
        dict: Diccionario con la información del correo o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, email, created_at FROM txt_emails WHERE id = ?",
            (email_id,)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "created_at": result[2]
            }
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener correo por ID: {e}")
        return None


def get_all_txt_emails():
    """
    Obtiene todos los correos almacenados en txt_emails.
    
    Returns:
        list: Lista de diccionarios con la información de todos los correos
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, email, created_at FROM txt_emails ORDER BY id ASC"
        )
        results = cursor.fetchall()
        
        conn.close()
        
        emails = []
        for result in results:
            emails.append({
                "id": result[0],
                "email": result[1],
                "created_at": result[2]
            })
        
        return emails
        
    except Exception as e:
        print(f"❌ Error al obtener todos los correos: {e}")
        return []


def clear_txt_emails():
    """
    Elimina todos los correos almacenados en txt_emails y reinicia los IDs.
    
    Returns:
        bool: True si se eliminaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Eliminar todos los correos
        cursor.execute("DELETE FROM txt_emails")
        deleted_count = cursor.rowcount
        
        # Reiniciar el contador de IDs (AUTOINCREMENT)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='txt_emails'")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Se eliminaron {deleted_count} correos de la tabla txt_emails")
        print("🔄 IDs reiniciados - el próximo email tendrá ID 1")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar correos: {e}")
        return False


def delete_txt_email_by_id(email_id):
    """
    Elimina un correo específico por su ID.
    
    Args:
        email_id (int): ID del correo a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM txt_emails WHERE id = ?",
            (email_id,)
        )
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            print(f"✅ Correo con ID {email_id} eliminado correctamente")
            return True
        else:
            conn.close()
            print(f"⚠️ No se encontró correo con ID {email_id}")
            return False
        
    except Exception as e:
        print(f"❌ Error al eliminar correo por ID: {e}")
        return False

# ================= FUNCIONES PARA USER AGENT =================

def save_user_agent(user_agent_text):
    """
    Guarda o actualiza el User Agent en la base de datos
    
    Args:
        user_agent_text (str): Texto del User Agent a guardar
    
    Returns:
        bool: True si se guardó exitosamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si ya existe un registro
        cursor.execute("SELECT COUNT(*) FROM user_agent WHERE id = 1")
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            # Actualizar el registro existente
            cursor.execute(
                "UPDATE user_agent SET user_agent_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
                (user_agent_text,)
            )
            print(f"✅ User Agent actualizado: {user_agent_text}")
        else:
            # Crear nuevo registro
            cursor.execute(
                "INSERT INTO user_agent (id, user_agent_text) VALUES (1, ?)",
                (user_agent_text,)
            )
            print(f"✅ User Agent guardado: {user_agent_text}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar User Agent: {e}")
        return False

def get_user_agent():
    """
    Obtiene el User Agent almacenado en la base de datos
    
    Returns:
        str: User Agent almacenado o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_agent_text FROM user_agent WHERE id = 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error al obtener User Agent: {e}")
        return None

def delete_user_agent():
    """
    Elimina el User Agent almacenado en la base de datos
    
    Returns:
        bool: True si se eliminó exitosamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_agent WHERE id = 1")
        
        if cursor.rowcount > 0:
            print("✅ User Agent eliminado exitosamente")
            conn.commit()
            conn.close()
            return True
        else:
            print("⚠️ No había User Agent para eliminar")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error al eliminar User Agent: {e}")
        return False

def get_user_agent_info():
    """
    Obtiene información completa del User Agent (texto, fecha creación, fecha actualización)
    
    Returns:
        dict: Diccionario con la información del User Agent o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_agent_text, created_at, updated_at FROM user_agent WHERE id = 1"
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                "user_agent_text": result[0],
                "created_at": result[1],
                "updated_at": result[2]
            }
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error al obtener información del User Agent: {e}")
        return None

def user_agent_exists():
    """
    Verifica si existe un User Agent en la base de datos
    
    Returns:
        bool: True si existe, False si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user_agent WHERE id = 1")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count > 0
        
    except Exception as e:
        print(f"❌ Error al verificar existencia del User Agent: {e}")
        return False
