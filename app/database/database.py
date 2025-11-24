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
        # Habilitar claves foráneas para esta conexión
        conn.execute("PRAGMA foreign_keys = ON")
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

        # 🔹 Tabla para navegadores
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS browsers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                isActive INTEGER NOT NULL DEFAULT 1
            )
            '''
        )
        
        # 🔹 Tabla para almacenar coordenadas de clicks del creator (ahora asociada a navegadores)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_coordinates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                browser_id INTEGER NOT NULL,
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
                white_captcha_click TEXT NOT NULL,
                close_captcha_error_click TEXT NOT NULL,
                close_proxy_error_click TEXT NOT NULL,
                FOREIGN KEY (browser_id) REFERENCES browsers(id) ON DELETE CASCADE,
                UNIQUE(browser_id)
            )
            '''
        )
        
        # 🔄 MIGRACIÓN: Agregar browser_id a creator_coordinates si no existe
        print("🔄 Verificando migración de creator_coordinates para múltiples navegadores...")
        cursor.execute("PRAGMA table_info(creator_coordinates)")
        creator_columns = [col[1] for col in cursor.fetchall()]
        
        # Si la tabla existe pero no tiene browser_id, necesitamos migrar
        if creator_columns and 'browser_id' not in creator_columns:
            print("🔄 Migrando creator_coordinates para soportar múltiples navegadores...")
            
            # Crear navegador por defecto si no existe
            cursor.execute("SELECT id FROM browsers LIMIT 1")
            default_browser = cursor.fetchone()
            if not default_browser:
                cursor.execute("INSERT INTO browsers (name, isActive) VALUES (?, ?)", ("Navegador Principal", 1))
                cursor.execute("SELECT id FROM browsers WHERE name = ?", ("Navegador Principal",))
                default_browser_id = cursor.fetchone()[0]
            else:
                default_browser_id = default_browser[0]
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute('''
                CREATE TABLE creator_coordinates_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    browser_id INTEGER NOT NULL,
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
                    white_captcha_click TEXT NOT NULL,
                    close_captcha_error_click TEXT NOT NULL,
                    close_proxy_error_click TEXT NOT NULL,
                    FOREIGN KEY (browser_id) REFERENCES browsers(id) ON DELETE CASCADE,
                    UNIQUE(browser_id)
                )
            ''')
            
            # Copiar datos existentes a la nueva tabla
            cursor.execute("SELECT * FROM creator_coordinates")
            old_data = cursor.fetchone()
            if old_data:
                # Mapear columnas antiguas a nuevas
                cursor.execute('''
                    INSERT INTO creator_coordinates_new (
                        browser_id, brave_click, linkedin_fav_click, email_input_click,
                        continue_button_click, name_input_click, continue_button2_click,
                        close_captcha_click, close_number_click, cookie_editor_icon_click,
                        save_cookie_clipboard_click, close_window, continue_button_click_optional,
                        white_captcha_click, close_captcha_error_click, close_proxy_error_click
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    default_browser_id,
                    old_data[1] if len(old_data) > 1 else '',
                    old_data[2] if len(old_data) > 2 else '',
                    old_data[3] if len(old_data) > 3 else '',
                    old_data[4] if len(old_data) > 4 else '',
                    old_data[5] if len(old_data) > 5 else '',
                    old_data[6] if len(old_data) > 6 else '',
                    old_data[7] if len(old_data) > 7 else '',
                    old_data[8] if len(old_data) > 8 else '',
                    old_data[9] if len(old_data) > 9 else '',
                    old_data[10] if len(old_data) > 10 else '',
                    old_data[11] if len(old_data) > 11 else '',
                    old_data[12] if len(old_data) > 12 else '',
                    old_data[13] if len(old_data) > 13 else '',
                    old_data[14] if len(old_data) > 14 else '',
                    old_data[15] if len(old_data) > 15 else ''
                ))
            
            # Eliminar tabla antigua y renombrar la nueva
            cursor.execute("DROP TABLE creator_coordinates")
            cursor.execute("ALTER TABLE creator_coordinates_new RENAME TO creator_coordinates")
            print("✅ Migración de creator_coordinates completada")
        
        # Verificar columnas faltantes en creator_coordinates
        cursor.execute("PRAGMA table_info(creator_coordinates)")
        creator_columns = [col[1] for col in cursor.fetchall()]
        
        expected_creator_columns = [
            'id', 'browser_id', 'brave_click', 'linkedin_fav_click', 'email_input_click',
            'continue_button_click', 'name_input_click', 'continue_button2_click',
            'close_captcha_click', 'close_number_click', 'cookie_editor_icon_click',
            'save_cookie_clipboard_click', 'close_window', 'continue_button_click_optional',
            'white_captcha_click', 'close_captcha_error_click', 'close_proxy_error_click'
        ]
        
        # Agregar columnas faltantes
        missing_columns = set(expected_creator_columns) - set(creator_columns)
        if missing_columns:
            print(f"🔄 Agregando columnas faltantes a creator_coordinates: {missing_columns}")
            for col in missing_columns:
                if col != 'browser_id':  # browser_id ya se maneja en la migración
                    try:
                        if col in ['close_window', 'white_captcha_click', 'close_captcha_error_click', 'close_proxy_error_click']:
                            cursor.execute(f"ALTER TABLE creator_coordinates ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")
                        elif col == 'continue_button_click_optional':
                            cursor.execute(f"ALTER TABLE creator_coordinates ADD COLUMN {col} TEXT")
                        print(f"✅ Columna {col} agregada a creator_coordinates")
                    except sqlite3.OperationalError:
                        pass  # La columna ya existe
        
        print("✅ Verificación de creator_coordinates completada")

        # 🔹 Tabla para configuración del creator (ahora asociada a navegadores)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_setting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                browser_id INTEGER NOT NULL,
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
                accounts_per_cycle INTEGER DEFAULT 1,
                isInVps INTEGER DEFAULT 0,
                is33mail INTEGER DEFAULT 1,
                domain TEXT,
                FOREIGN KEY (browser_id) REFERENCES browsers(id) ON DELETE CASCADE,
                UNIQUE(browser_id)
            )
            '''
        )
        
        # 🔹 Tabla para imágenes de navegadores
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS browser_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                browser_id INTEGER NOT NULL,
                image_name TEXT NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY (browser_id) REFERENCES browsers(id) ON DELETE CASCADE,
                UNIQUE(browser_id, image_name)
            )
            '''
        )
        
        # 🔄 MIGRACIÓN: Agregar browser_id a creator_setting si no existe
        print("🔄 Verificando migración de creator_setting para múltiples navegadores...")
        cursor.execute("PRAGMA table_info(creator_setting)")
        setting_columns = [col[1] for col in cursor.fetchall()]
        
        # Si la tabla existe pero no tiene browser_id, necesitamos migrar
        if setting_columns and 'browser_id' not in setting_columns:
            print("🔄 Migrando creator_setting para soportar múltiples navegadores...")
            
            # Obtener navegador por defecto
            cursor.execute("SELECT id FROM browsers LIMIT 1")
            default_browser = cursor.fetchone()
            if not default_browser:
                cursor.execute("INSERT INTO browsers (name, isActive) VALUES (?, ?)", ("Navegador Principal", 1))
                cursor.execute("SELECT id FROM browsers WHERE name = ?", ("Navegador Principal",))
                default_browser_id = cursor.fetchone()[0]
            else:
                default_browser_id = default_browser[0]
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute('''
                CREATE TABLE creator_setting_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    browser_id INTEGER NOT NULL,
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
                    accounts_per_cycle INTEGER DEFAULT 1,
                    isInVps INTEGER DEFAULT 0,
                    is33mail INTEGER DEFAULT 1,
                    domain TEXT,
                    FOREIGN KEY (browser_id) REFERENCES browsers(id) ON DELETE CASCADE,
                    UNIQUE(browser_id)
                )
            ''')
            
            # Copiar datos existentes a la nueva tabla
            cursor.execute("SELECT * FROM creator_setting")
            old_data = cursor.fetchone()
            if old_data:
                cursor.execute('''
                    INSERT INTO creator_setting_new (
                        browser_id, user_agent, accounts_to_create, scheduled_time, timezone,
                        notification_email, google_sheets_enabled, google_sheets_name,
                        google_credentials_file, cycle_time_minutes, time_config_type,
                        accounts_per_cycle, isInVps, is33mail, domain
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    default_browser_id,
                    old_data[1] if len(old_data) > 1 else '',
                    old_data[2] if len(old_data) > 2 else 1,
                    old_data[3] if len(old_data) > 3 else None,
                    old_data[4] if len(old_data) > 4 else None,
                    old_data[5] if len(old_data) > 5 else None,
                    old_data[6] if len(old_data) > 6 else 0,
                    old_data[7] if len(old_data) > 7 else None,
                    old_data[8] if len(old_data) > 8 else None,
                    old_data[9] if len(old_data) > 9 else 60,
                    old_data[10] if len(old_data) > 10 else 'scheduled',
                    old_data[11] if len(old_data) > 11 else 1,
                    old_data[12] if len(old_data) > 12 else 0,
                    old_data[13] if len(old_data) > 13 else 1,
                    old_data[14] if len(old_data) > 14 else None
                ))
            
            # Eliminar tabla antigua y renombrar la nueva
            cursor.execute("DROP TABLE creator_setting")
            cursor.execute("ALTER TABLE creator_setting_new RENAME TO creator_setting")
            print("✅ Migración de creator_setting completada")
        
        # Agregar columnas faltantes si no existen
        expected_setting_columns = [
            'id', 'browser_id', 'user_agent', 'accounts_to_create', 'scheduled_time',
            'timezone', 'notification_email', 'google_sheets_enabled', 'google_sheets_name',
            'google_credentials_file', 'cycle_time_minutes', 'time_config_type',
            'accounts_per_cycle', 'isInVps', 'is33mail', 'domain'
        ]
        
        missing_setting_columns = set(expected_setting_columns) - set(setting_columns)
        if missing_setting_columns:
            print(f"🔄 Agregando columnas faltantes a creator_setting: {missing_setting_columns}")
            for col in missing_setting_columns:
                if col != 'browser_id':  # browser_id ya se maneja en la migración
                    try:
                        if col in ['scheduled_time', 'timezone', 'notification_email', 'google_sheets_name', 'google_credentials_file', 'domain']:
                            cursor.execute(f"ALTER TABLE creator_setting ADD COLUMN {col} TEXT")
                        elif col in ['google_sheets_enabled', 'cycle_time_minutes', 'accounts_per_cycle', 'isInVps', 'is33mail']:
                            default_val = 0 if col in ['google_sheets_enabled', 'isInVps'] else (1 if col == 'is33mail' else (60 if col == 'cycle_time_minutes' else 1))
                            cursor.execute(f"ALTER TABLE creator_setting ADD COLUMN {col} INTEGER DEFAULT {default_val}")
                        elif col == 'time_config_type':
                            cursor.execute(f"ALTER TABLE creator_setting ADD COLUMN {col} TEXT DEFAULT 'scheduled'")
                        print(f"✅ Columna {col} agregada a creator_setting")
                    except sqlite3.OperationalError:
                        pass  # La columna ya existe
        
        print("✅ Verificación de creator_setting completada")

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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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


