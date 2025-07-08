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

        # 🔹 Tabla para almacenar las coordenadas de 3 clics
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY CHECK (id = 1),  -- Siempre 1
                first_click TEXT NOT NULL,   -- formato "200 x 200"
                second_click TEXT NOT NULL,
                third_click TEXT NOT NULL,
                fourth_click TEXT NOT NULL
            )
            '''
        )

        # ▶️ Asegurar que la columna fourth_click existe (migraciones antiguas)
        cursor.execute("PRAGMA table_info(actions)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        if "fourth_click" not in existing_cols:
            cursor.execute("ALTER TABLE actions ADD COLUMN fourth_click TEXT NOT NULL DEFAULT ''")

        # 🔹 Tabla para almacenar la clave de NopeCHA
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS nopecha_key (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                api_key TEXT NOT NULL
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


def save_click_coordinates(coordinates):

    if len(coordinates) != 4:
        print("❌ Debes proporcionar exactamente 4 coordenadas.")
        return False

    c1, c2, c3, c4 = map(_format_coord, coordinates)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("REPLACE INTO actions (id, first_click, second_click, third_click, fourth_click) VALUES (1, ?, ?, ?, ?)",
                       (c1, c2, c3, c4))

        conn.commit()
        conn.close()
        print("✅ Coordenadas guardadas exitosamente.")
        return True

    except Exception as e:
        print(f"❌ Error al guardar coordenadas: {e}")
        return False


def get_click_coordinates():
    """Devuelve un diccionario con las 3 coordenadas almacenadas o None."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT first_click, second_click, third_click, fourth_click FROM actions WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            "first_click": row[0],
            "second_click": row[1],
            "third_click": row[2],
            "fourth_click": row[3]
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
    """Obtiene la clave de NopeCHA almacenada, o None si no existe."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT api_key FROM nopecha_key WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]
        return None

    except Exception as e:
        print(f"❌ Error al obtener NopeCHA key: {e}")
        return None
