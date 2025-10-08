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

        # 🔹 Crear tabla de versiones de migración
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER UNIQUE NOT NULL,
                description TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

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
                iterations INTEGER NOT NULL,
                pause_minutes INTEGER NOT NULL DEFAULT 20
            )
            '''
        )
        
        # 🔄 SISTEMA DE MIGRACIONES PARA BOT_SETTINGS
        print("🔄 Verificando migraciones de bot_settings...")
        
        # Obtener columnas existentes
        cursor.execute("PRAGMA table_info(bot_settings)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Migración 1: Agregar pause_minutes si no existe
        if 'pause_minutes' not in existing_columns:
            print("🔄 Aplicando migración: agregando columna pause_minutes...")
            try:
                cursor.execute("ALTER TABLE bot_settings ADD COLUMN pause_minutes INTEGER NOT NULL DEFAULT 20")
                print("✅ Migración pause_minutes aplicada exitosamente")
            except Exception as e:
                print(f"⚠️ Error en migración pause_minutes: {e}")
        
        # Migración 2: Agregar enable_adb si no existe
        if 'enable_adb' not in existing_columns:
            print("🔄 Aplicando migración: agregando columna enable_adb...")
            try:
                cursor.execute("ALTER TABLE bot_settings ADD COLUMN enable_adb INTEGER NOT NULL DEFAULT 1")
                print("✅ Migración enable_adb aplicada exitosamente")
            except Exception as e:
                print(f"⚠️ Error en migración enable_adb: {e}")
        
        # Migración 3: Agregar enable_proxy si no existe
        if 'enable_proxy' not in existing_columns:
            print("🔄 Aplicando migración: agregando columna enable_proxy...")
            try:
                cursor.execute("ALTER TABLE bot_settings ADD COLUMN enable_proxy INTEGER NOT NULL DEFAULT 1")
                print("✅ Migración enable_proxy aplicada exitosamente")
            except Exception as e:
                print(f"⚠️ Error en migración enable_proxy: {e}")
        
        # Migración 4: Agregar emails_per_batch si no existe
        if 'emails_per_batch' not in existing_columns:
            print("🔄 Aplicando migración: agregando columna emails_per_batch...")
            try:
                cursor.execute("ALTER TABLE bot_settings ADD COLUMN emails_per_batch INTEGER NOT NULL DEFAULT 5")
                print("✅ Migración emails_per_batch aplicada exitosamente")
            except Exception as e:
                print(f"⚠️ Error en migración emails_per_batch: {e}")
        
        print("✅ Verificación de migraciones de bot_settings completada")

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

        # 🔹 Tabla para almacenar coordenadas de clicks del creator
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_coordinates (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                brave_click TEXT NOT NULL,
                linkedin_fav_click TEXT NOT NULL,
                email_input_click TEXT NOT NULL,
                continue_button_click TEXT NOT NULL,
                name_input_click TEXT NOT NULL,
                continue_button2_click TEXT NOT NULL,
                close_captcha_click TEXT NOT NULL,
                close_number_click TEXT NOT NULL,
                cookie_editor_icon_click TEXT NOT NULL,
                save_cookie_clipboard_click TEXT NOT NULL,
                close_window TEXT NOT NULL,
                continue_button_click_optional TEXT NOT NULL,
                white_captcha_click TEXT NOT NULL
            )
            '''
        )
        
        # Migrar tabla existente si no tiene la columna close_window
        try:
            cursor.execute("ALTER TABLE creator_coordinates ADD COLUMN close_window TEXT NOT NULL DEFAULT ''")
            print("✅ Columna close_window agregada a creator_coordinates")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
        
        # Migrar tabla existente si no tiene la columna continue_button_click_optional
        try:
            cursor.execute("ALTER TABLE creator_coordinates ADD COLUMN continue_button_click_optional TEXT")
            print("✅ Columna continue_button_click_optional agregada a creator_coordinates")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
        
        # Migrar tabla existente si no tiene la columna white_captcha_click
        try:
            cursor.execute("ALTER TABLE creator_coordinates ADD COLUMN white_captcha_click TEXT NOT NULL DEFAULT ''")
            print("✅ Columna white_captcha_click agregada a creator_coordinates")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
        
        # 🔄 MIGRACIÓN ESPECIAL: Verificar y corregir estructura de creator_coordinates
        print("🔄 Verificando estructura de creator_coordinates...")
        cursor.execute("PRAGMA table_info(creator_coordinates)")
        creator_columns = [col[1] for col in cursor.fetchall()]
        
        expected_creator_columns = [
            'id', 'brave_click', 'linkedin_fav_click', 'email_input_click',
            'continue_button_click', 'name_input_click', 'continue_button2_click',
            'close_captcha_click', 'close_number_click', 'cookie_editor_icon_click',
            'save_cookie_clipboard_click', 'close_window', 'continue_button_click_optional',
            'white_captcha_click'
        ]
        
        # Si la tabla no tiene la estructura correcta, recrearla
        if len(creator_columns) != len(expected_creator_columns) or not all(col in creator_columns for col in expected_creator_columns):
            print("🔄 Recreando tabla creator_coordinates con estructura correcta...")
            
            # Obtener datos existentes si los hay
            cursor.execute("SELECT * FROM creator_coordinates WHERE id = 1")
            existing_data = cursor.fetchone()
            
            # Eliminar la tabla existente
            cursor.execute("DROP TABLE IF EXISTS creator_coordinates")
            
            # Crear la tabla con la estructura correcta
            cursor.execute('''
                CREATE TABLE creator_coordinates (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    brave_click TEXT NOT NULL,
                    linkedin_fav_click TEXT NOT NULL,
                    email_input_click TEXT NOT NULL,
                    continue_button_click TEXT NOT NULL,
                    name_input_click TEXT NOT NULL,
                    continue_button2_click TEXT NOT NULL,
                    close_captcha_click TEXT NOT NULL,
                    close_number_click TEXT NOT NULL,
                    cookie_editor_icon_click TEXT NOT NULL,
                    save_cookie_clipboard_click TEXT NOT NULL,
                    close_window TEXT NOT NULL,
                    continue_button_click_optional TEXT NOT NULL,
                    white_captcha_click TEXT NOT NULL
                )
            ''')
            
            # Restaurar datos existentes si los hay
            if existing_data:
                # Asegurar que tenemos 13 valores de datos (excluyendo id)
                values = list(existing_data[1:])  # Excluir id
                while len(values) < 13:  # Asegurar que tenemos 13 valores de datos
                    values.append('')
                
                cursor.execute('''
                    INSERT INTO creator_coordinates (
                        id, brave_click, linkedin_fav_click, email_input_click,
                        continue_button_click, name_input_click, continue_button2_click,
                        close_captcha_click, close_number_click, cookie_editor_icon_click,
                        save_cookie_clipboard_click, close_window, continue_button_click_optional,
                        white_captcha_click
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(values))
            
            print("✅ Tabla creator_coordinates recreada con estructura correcta")
        else:
            print("✅ Tabla creator_coordinates ya tiene la estructura correcta")

        # 🔹 Tabla para configuración del creator
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_setting (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_agent TEXT NOT NULL,
                accounts_to_create INTEGER NOT NULL DEFAULT 1,
                scheduled_time TEXT,
                timezone TEXT,
                notification_email TEXT,
                google_sheets_enabled INTEGER DEFAULT 0,
                google_sheets_name TEXT,
                google_credentials_file TEXT,
                cycle_time_minutes INTEGER DEFAULT 60,
                time_config_type TEXT DEFAULT 'scheduled',
                accounts_per_cycle INTEGER DEFAULT 1
            )
            '''
        )
        
        # Agregar columnas de hora programada si no existen
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN scheduled_time TEXT")
            print("✅ Columna scheduled_time agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN timezone TEXT")
            print("✅ Columna timezone agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN notification_email TEXT")
            print("✅ Columna notification_email agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN google_sheets_enabled INTEGER DEFAULT 0")
            print("✅ Columna google_sheets_enabled agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN google_sheets_name TEXT")
            print("✅ Columna google_sheets_name agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN google_credentials_file TEXT")
            print("✅ Columna google_credentials_file agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN cycle_time_minutes INTEGER DEFAULT 60")
            print("✅ Columna cycle_time_minutes agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN time_config_type TEXT DEFAULT 'scheduled'")
            print("✅ Columna time_config_type agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass
            
        try:
            cursor.execute("ALTER TABLE creator_setting ADD COLUMN accounts_per_cycle INTEGER DEFAULT 1")
            print("✅ Columna accounts_per_cycle agregada a creator_setting")
        except sqlite3.OperationalError:
            # La columna ya existe, no hacer nada
            pass

        # 🔹 Tabla para emails del creator
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_email (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        # 🔹 Tabla para rastrear el progreso de emails del creator
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_email_progress (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_used_email_id INTEGER DEFAULT 0,
                total_emails_used INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )

        conn.commit()
        conn.close()
        print(f"✅ Base de datos lista en {DB_PATH}")
        
        # Ejecutar migraciones automáticamente
        run_migrations()

    except Exception as e:
        print(f"❌ Error al crear la base de datos: {e}")


def run_migrations():
    """
    Ejecuta migraciones automáticamente basándose en la versión actual
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Obtener la versión actual de migración
        cursor.execute("SELECT MAX(version) FROM migrations")
        current_version = cursor.fetchone()[0] or 0
        
        print(f"🔄 Versión actual de migración: {current_version}")
        
        # Definir migraciones pendientes
        migrations = [
            {
                'version': 1,
                'description': 'Agregar columna white_captcha_click a creator_coordinates',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN white_captcha_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 2,
                'description': 'Eliminar columna duplicada close_captcha_white_click',
                'sql': "ALTER TABLE creator_coordinates DROP COLUMN close_captcha_white_click"
            },
            {
                'version': 3,
                'description': 'Agregar columna white_captcha_click después de eliminar duplicada',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN white_captcha_click TEXT NOT NULL DEFAULT ''"
            }
        ]
        
        # Ejecutar migraciones pendientes
        for migration in migrations:
            if migration['version'] > current_version:
                try:
                    print(f"🔄 Ejecutando migración {migration['version']}: {migration['description']}")
                    cursor.execute(migration['sql'])
                    
                    # Registrar la migración
                    cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        (migration['version'], migration['description'])
                    )
                    
                    print(f"✅ Migración {migration['version']} completada")
                    
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower() or "no such column" in str(e).lower():
                        print(f"⚠️ Migración {migration['version']} ya aplicada o no aplicable: {e}")
                        # Registrar como aplicada para evitar intentos futuros
                        try:
                            cursor.execute(
                                "INSERT INTO migrations (version, description) VALUES (?, ?)",
                                (migration['version'], migration['description'])
                            )
                        except sqlite3.IntegrityError:
                            pass  # Ya existe
                    else:
                        print(f"❌ Error en migración {migration['version']}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Migraciones completadas")
        
    except Exception as e:
        print(f"❌ Error al ejecutar migraciones: {e}")


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



def save_bot_settings(iterations, pause_minutes=20, enable_adb=True, enable_proxy=True, emails_per_batch=5):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificamos si ya hay una configuración guardada
        cursor.execute("SELECT id FROM bot_settings LIMIT 1")
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE bot_settings
                SET iterations = ?, pause_minutes = ?, enable_adb = ?, enable_proxy = ?, emails_per_batch = ?
                WHERE id = ?
            ''', (iterations, pause_minutes, int(enable_adb), int(enable_proxy), emails_per_batch, existing[0]))
        else:
            cursor.execute('''
                INSERT INTO bot_settings (iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch)
                VALUES (?, ?, ?, ?, ?)
            ''', (iterations, pause_minutes, int(enable_adb), int(enable_proxy), emails_per_batch))

        conn.commit()
        conn.close()
        print("✅ Configuración de bot guardada.")
        return True

    except Exception as e:
        print(f"❌ Error al guardar configuración: {e}")
        return False

def get_bot_settings():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch FROM bot_settings LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "iterations": row[0], 
                "pause_minutes": row[1],
                "enable_adb": bool(row[2]),
                "enable_proxy": bool(row[3]),
                "emails_per_batch": row[4]
            }
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


def save_creator_coordinates(coordinates_dict=None, **kwargs):

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener coordenadas existentes
        cursor.execute("SELECT * FROM creator_coordinates WHERE id = 1")
        existing_row = cursor.fetchone()
        
        # Preparar valores con los existentes como base
        if existing_row:
            values = list(existing_row[1:])  # Excluir el id
            # Asegurar que tenemos exactamente 13 valores (14 columnas - 1 id)
            while len(values) < 13:
                values.append('')
            values = values[:13]  # Limitar a 13 valores máximo
        else:
            values = [''] * 13  # 13 campos de datos (sin id)

        # Mapeo de nombres de campos a índices (0-12 para 13 campos)
        field_mapping = {
            'brave_click': 0,
            'linkedin_fav_click': 1,
            'email_input_click': 2,
            'continue_button_click': 3,
            'name_input_click': 4,
            'continue_button2_click': 5,
            'close_captcha_click': 6,
            'close_number_click': 7,
            'cookie_editor_icon_click': 8,
            'save_cookie_clipboard_click': 9,
            'close_window': 10,
            'continue_button_click_optional': 11,
            'white_captcha_click': 12
        }

        # Actualizar valores desde coordinates_dict si se proporciona
        if coordinates_dict:
            for field, coord in coordinates_dict.items():
                if field in field_mapping:
                    values[field_mapping[field]] = coord

        # Actualizar valores desde kwargs
        for field, coord in kwargs.items():
            if field in field_mapping:
                values[field_mapping[field]] = coord

        cursor.execute(
            """
            REPLACE INTO creator_coordinates (
                id, brave_click, linkedin_fav_click, email_input_click,
                continue_button_click, name_input_click, continue_button2_click,
                close_captcha_click, close_number_click, cookie_editor_icon_click,
                save_cookie_clipboard_click, close_window, continue_button_click_optional,
                white_captcha_click
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(values)
        )

        conn.commit()
        conn.close()
        print("✅ Coordenadas del creator guardadas.")
        return True

    except Exception as e:
        print(f"❌ Error al guardar coordenadas del creator: {e}")
        return False


def get_creator_coordinates(*field_names):

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM creator_coordinates WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Mapeo de nombres de campos a índices
        field_mapping = {
            'brave_click': 1,
            'linkedin_fav_click': 2,
            'email_input_click': 3,
            'continue_button_click': 4,
            'name_input_click': 5,
            'continue_button2_click': 6,
            'close_captcha_click': 7,
            'close_number_click': 8,
            'cookie_editor_icon_click': 9,
            'save_cookie_clipboard_click': 10,
            'close_window': 11,
            'continue_button_click_optional': 12,
            'white_captcha_click': 13
        }

        # Si no se especifican campos, devolver todos
        if not field_names:
            return {
                'brave_click': row[1],
                'linkedin_fav_click': row[2],
                'email_input_click': row[3],
                'continue_button_click': row[4],
                'name_input_click': row[5],
                'continue_button2_click': row[6],
                'close_captcha_click': row[7],
                'close_number_click': row[8],
                'cookie_editor_icon_click': row[9],
                'save_cookie_clipboard_click': row[10],
                'close_window': row[11],
                'continue_button_click_optional': row[12],
                'white_captcha_click': row[13]
            }

        # Devolver solo los campos solicitados
        result = {}
        for field_name in field_names:
            if field_name in field_mapping:
                result[field_name] = row[field_mapping[field_name]]

        return result if result else None

    except Exception as e:
        print(f"❌ Error al obtener coordenadas del creator: {e}")
        return None


#! FUNCIONES DE CREATOR_SETTING
def save_creator_setting(user_agent, accounts_to_create=1, scheduled_time=None, timezone=None, notification_email=None, cycle_time_minutes=None, time_config_type='manual', accounts_per_cycle=None):
    """
    Guarda o actualiza la configuración del creator
    
    Args:
        user_agent (str): User agent a utilizar
        accounts_to_create (int): Cantidad de cuentas a crear (default: 1)
        scheduled_time (str): Hora programada en formato HH:MM (opcional)
        timezone (str): Zona horaria (opcional)
        notification_email (str): Email para recibir notificaciones (opcional)
        cycle_time_minutes (int): Tiempo en minutos para el ciclo (default: 60)
        time_config_type (str): Tipo de configuración ('scheduled' o 'cycle')
        accounts_per_cycle (int): Cantidad de cuentas a crear por ciclo (default: 1)
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insertar o actualizar (UPSERT)
        cursor.execute('''
            INSERT OR REPLACE INTO creator_setting (id, user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle))
        
        conn.commit()
        conn.close()
        print(f"✅ Configuración del creator guardada: UA={user_agent}, Cuentas={accounts_to_create}, Hora={scheduled_time}, Zona={timezone}, Notificación={notification_email}, Ciclo={cycle_time_minutes}min, Tipo={time_config_type}, CuentasPorCiclo={accounts_per_cycle}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar configuración del creator: {e}")
        return False


def get_creator_setting():
    """
    Obtiene la configuración del creator
    
    Returns:
        dict: Diccionario con user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type y accounts_per_cycle, o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle FROM creator_setting WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_agent': row[0],
                'accounts_to_create': row[1],
                'scheduled_time': row[2],
                'timezone': row[3],
                'notification_email': row[4],
                'cycle_time_minutes': row[5],  # Mantener el valor real, incluso si es None
                'time_config_type': row[6] if row[6] is not None else 'manual',  # Cambiar default a 'manual'
                'accounts_per_cycle': row[7]  # Mantener el valor real, incluso si es None
            }
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener configuración del creator: {e}")
        return None


def clear_scheduled_time():
    """
    Elimina la hora programada de la configuración del creator
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Actualizar solo los campos de hora programada
        cursor.execute('''
            UPDATE creator_setting 
            SET scheduled_time = NULL, timezone = NULL 
            WHERE id = 1
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Hora programada eliminada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar hora programada: {e}")
        return False


#! FUNCIONES DE CREATOR_EMAIL
def save_creator_email(email):
    """
    Guarda un email en la tabla creator_email
    
    Args:
        email (str): Email a guardar (formato: holamundo@hola.com)
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO creator_email (email)
            VALUES (?)
        ''', (email,))
        
        conn.commit()
        conn.close()
        print(f"✅ Email guardado: {email}")
        return True
        
    except sqlite3.IntegrityError:
        print(f"⚠️ El email {email} ya existe en la base de datos")
        return False
    except Exception as e:
        print(f"❌ Error al guardar email: {e}")
        return False


def get_all_creator_emails():
    """
    Obtiene todos los emails de la tabla creator_email
    
    Returns:
        list: Lista de emails, o lista vacía si no hay emails
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM creator_email ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        emails = [row[0] for row in rows]
        #print(f"📧 Se encontraron {len(emails)} emails")
        return emails
        
    except Exception as e:
        print(f"❌ Error al obtener emails: {e}")
        return []


def get_creator_email_count():
    """
    Obtiene la cantidad de emails en la tabla creator_email
    
    Returns:
        int: Cantidad de emails, 0 si no hay emails o error
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM creator_email")
        count = cursor.fetchone()[0]
        conn.close()
        
        #print(f"📊 Total de emails: {count}")
        return count
        
    except Exception as e:
        print(f"❌ Error al contar emails: {e}")
        return 0


def delete_all_creator_emails():
    """
    Elimina todos los emails de la tabla creator_email y reinicia los IDs
    
    Returns:
        bool: True si se eliminaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar emails antes de eliminar
        cursor.execute("SELECT COUNT(*) FROM creator_email")
        count_before = cursor.fetchone()[0]
        
        # Eliminar todos los emails
        cursor.execute("DELETE FROM creator_email")
        
        # Reiniciar el contador de AUTOINCREMENT
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='creator_email'")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Se eliminaron {count_before} emails y se reiniciaron los IDs")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar todos los emails: {e}")
        return False

def get_creator_email_by_id(id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM creator_email WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return row[0]
    except Exception as e:
        print(f"❌ Error al obtener email por ID: {e}")
        return None


def get_all_creator_email_ids():
    """
    Obtiene todos los IDs de emails de la tabla creator_email
    
    Returns:
        list: Lista de IDs de emails, o lista vacía si no hay emails
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM creator_email ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        ids = [row[0] for row in rows]
        #print(f"📧 Se encontraron {len(ids)} emails con IDs")
        return ids
        
    except Exception as e:
        print(f"❌ Error al obtener IDs de emails: {e}")
        return []


def load_emails_from_file(file_path):
    """
    Carga emails desde un archivo .txt y los guarda en la tabla creator_email
    
    Args:
        file_path (str): Ruta del archivo .txt con emails
    
    Returns:
        dict: Resultado con estadísticas de la carga
    """
    try:
        # Leer el archivo
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            return {
                'success': False,
                'message': 'El archivo está vacío',
                'total_lines': 0,
                'valid_emails': 0,
                'saved_emails': 0,
                'duplicate_emails': 0,
                'invalid_emails': 0
            }
        
        # Validar formato de email (debe contener @ y .)
        valid_emails = []
        invalid_emails = []
        
        for line in lines:
            if '@' in line and '.' in line and len(line) > 5:
                valid_emails.append(line)
            else:
                invalid_emails.append(line)
        
        if not valid_emails:
            return {
                'success': False,
                'message': 'No se encontraron emails válidos en el archivo',
                'total_lines': len(lines),
                'valid_emails': 0,
                'saved_emails': 0,
                'duplicate_emails': 0,
                'invalid_emails': len(invalid_emails)
            }
        
        # Guardar emails válidos en la base de datos
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        saved_count = 0
        duplicate_count = 0
        
        for email in valid_emails:
            try:
                cursor.execute("INSERT INTO creator_email (email) VALUES (?)", (email,))
                saved_count += 1
            except sqlite3.IntegrityError:
                duplicate_count += 1
                print(f"⚠️ Email duplicado: {email}")
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f'Carga completada exitosamente',
            'total_lines': len(lines),
            'valid_emails': len(valid_emails),
            'saved_emails': saved_count,
            'duplicate_emails': duplicate_count,
            'invalid_emails': len(invalid_emails)
        }
        
    except FileNotFoundError:
        return {
            'success': False,
            'message': 'El archivo no existe',
            'total_lines': 0,
            'valid_emails': 0,
            'saved_emails': 0,
            'duplicate_emails': 0,
            'invalid_emails': 0
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al procesar el archivo: {e}',
            'total_lines': 0,
            'valid_emails': 0,
            'saved_emails': 0,
            'duplicate_emails': 0,
            'invalid_emails': 0
        }


#! FUNCIONES DE PROGRESO DE EMAILS DEL CREATOR
def get_creator_email_progress():
    """
    Obtiene el progreso actual de emails del creator
    
    Returns:
        dict: Diccionario con last_used_email_id, total_emails_used y last_updated, o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT last_used_email_id, total_emails_used, last_updated FROM creator_email_progress WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'last_used_email_id': row[0],
                'total_emails_used': row[1],
                'last_updated': row[2]
            }
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener progreso de emails: {e}")
        return None


def update_creator_email_progress(last_used_email_id, total_emails_used):
    """
    Actualiza el progreso de emails del creator
    
    Args:
        last_used_email_id (int): ID del último email usado
        total_emails_used (int): Total de emails usados
    
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insertar o actualizar (UPSERT)
        cursor.execute('''
            INSERT OR REPLACE INTO creator_email_progress (id, last_used_email_id, total_emails_used, last_updated)
            VALUES (1, ?, ?, CURRENT_TIMESTAMP)
        ''', (last_used_email_id, total_emails_used))
        
        conn.commit()
        conn.close()
        # Progreso actualizado silenciosamente
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar progreso de emails: {e}")
        return False


def get_creator_emails_with_offset(limit, offset=0):
    """
    Obtiene emails del creator con offset para avanzar por la lista
    
    Args:
        limit (int): Cantidad de emails a obtener
        offset (int): Desplazamiento desde el inicio (default: 0)
    
    Returns:
        list: Lista de IDs de emails, o lista vacía si no hay emails
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM creator_email ORDER BY created_at ASC LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        conn.close()
        
        ids = [row[0] for row in rows]
        print(f"📧 Obtenidos {len(ids)} emails con offset {offset}")
        return ids
        
    except Exception as e:
        print(f"❌ Error al obtener emails con offset: {e}")
        return []


def get_next_creator_emails(limit):
    """
    Obtiene los siguientes N emails del creator basándose en el progreso actual
    
    Args:
        limit (int): Cantidad de emails a obtener
    
    Returns:
        list: Lista de IDs de emails, o lista vacía si no hay emails
    """
    try:
        # Obtener progreso actual
        progress = get_creator_email_progress()
        if not progress:
            # Si no hay progreso, empezar desde el principio
            offset = 0
        else:
            # Usar el último email usado como offset
            offset = progress['last_used_email_id']
            
            # Verificar si los emails han cambiado (recargados)
            if detect_emails_changed():
                print("🔄 Emails recargados detectados - reiniciando progreso")
                reset_creator_email_progress()
                offset = 0
        
        # Obtener emails con offset
        email_ids = get_creator_emails_with_offset(limit, offset)
        
        # NO reiniciar automáticamente - si no hay más emails, retornar lista vacía
        if not email_ids:
            print("📧 No hay más emails disponibles para procesar")
        
        return email_ids
        
    except Exception as e:
        print(f"❌ Error al obtener siguientes emails: {e}")
        return []


def get_all_available_creator_emails():
    """
    Obtiene todos los emails disponibles del creator basándose en el progreso actual
    
    Returns:
        list: Lista de IDs de emails, o lista vacía si no hay emails
    """
    try:
        # Obtener progreso actual
        progress = get_creator_email_progress()
        if not progress:
            # Si no hay progreso, empezar desde el principio
            offset = 0
        else:
            # Usar el último email usado como offset
            offset = progress['last_used_email_id']
            
            # Verificar si los emails han cambiado (recargados)
            if detect_emails_changed():
                print("🔄 Emails recargados detectados - reiniciando progreso")
                reset_creator_email_progress()
                offset = 0
        
        # Obtener todos los emails restantes con offset
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM creator_email ORDER BY created_at ASC LIMIT -1 OFFSET ?", (offset,))
        rows = cursor.fetchall()
        conn.close()
        
        email_ids = [row[0] for row in rows]
        
        if not email_ids:
            print("📧 No hay más emails disponibles para procesar")
        else:
            print(f"📧 Obtenidos {len(email_ids)} emails disponibles para procesar")
        
        return email_ids
        
    except Exception as e:
        print(f"❌ Error al obtener emails disponibles: {e}")
        return []


def get_all_available_creator_emails_for_objective():
    """
    Obtiene todos los emails disponibles del creator para el proceso de objetivo
    NO reinicia el progreso automáticamente para evitar interrupciones
    
    Returns:
        list: Lista de IDs de emails, o lista vacía si no hay emails
    """
    try:
        # Obtener progreso actual
        progress = get_creator_email_progress()
        if not progress:
            # Si no hay progreso, empezar desde el principio
            offset = 0
        else:
            # Usar el último email usado como offset
            offset = progress['last_used_email_id']
        
        # Obtener todos los emails restantes con offset
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM creator_email ORDER BY created_at ASC LIMIT -1 OFFSET ?", (offset,))
        rows = cursor.fetchall()
        conn.close()
        
        email_ids = [row[0] for row in rows]
        
        if not email_ids:
            print("📧 No hay más emails disponibles para procesar")
        else:
            print(f"📧 Obtenidos {len(email_ids)} emails disponibles para procesar")
        
        return email_ids
        
    except Exception as e:
        print(f"❌ Error al obtener emails disponibles: {e}")
        return []


def detect_emails_changed():
    """
    Detecta si los emails han cambiado comparando el total actual con el último procesado
    
    Returns:
        bool: True si los emails han cambiado, False si no
    """
    try:
        # Obtener progreso actual
        progress = get_creator_email_progress()
        if not progress:
            return False  # No hay progreso previo
        
        # Obtener total actual de emails
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM creator_email")
        total_emails = cursor.fetchone()[0]
        conn.close()
        
        # Si el último ID procesado es mayor o igual al total actual, los emails cambiaron
        return progress['last_used_email_id'] >= total_emails
        
    except Exception as e:
        return False


def reset_creator_email_progress():
    """
    Reinicia el progreso de emails del creator
    
    Returns:
        bool: True si se reinició correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Reiniciar progreso
        cursor.execute('''
            INSERT OR REPLACE INTO creator_email_progress (id, last_used_email_id, total_emails_used, last_updated)
            VALUES (1, 0, 0, CURRENT_TIMESTAMP)
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Progreso de emails reiniciado")
        return True
        
    except Exception as e:
        print(f"❌ Error al reiniciar progreso de emails: {e}")
        return False


def get_user_data():
    """
    Obtiene los datos del usuario desde la base de datos.
    
    Returns:
        dict or None: Datos del usuario (id, name, lastname, access_token) o None si hay error
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, lastname, access_token FROM user LIMIT 1')
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return {
                'id': user_data[0],
                'name': user_data[1],
                'lastname': user_data[2],
                'access_token': user_data[3]
            }
        else:
            print("❌ No se encontraron datos de usuario en la base de datos")
            return None
            
    except Exception as e:
        print(f"❌ Error al obtener datos del usuario: {e}")
        return None


#! FUNCIONES PARA OBTENER EMAILS DEL SERVIDOR
def fetch_emails_from_server(count: int) -> list:
    """
    Obtiene emails del servidor externo
    
    Args:
        count (int): Cantidad de emails a solicitar
    
    Returns:
        list: Lista de emails obtenidos del servidor, o lista vacía si hay error
    """
    from app.utils.http_utils import post
    
    try:
        # Obtener datos del usuario desde la base de datos
        user_data = get_user_data()
        if not user_data:
            print("❌ No se encontraron datos de usuario en la base de datos")
            return []
        
        user_id = user_data['id']
        access_token = user_data['access_token']
        
        # Construir URL con el ID del usuario
        url = f"http://35.209.237.44/api/emails/next/{user_id}"
        headers = {
            "Content-Type": "application/json"
        }
        
        body = {
            "access_token": access_token,
            "count": count
        }
        
        print(f"🌐 Solicitando {count} emails del servidor para usuario ID {user_id}...")
        response = post(url, body=body, headers=headers, timeout=30)
        
        if not response:
            print("❌ No se pudo conectar al servidor")
            _mostrar_error_servidor("Error de conexión", "No se pudo conectar al servidor. Verifica tu conexión a internet.")
            return "SERVER_ERROR"
        
        if response.status_code != 200:
            print(f"❌ Error del servidor: {response.status_code}")
            try:
                error_data = response.json()
                error_message = error_data.get('message', f'Error del servidor: {response.status_code}')
            except:
                error_message = f'Error del servidor: {response.status_code}'
            
            _mostrar_error_servidor(f"Error {response.status_code}", error_message)
            return "SERVER_ERROR"
        
        data = response.json()
        
        if 'emails' not in data:
            print("❌ Respuesta del servidor no contiene emails")
            return []
        
        emails = data['emails']
        
        # Mostrar información adicional de la respuesta
        active_count = data.get('active_count', 0)
        completed_count = data.get('completed_count', 0)
        requested_count = data.get('requested_count', 0)
        message = data.get('message', 'Sin mensaje')
        
        print(f"📊 Información del servidor:")
        print(f"   - Emails activos: {active_count}")
        print(f"   - Emails completados: {completed_count}")
        print(f"   - Emails solicitados: {requested_count}")
        print(f"   - Emails obtenidos: {len(emails)}")
        print(f"   - Mensaje: {message}")
        
        # Verificar si no hay emails disponibles
        if len(emails) == 0:
            print("📭 No hay más emails disponibles en el servidor")
            return "NO_EMAILS_AVAILABLE"  # Retornar señal especial
        
        print(f"✅ Obtenidos {len(emails)} emails del servidor")
        
        return emails
        
    except Exception as e:
        print(f"❌ Error al obtener emails del servidor: {e}")
        _mostrar_error_servidor("Error inesperado", f"Error inesperado al obtener emails: {e}")
        return "SERVER_ERROR"


def _mostrar_error_servidor(titulo, mensaje):
    """
    Muestra un messagebox de error del servidor y detiene la ejecución
    """
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        
        mensaje_completo = f"{mensaje}\n\nEl bot se detendrá.\n\nContacta con el desarrollador si el problema persiste."
        
        messagebox.showerror(titulo, mensaje_completo)
        root.destroy()
        
        # Detener la ejecución
        import sys
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error al mostrar messagebox: {e}")
        print(f"❌ {titulo}: {mensaje}")
        import sys
        sys.exit(1)


def save_emails_from_server(emails_data: list) -> bool:
    """
    Guarda los emails obtenidos del servidor en la base de datos local
    
    Args:
        emails_data (list): Lista de emails del servidor con formato:
            [{"id": 1, "email": "@lawyer313ztle.33mail.com", "created_at": "2025-10-08T18:04:41.187967", 
              "status": "completed", "usage_count": 2, "user_id": 2}, ...]
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Limpiar emails existentes antes de agregar los nuevos
        cursor.execute("DELETE FROM creator_email")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='creator_email'")
        
        # Contar emails por status
        status_counts = {}
        
        # Insertar nuevos emails
        for email_data in emails_data:
            email = email_data['email']
            created_at = email_data['created_at']
            status = email_data.get('status', 'unknown')
            usage_count = email_data.get('usage_count', 0)
            
            # Contar por status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            cursor.execute('''
                INSERT OR IGNORE INTO creator_email (email, created_at)
                VALUES (?, ?)
            ''', (email, created_at))
            
            #print(f"📧 Email: {email} | Status: {status} | Usos: {usage_count}")
        
        conn.commit()
        conn.close()
        
        # Mostrar resumen por status
        print(f"📊 Resumen de emails guardados:")
        for status, count in status_counts.items():
            print(f"   - {status}: {count} emails")
        
        print(f"✅ Guardados {len(emails_data)} emails en la base de datos local")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar emails del servidor: {e}")
        return False


def fetch_and_save_emails_for_cycle(count: int) -> bool:
    """
    Obtiene emails del servidor y los guarda en la base de datos local para el ciclo actual
    
    Args:
        count (int): Cantidad de emails a solicitar
    
    Returns:
        bool: True si se obtuvieron y guardaron correctamente, False en caso contrario
    """
    try:
        # Obtener emails del servidor
        emails_data = fetch_emails_from_server(count)
        
        if emails_data == "NO_EMAILS_AVAILABLE":
            print("📭 No hay más emails disponibles en el servidor")
            return "NO_EMAILS_AVAILABLE"  # Retornar señal especial
        
        if emails_data == "SERVER_ERROR":
            print("❌ Error del servidor - deteniendo ejecución")
            return False
        
        if not emails_data:
            print("❌ No se pudieron obtener emails del servidor")
            return False
        
        # Guardar emails en la base de datos local
        success = save_emails_from_server(emails_data)
        
        if success:
            # Reiniciar el progreso para empezar con los nuevos emails
            reset_creator_email_progress()
            print(f"🔄 Listo para procesar {len(emails_data)} emails en el ciclo actual")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en fetch_and_save_emails_for_cycle: {e}")
        return False


def fetch_and_append_emails_for_cycle(count: int) -> bool:
    """
    Obtiene emails del servidor y los agrega a la base de datos local sin limpiar los existentes
    
    Args:
        count (int): Cantidad de emails a solicitar
    
    Returns:
        bool: True si se obtuvieron y guardaron correctamente, False en caso contrario
    """
    try:
        # Obtener emails del servidor
        emails_data = fetch_emails_from_server(count)
        
        if emails_data == "NO_EMAILS_AVAILABLE":
            print("📭 No hay más emails disponibles en el servidor")
            return "NO_EMAILS_AVAILABLE"  # Retornar señal especial
        
        if emails_data == "SERVER_ERROR":
            print("❌ Error del servidor - deteniendo ejecución")
            return False
        
        if not emails_data:
            print("❌ No se pudieron obtener emails del servidor")
            return False
        
        # Agregar emails a la base de datos local sin limpiar los existentes
        success = append_emails_from_server(emails_data)
        
        if success:
            print(f"🔄 Agregados {len(emails_data)} emails adicionales a la base de datos local")
        
        return success
        
    except Exception as e:
        print(f"❌ Error en fetch_and_append_emails_for_cycle: {e}")
        return False


def append_emails_from_server(emails_data: list) -> bool:
    """
    Agrega los emails obtenidos del servidor a la base de datos local sin limpiar los existentes
    
    Args:
        emails_data (list): Lista de emails del servidor con formato:
            [{"id": 1, "email": "@lawyer313ztle.33mail.com", "created_at": "2025-10-08T18:04:41.187967", 
              "status": "completed", "usage_count": 2, "user_id": 2}, ...]
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar emails por status
        status_counts = {}
        
        # Insertar nuevos emails sin limpiar los existentes
        for email_data in emails_data:
            email = email_data['email']
            created_at = email_data['created_at']
            status = email_data.get('status', 'unknown')
            usage_count = email_data.get('usage_count', 0)
            
            # Contar por status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            cursor.execute('''
                INSERT OR IGNORE INTO creator_email (email, created_at)
                VALUES (?, ?)
            ''', (email, created_at))
            
            #print(f"📧 Email: {email} | Status: {status} | Usos: {usage_count}")
        
        conn.commit()
        conn.close()
        
        # Mostrar resumen por status
        print(f"📊 Resumen de emails agregados:")
        for status, count in status_counts.items():
            print(f"   - {status}: {count} emails")
        
        print(f"✅ Agregados {len(emails_data)} emails a la base de datos local")
        return True
        
    except Exception as e:
        print(f"❌ Error al agregar emails del servidor: {e}")
        return False