# =================================
#         BROWSERS
# =================================

def create_browser(name, isActive=True):
    """
    Crea un nuevo navegador
    
    Args:
        name (str): Nombre del navegador
        isActive (bool): Si el navegador está activo (default: True)
    
    Returns:
        int: ID del navegador creado, o None si hay error
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO browsers (name, isActive) VALUES (?, ?)",
            (name.strip(), 1 if isActive else 0)
        )
        
        browser_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Navegador '{name}' creado con ID {browser_id}")
        return browser_id
        
    except sqlite3.IntegrityError:
        print(f"⚠️ El navegador '{name}' ya existe")
        return None
    except Exception as e:
        print(f"❌ Error al crear navegador: {e}")
        return None


def get_all_browsers():
    """
    Obtiene todos los navegadores
    
    Returns:
        list: Lista de diccionarios con id, name, isActive
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, isActive FROM browsers ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'isActive': bool(row[2])
            }
            for row in rows
        ]
    except Exception as e:
        print(f"❌ Error al obtener navegadores: {e}")
        return []


def get_browser_by_id(browser_id):
    """
    Obtiene un navegador por su ID
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        dict: Diccionario con id, name, isActive, o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, isActive FROM browsers WHERE id = ?", (browser_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'isActive': bool(row[2])
            }
        return None
    except Exception as e:
        print(f"❌ Error al obtener navegador: {e}")
        return None


def update_browser(browser_id, name=None, isActive=None):
    """
    Actualiza un navegador
    
    Args:
        browser_id (int): ID del navegador
        name (str): Nuevo nombre (opcional)
        isActive (bool): Nuevo estado activo (opcional)
    
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if name is not None:
            updates.append("name = ?")
            values.append(name.strip())
        
        if isActive is not None:
            updates.append("isActive = ?")
            values.append(1 if isActive else 0)
        
        if not updates:
            conn.close()
            return False
        
        values.append(browser_id)
        cursor.execute(
            f"UPDATE browsers SET {', '.join(updates)} WHERE id = ?",
            values
        )
        
        conn.commit()
        conn.close()
        
        print(f"✅ Navegador {browser_id} actualizado")
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar navegador: {e}")
        return False


def delete_browser(browser_id):
    """
    Elimina un navegador y todas sus configuraciones asociadas
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT name FROM browsers WHERE id = ?", (browser_id,))
        browser = cursor.fetchone()
        if not browser:
            conn.close()
            print(f"⚠️ Navegador {browser_id} no existe")
            return False
        
        # Eliminar (CASCADE eliminará automáticamente coordenadas, configuraciones e imágenes)
        cursor.execute("DELETE FROM browsers WHERE id = ?", (browser_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Navegador '{browser[0]}' eliminado")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar navegador: {e}")
        return False


def get_active_browsers():
    """
    Obtiene todos los navegadores activos
    
    Returns:
        list: Lista de diccionarios con id, name, isActive
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, isActive FROM browsers WHERE isActive = 1 ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'isActive': True
            }
            for row in rows
        ]
    except Exception as e:
        print(f"❌ Error al obtener navegadores activos: {e}")
        return []


def get_default_browser():
    """
    Obtiene el primer navegador activo, o el primero disponible si no hay activos
    
    Returns:
        dict: Diccionario con id, name, isActive, o None si no hay navegadores
    """
    try:
        # Intentar obtener un navegador activo
        active_browsers = get_active_browsers()
        if active_browsers:
            return active_browsers[0]
        
        # Si no hay activos, obtener el primero disponible
        all_browsers = get_all_browsers()
        if all_browsers:
            return all_browsers[0]
        
        return None
    except Exception as e:
        print(f"❌ Error al obtener navegador por defecto: {e}")
        return None


def save_creator_coordinates(browser_id, coordinates_dict=None, **kwargs):
    """
    Guarda las coordenadas del creator para un navegador específico
    
    Args:
        browser_id (int): ID del navegador
        coordinates_dict (dict): Diccionario con las coordenadas
        **kwargs: Coordenadas individuales como argumentos
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Obtener coordenadas existentes para este navegador
        cursor.execute("SELECT * FROM creator_coordinates WHERE browser_id = ?", (browser_id,))
        existing_row = cursor.fetchone()
        
        # Preparar valores con los existentes como base o valores por defecto
        if existing_row:
            # Excluir id y browser_id (índices 0 y 1)
            values = list(existing_row[2:])  # Desde índice 2 en adelante
            # Asegurar que tenemos exactamente 15 valores
            while len(values) < 15:
                values.append('')
            values = values[:15]
        else:
            values = [''] * 15  # 15 campos de coordenadas

        # Mapeo de nombres de campos a índices (0-14 para 15 campos)
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
            'white_captcha_click': 12,
            'close_captcha_error_click': 13,
            'close_proxy_error_click': 14
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

        # Insertar o actualizar (UPSERT usando REPLACE)
        cursor.execute(
            """
            INSERT OR REPLACE INTO creator_coordinates (
                browser_id, brave_click, linkedin_fav_click, email_input_click,
                continue_button_click, name_input_click, continue_button2_click,
                close_captcha_click, close_number_click, cookie_editor_icon_click,
                save_cookie_clipboard_click, close_window, continue_button_click_optional,
                white_captcha_click, close_captcha_error_click, close_proxy_error_click
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (browser_id,) + tuple(values)
        )

        conn.commit()
        conn.close()
        print(f"✅ Coordenadas del creator guardadas para navegador {browser_id}")
        return True

    except Exception as e:
        print(f"❌ Error al guardar coordenadas del creator: {e}")
        return False


def get_creator_coordinates(browser_id, *field_names):
    """
    Obtiene las coordenadas del creator para un navegador específico
    
    Args:
        browser_id (int): ID del navegador
        *field_names: Campos específicos a obtener (opcional)
    
    Returns:
        dict: Diccionario con las coordenadas, o None si no existen
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM creator_coordinates WHERE browser_id = ?", (browser_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Mapeo de nombres de campos a índices (ahora browser_id es índice 1)
        field_mapping = {
            'brave_click': 2,
            'linkedin_fav_click': 3,
            'email_input_click': 4,
            'continue_button_click': 5,
            'name_input_click': 6,
            'continue_button2_click': 7,
            'close_captcha_click': 8,
            'close_number_click': 9,
            'cookie_editor_icon_click': 10,
            'save_cookie_clipboard_click': 11,
            'close_window': 12,
            'continue_button_click_optional': 13,
            'white_captcha_click': 14,
            'close_captcha_error_click': 15,
            'close_proxy_error_click': 16
        }

        # Si no se especifican campos, devolver todos
        if not field_names:
            return {
                'brave_click': row[2] if len(row) > 2 else '',
                'linkedin_fav_click': row[3] if len(row) > 3 else '',
                'email_input_click': row[4] if len(row) > 4 else '',
                'continue_button_click': row[5] if len(row) > 5 else '',
                'name_input_click': row[6] if len(row) > 6 else '',
                'continue_button2_click': row[7] if len(row) > 7 else '',
                'close_captcha_click': row[8] if len(row) > 8 else '',
                'close_number_click': row[9] if len(row) > 9 else '',
                'cookie_editor_icon_click': row[10] if len(row) > 10 else '',
                'save_cookie_clipboard_click': row[11] if len(row) > 11 else '',
                'close_window': row[12] if len(row) > 12 else '',
                'continue_button_click_optional': row[13] if len(row) > 13 else '',
                'white_captcha_click': row[14] if len(row) > 14 else '',
                'close_captcha_error_click': row[15] if len(row) > 15 else '',
                'close_proxy_error_click': row[16] if len(row) > 16 else ''
            }

        # Devolver solo los campos solicitados
        result = {}
        for field_name in field_names:
            if field_name in field_mapping:
                idx = field_mapping[field_name]
                result[field_name] = row[idx] if len(row) > idx else ''

        return result if result else None

    except Exception as e:
        print(f"❌ Error al obtener coordenadas del creator: {e}")
        return None


#! FUNCIONES DE CREATOR_SETTING
def save_creator_setting(browser_id, user_agent, accounts_to_create=1, scheduled_time=None, timezone=None, notification_email=None, cycle_time_minutes=None, time_config_type='manual', accounts_per_cycle=None, isInVps=None, is33mail=None, domain=None):
    """
    Guarda o actualiza la configuración del creator para un navegador específico
    
    Args:
        browser_id (int): ID del navegador
        user_agent (str): User agent a utilizar
        accounts_to_create (int): Cantidad de cuentas a crear (default: 1)
        scheduled_time (str): Hora programada en formato HH:MM (opcional)
        timezone (str): Zona horaria (opcional)
        notification_email (str): Email para recibir notificaciones (opcional)
        cycle_time_minutes (int): Tiempo en minutos para el ciclo (default: 60)
        time_config_type (str): Tipo de configuración ('scheduled' o 'cycle')
        accounts_per_cycle (int): Cantidad de cuentas a crear por ciclo (default: 1)
        isInVps (bool): Si está ejecutándose en VPS (True) o máquina física (False) (opcional)
        is33mail (bool): Si se usa 33mail (True) o no (False) (opcional)
        domain (str): Dominio a utilizar (opcional)
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Convertir boolean a integer para SQLite (True = 1, False = 0)
        isInVps_int = 1 if isInVps is True else (0 if isInVps is False else None)
        is33mail_int = 1 if is33mail is True else (0 if is33mail is False else None)
        
        # Insertar o actualizar (UPSERT usando REPLACE)
        cursor.execute('''
            INSERT OR REPLACE INTO creator_setting (browser_id, user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps, is33mail, domain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (browser_id, user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps_int, is33mail_int, domain))
        
        conn.commit()
        conn.close()
        print(f"✅ Configuración del creator guardada para navegador {browser_id}: UA={user_agent}, Cuentas={accounts_to_create}, Hora={scheduled_time}, Zona={timezone}, Notificación={notification_email}, Ciclo={cycle_time_minutes}min, Tipo={time_config_type}, CuentasPorCiclo={accounts_per_cycle}, isInVps={isInVps}, is33mail={is33mail}, domain={domain}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar configuración del creator: {e}")
        return False


def get_creator_setting(browser_id):
    """
    Obtiene la configuración del creator para un navegador específico
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        dict: Diccionario con user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps, is33mail y domain, o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT user_agent, accounts_to_create, scheduled_time, timezone, notification_email, cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps, is33mail, domain FROM creator_setting WHERE browser_id = ?", (browser_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Convertir integer a boolean para isInVps (None si no está configurado)
            isInVps_bool = None
            if row[8] is not None:
                isInVps_bool = bool(row[8])
            
            # Convertir integer a boolean para is33mail (None si no está configurado)
            is33mail_bool = None
            if row[9] is not None:
                is33mail_bool = bool(row[9])
            
            return {
                'user_agent': row[0],
                'accounts_to_create': row[1],
                'scheduled_time': row[2],
                'timezone': row[3],
                'notification_email': row[4],
                'cycle_time_minutes': row[5],  # Mantener el valor real, incluso si es None
                'time_config_type': row[6] if row[6] is not None else 'manual',  # Cambiar default a 'manual'
                'accounts_per_cycle': row[7],  # Mantener el valor real, incluso si es None
                'isInVps': isInVps_bool,  # Boolean o None
                'is33mail': is33mail_bool,  # Boolean o None
                'domain': row[10]  # String o None
            }
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener configuración del creator: {e}")
        return None


def clear_scheduled_time(browser_id):
    """
    Elimina la hora programada de la configuración del creator para un navegador específico
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Actualizar solo los campos de hora programada
        cursor.execute('''
            UPDATE creator_setting 
            SET scheduled_time = NULL, timezone = NULL 
            WHERE browser_id = ?
        ''', (browser_id,))
        
        conn.commit()
        conn.close()
        print(f"✅ Hora programada eliminada para navegador {browser_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar hora programada: {e}")
        return False


# =================================
#         BROWSER IMAGES
# =================================

def save_browser_image(browser_id, image_name, image_path):
    """
    Guarda o actualiza una imagen asociada a un navegador
    
    Args:
        browser_id (int): ID del navegador
        image_name (str): Nombre de la imagen
        image_path (str): Ruta de la imagen
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO browser_images (browser_id, image_name, image_path)
            VALUES (?, ?, ?)
        ''', (browser_id, image_name, image_path))
        
        conn.commit()
        conn.close()
        print(f"✅ Imagen '{image_name}' guardada para navegador {browser_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar imagen del navegador: {e}")
        return False


def get_browser_image(browser_id, image_name):
    """
    Obtiene la ruta de una imagen específica de un navegador
    
    Args:
        browser_id (int): ID del navegador
        image_name (str): Nombre de la imagen
    
    Returns:
        str: Ruta de la imagen, o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM browser_images WHERE browser_id = ? AND image_name = ?", (browser_id, image_name))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener imagen del navegador: {e}")
        return None


def get_all_browser_images(browser_id):
    """
    Obtiene todas las imágenes asociadas a un navegador
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        dict: Diccionario con image_name como clave y image_path como valor
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT image_name, image_path FROM browser_images WHERE browser_id = ?", (browser_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in rows}
        
    except Exception as e:
        print(f"❌ Error al obtener imágenes del navegador: {e}")
        return {}


def delete_browser_image(browser_id, image_name):
    """
    Elimina una imagen asociada a un navegador
    
    Args:
        browser_id (int): ID del navegador
        image_name (str): Nombre de la imagen
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM browser_images WHERE browser_id = ? AND image_name = ?", (browser_id, image_name))
        
        conn.commit()
        conn.close()
        print(f"✅ Imagen '{image_name}' eliminada para navegador {browser_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar imagen del navegador: {e}")
        return False


def delete_all_browser_images(browser_id):
    """
    Elimina todas las imágenes asociadas a un navegador
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        bool: True si se eliminaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM browser_images WHERE browser_id = ?", (browser_id,))
        
        conn.commit()
        conn.close()
        print(f"✅ Todas las imágenes eliminadas para navegador {browser_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar imágenes del navegador: {e}")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        
        # Verificar si los emails han cambiado (recargados)
        if progress and detect_emails_changed():
            print("🔄 Emails recargados detectados - reiniciando progreso")
            reset_creator_email_progress()
            progress = None
        
        # Obtener emails restantes
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if not progress or progress['last_used_email_id'] == 0:
            # Si no hay progreso o el último usado es 0, obtener los primeros emails
            cursor.execute("SELECT id FROM creator_email ORDER BY id ASC LIMIT ?", (limit,))
        else:
            # Obtener emails con ID mayor al último usado
            cursor.execute("SELECT id FROM creator_email WHERE id > ? ORDER BY id ASC LIMIT ?", (progress['last_used_email_id'], limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        email_ids = [row[0] for row in rows]
        
        # NO reiniciar automáticamente - si no hay más emails, retornar lista vacía
        if not email_ids:
            print("📧 No hay más emails disponibles para procesar")
        else:
            print(f"📧 Obtenidos {len(email_ids)} emails disponibles para procesar")
        
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
        
        # Verificar si los emails han cambiado (recargados)
        if progress and detect_emails_changed():
            print("🔄 Emails recargados detectados - reiniciando progreso")
            reset_creator_email_progress()
            progress = None
        
        # Obtener todos los emails restantes
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if not progress or progress['last_used_email_id'] == 0:
            # Si no hay progreso o el último usado es 0, obtener todos los emails
            cursor.execute("SELECT id FROM creator_email ORDER BY id ASC")
        else:
            # Obtener emails con ID mayor al último usado
            cursor.execute("SELECT id FROM creator_email WHERE id > ? ORDER BY id ASC", (progress['last_used_email_id'],))
        
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
        
        # Obtener todos los emails restantes
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if not progress or progress['last_used_email_id'] == 0:
            # Si no hay progreso o el último usado es 0, obtener todos los emails
            cursor.execute("SELECT id FROM creator_email ORDER BY id ASC")
        else:
            # Obtener emails con ID mayor al último usado
            cursor.execute("SELECT id FROM creator_email WHERE id > ? ORDER BY id ASC", (progress['last_used_email_id'],))
        
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
        url = f"http://34.29.59.97/api/emails/next/{user_id}"
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
    Guarda los emails obtenidos del servidor en la base de datos local.
    Limpia todos los emails existentes y guarda los nuevos del servidor.
    
    Args:
        emails_data (list): Lista de emails del servidor con formato:
            [{"id": 1, "email": "@lawyer313ztle.33mail.com", "created_at": "2025-10-08T18:04:41.187967", 
              "status": "completed", "usage_count": 2, "user_id": 2}, ...]
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
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
                INSERT INTO creator_email (email, created_at)
                VALUES (?, ?)
            ''', (email, created_at))
            
            print(f"📧 Email guardado: {email} | Status: {status} | Usos: {usage_count}")
        
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


def check_email_exists(email: str) -> bool:
    """
    Verifica si un email ya existe en la base de datos
    
    Args:
        email (str): Email a verificar
    
    Returns:
        bool: True si existe, False si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM creator_email WHERE email = ?", (email,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"❌ Error al verificar email: {e}")
        return False


def append_emails_from_server(emails_data: list) -> bool:
    """
    Agrega los emails obtenidos del servidor a la base de datos local.
    Si un email ya existe, lo elimina y lo reemplaza con la versión del servidor
    (ya que si el servidor lo envía, significa que aún tiene usos disponibles)
    
    Args:
        emails_data (list): Lista de emails del servidor con formato:
            [{"id": 1, "email": "@lawyer313ztle.33mail.com", "created_at": "2025-10-08T18:04:41.187967", 
              "status": "completed", "usage_count": 2, "user_id": 2}, ...]
    
    Returns:
        bool: True si se guardaron correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Contar emails por status
        status_counts = {}
        emails_nuevos = 0
        emails_actualizados = 0
        
        # Procesar cada email del servidor
        for email_data in emails_data:
            email = email_data['email']
            created_at = email_data['created_at']
            status = email_data.get('status', 'unknown')
            usage_count = email_data.get('usage_count', 0)
            
            # Contar por status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Verificar si el email ya existe
            if check_email_exists(email):
                # Eliminar el email existente y agregar el del servidor
                cursor.execute("DELETE FROM creator_email WHERE email = ?", (email,))
                emails_actualizados += 1
                print(f"🔄 Email actualizado: {email} | Status: {status} | Usos: {usage_count}")
            else:
                emails_nuevos += 1
                print(f"📧 Email nuevo: {email} | Status: {status} | Usos: {usage_count}")
            
            # Insertar el email del servidor
            cursor.execute('''
                INSERT INTO creator_email (email, created_at)
                VALUES (?, ?)
            ''', (email, created_at))
        
        conn.commit()
        conn.close()
        
        # Si se actualizaron emails, reiniciar el progreso para que estén disponibles
        if emails_actualizados > 0:
            print("🔄 Emails actualizados detectados - reiniciando progreso para disponibilidad")
            reset_creator_email_progress()
        
        # Mostrar resumen por status
        print(f"📊 Resumen de emails procesados:")
        for status, count in status_counts.items():
            print(f"   - {status}: {count} emails")
        
        print(f"📧 Emails nuevos agregados: {emails_nuevos}")
        print(f"🔄 Emails actualizados: {emails_actualizados}")
        print(f"✅ Procesados {len(emails_data)} emails del servidor")
        return True
        
    except Exception as e:
        print(f"❌ Error al agregar emails del servidor: {e}")
        return False