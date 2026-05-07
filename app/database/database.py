import os
import sys
import json
import sqlite3
from app.utils.server_config import build_api_url



if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(
        __file__), "..", ".."))

DB_DIR = os.path.join(BASE_DIR, "app", "database")
DB_PATH = os.path.join(DB_DIR, "cookies.db")


def _creator_coordinates_column_names(cursor):
    """Orden real de columnas en SQLite (evita mezclar activate/disable si ALTER las añadió en otro orden)."""
    cursor.execute("PRAGMA table_info(creator_coordinates)")
    return [row[1] for row in cursor.fetchall()]


def _sync_random_tlds_global_column(conn=None):
    """
    Copia las filas de random_tld_entries a global_time_config.random_domain_tlds (CSV).
    Si conn se pasa (p. ej. create_database), no hace commit.
    """
    close_after = conn is None
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT tld FROM random_tld_entries ORDER BY sort_order ASC, id ASC")
        rows = cursor.fetchall()
        joined = ",".join(r[0] for r in rows) if rows else None
        cursor.execute("UPDATE global_time_config SET random_domain_tlds = ? WHERE id = 1", (joined,))
        if close_after:
            conn.commit()
    finally:
        if close_after:
            conn.close()


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
        
        # Migración 5: Agregar bot_name y bot_type si no existen
        if 'bot_name' not in existing_columns:
            print("🔄 Aplicando migración: agregando columna bot_name...")
            try:
                cursor.execute("ALTER TABLE bot_settings ADD COLUMN bot_name TEXT")
                print("✅ Migración bot_name aplicada exitosamente")
            except Exception as e:
                print(f"⚠️ Error en migración bot_name: {e}")
        
        if 'bot_type' not in existing_columns:
            print("🔄 Aplicando migración: agregando columna bot_type...")
            try:
                cursor.execute("ALTER TABLE bot_settings ADD COLUMN bot_type TEXT DEFAULT 'creador'")
                print("✅ Migración bot_type aplicada exitosamente")
            except Exception as e:
                print(f"⚠️ Error en migración bot_type: {e}")
        
        # Migración 6/7: modo de proxy (coordenadas vs Windows)
        cursor.execute("PRAGMA table_info(bot_settings)")
        _bs_cols = [column[1] for column in cursor.fetchall()]
        if "proxy_via_coordinates" not in _bs_cols or "proxy_via_windows" not in _bs_cols:
            print("🔄 Aplicando migración: proxy_via_coordinates / proxy_via_windows...")
            try:
                if "proxy_via_coordinates" not in _bs_cols:
                    cursor.execute(
                        "ALTER TABLE bot_settings ADD COLUMN proxy_via_coordinates INTEGER NOT NULL DEFAULT 0"
                    )
                if "proxy_via_windows" not in _bs_cols:
                    cursor.execute(
                        "ALTER TABLE bot_settings ADD COLUMN proxy_via_windows INTEGER NOT NULL DEFAULT 0"
                    )
                cursor.execute(
                    """
                    UPDATE bot_settings SET proxy_via_windows = 1
                    WHERE COALESCE(enable_proxy, 0) = 1
                    """
                )
                print("✅ Migración modo proxy aplicada")
            except Exception as e:
                print(f"⚠️ Error en migración modo proxy: {e}")
        
        cursor.execute("PRAGMA table_info(bot_settings)")
        _bs_cols2 = [column[1] for column in cursor.fetchall()]
        if "enable_creator_user_agent_actions" not in _bs_cols2:
            print("🔄 Aplicando migración: enable_creator_user_agent_actions...")
            try:
                cursor.execute(
                    "ALTER TABLE bot_settings ADD COLUMN enable_creator_user_agent_actions INTEGER NOT NULL DEFAULT 0"
                )
                print("✅ Migración enable_creator_user_agent_actions aplicada")
            except Exception as e:
                print(f"⚠️ Error en migración enable_creator_user_agent_actions: {e}")
        
        conn.commit()
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
                proxy_extension_click TEXT NOT NULL,
                activate_proxy_click TEXT NOT NULL,
                disable_proxy_click TEXT NOT NULL,
                user_agent_extension_click TEXT NOT NULL,
                user_agent_extract_click TEXT NOT NULL,
                user_agent_apply_click TEXT NOT NULL,
                user_agent_outside_click TEXT NOT NULL,
                search_bar_click TEXT NOT NULL,
                user_options_click TEXT NOT NULL,
                logout_click TEXT NOT NULL,
                jobs_click TEXT NOT NULL,
                login_with_email_click TEXT NOT NULL,
                clic_email_click TEXT NOT NULL,
                linkedin_logo_click TEXT NOT NULL,
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
                    proxy_extension_click TEXT NOT NULL,
                    activate_proxy_click TEXT NOT NULL,
                    disable_proxy_click TEXT NOT NULL,
                    user_agent_extension_click TEXT NOT NULL,
                    user_agent_extract_click TEXT NOT NULL,
                    user_agent_apply_click TEXT NOT NULL,
                    user_agent_outside_click TEXT NOT NULL,
                    search_bar_click TEXT NOT NULL,
                    user_options_click TEXT NOT NULL,
                    logout_click TEXT NOT NULL,
                    jobs_click TEXT NOT NULL,
                    login_with_email_click TEXT NOT NULL,
                    clic_email_click TEXT NOT NULL,
                    linkedin_logo_click TEXT NOT NULL,
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
                        white_captcha_click, close_captcha_error_click, close_proxy_error_click,
                        proxy_extension_click, activate_proxy_click, disable_proxy_click,
                        user_agent_extension_click, user_agent_extract_click,
                        user_agent_apply_click, user_agent_outside_click,
                        search_bar_click, user_options_click, logout_click,
                        jobs_click, login_with_email_click, clic_email_click, linkedin_logo_click
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    old_data[15] if len(old_data) > 15 else '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
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
            'white_captcha_click', 'close_captcha_error_click', 'close_proxy_error_click',
            'proxy_extension_click', 'activate_proxy_click', 'disable_proxy_click',
            'user_agent_extension_click', 'user_agent_extract_click', 'user_agent_apply_click', 'user_agent_outside_click',
            'search_bar_click', 'user_options_click', 'logout_click', 'jobs_click',
            'login_with_email_click', 'clic_email_click', 'linkedin_logo_click',
            'proxy_rotation_browser_click', 'proxy_rotation_search_bar_click', 'proxy_rotation_close_browser_click',
        ]
        
        # Agregar columnas faltantes
        missing_columns = set(expected_creator_columns) - set(creator_columns)
        if missing_columns:
            print(f"🔄 Agregando columnas faltantes a creator_coordinates: {missing_columns}")
            for col in missing_columns:
                if col != 'browser_id':  # browser_id ya se maneja en la migración
                    try:
                        if col in ['close_window', 'white_captcha_click', 'close_captcha_error_click', 'close_proxy_error_click', 'proxy_extension_click', 'activate_proxy_click', 'disable_proxy_click', 'user_agent_extension_click', 'user_agent_extract_click', 'user_agent_apply_click', 'user_agent_outside_click', 'search_bar_click', 'user_options_click', 'logout_click', 'jobs_click', 'login_with_email_click', 'clic_email_click', 'linkedin_logo_click', 'proxy_rotation_browser_click', 'proxy_rotation_search_bar_click', 'proxy_rotation_close_browser_click']:
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
        
        # 🔹 Tabla para configuración global de tiempo (hora programada y ciclo) y dominio
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS global_time_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_time TEXT,
                timezone TEXT,
                cycle_time_minutes INTEGER DEFAULT 60,
                time_config_type TEXT DEFAULT 'manual',
                accounts_per_cycle INTEGER DEFAULT 1,
                is33mail INTEGER DEFAULT 1,
                domain TEXT,
                fill_domain INTEGER DEFAULT 0
            )
            '''
        )
        
        # Inicializar con un registro por defecto si no existe
        cursor.execute("SELECT COUNT(*) FROM global_time_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO global_time_config (scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail, domain, fill_domain)
                VALUES (NULL, NULL, 60, 'manual', 1, 1, NULL, 0)
            ''')
        
        # 🔄 MIGRACIÓN: Agregar campos is33mail, domain y fill_domain si no existen
        cursor.execute("PRAGMA table_info(global_time_config)")
        global_config_columns = [col[1] for col in cursor.fetchall()]
        
        if 'is33mail' not in global_config_columns:
            print("🔄 Agregando campo is33mail a global_time_config...")
            cursor.execute("ALTER TABLE global_time_config ADD COLUMN is33mail INTEGER DEFAULT 1")
        
        if 'domain' not in global_config_columns:
            print("🔄 Agregando campo domain a global_time_config...")
            cursor.execute("ALTER TABLE global_time_config ADD COLUMN domain TEXT")
        
        if 'fill_domain' not in global_config_columns:
            print("🔄 Agregando campo fill_domain a global_time_config...")
            cursor.execute("ALTER TABLE global_time_config ADD COLUMN fill_domain INTEGER DEFAULT 0")
        
        if 'random_domains' not in global_config_columns:
            print("🔄 Agregando campo random_domains a global_time_config...")
            cursor.execute("ALTER TABLE global_time_config ADD COLUMN random_domains INTEGER DEFAULT 0")
        
        if 'random_domain_tlds' not in global_config_columns:
            print("🔄 Agregando campo random_domain_tlds a global_time_config...")
            cursor.execute("ALTER TABLE global_time_config ADD COLUMN random_domain_tlds TEXT")

        # 🔹 Tabla para pool de User-Agents remotos del creator (lista global enviada por servidor)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS creator_user_agents_pool (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_agents_json TEXT NOT NULL DEFAULT '[]',
                used_user_agents_json TEXT NOT NULL DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        cursor.execute("PRAGMA table_info(creator_user_agents_pool)")
        ua_pool_cols = [col[1] for col in cursor.fetchall()]
        if 'used_user_agents_json' not in ua_pool_cols:
            print("🔄 Agregando campo used_user_agents_json a creator_user_agents_pool...")
            cursor.execute(
                "ALTER TABLE creator_user_agents_pool ADD COLUMN used_user_agents_json TEXT NOT NULL DEFAULT '[]'"
            )
        cursor.execute("SELECT COUNT(*) FROM creator_user_agents_pool")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO creator_user_agents_pool (id, user_agents_json, used_user_agents_json) VALUES (1, ?, ?)",
                ('[]', '[]'),
            )
        
        # 🔹 Tabla para dominios (múltiples dominios con configuración de relleno)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                fill_domain INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        
        # 🔹 Terminaciones TLD para dominios aleatorios (tabla editable en UI)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS random_tld_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tld TEXT NOT NULL UNIQUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        
        cursor.execute("SELECT COUNT(*) FROM random_tld_entries")
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT random_domain_tlds FROM global_time_config WHERE id = 1")
            _r = cursor.fetchone()
            if _r and _r[0]:
                try:
                    from app.creator.computer_actions import parse_configured_random_tlds
                    _parts = parse_configured_random_tlds(_r[0]) or []
                except Exception:
                    _parts = []
                for _i, _t in enumerate(_parts):
                    try:
                        cursor.execute(
                            "INSERT INTO random_tld_entries (tld, sort_order) VALUES (?, ?)",
                            (_t, _i),
                        )
                    except sqlite3.IntegrityError:
                        pass
        
        _sync_random_tlds_global_column(conn)
        
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

        for _pr_col, _pr_sql in (
            ("proxy_rotation_enabled", "ALTER TABLE creator_setting ADD COLUMN proxy_rotation_enabled INTEGER DEFAULT 0"),
            ("proxy_rotation_link", "ALTER TABLE creator_setting ADD COLUMN proxy_rotation_link TEXT"),
        ):
            cursor.execute("PRAGMA table_info(creator_setting)")
            _cols_now = [col[1] for col in cursor.fetchall()]
            if _pr_col not in _cols_now:
                try:
                    cursor.execute(_pr_sql)
                    print(f"✅ Columna {_pr_col} agregada a creator_setting")
                except sqlite3.OperationalError:
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
            },
            {
                'version': 4,
                'description': 'Agregar columna proxy_extension_click a creator_coordinates',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_extension_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 5,
                'description': 'Agregar columna activate_proxy_click a creator_coordinates',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN activate_proxy_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 6,
                'description': 'Agregar columna disable_proxy_click a creator_coordinates',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN disable_proxy_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 7,
                'description': 'Coordenadas rotación proxy: proxy_rotation_url_click',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_rotation_url_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 8,
                'description': 'Coordenadas rotación proxy: proxy_rotation_rotate_click',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_rotation_rotate_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 9,
                'description': 'Coordenadas rotación proxy: proxy_rotation_confirm_click',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_rotation_confirm_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 10,
                'description': 'Rotación proxy: clic navegador (proxy_rotation_browser_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_rotation_browser_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 11,
                'description': 'Rotación proxy: barra búsqueda (proxy_rotation_search_bar_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_rotation_search_bar_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 12,
                'description': 'Rotación proxy: cerrar navegador (proxy_rotation_close_browser_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN proxy_rotation_close_browser_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 13,
                'description': 'User-Agent: clic extensión (user_agent_extension_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN user_agent_extension_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 14,
                'description': 'User-Agent: clic extraer valor (user_agent_extract_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN user_agent_extract_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 15,
                'description': 'User-Agent: clic aplicar (user_agent_apply_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN user_agent_apply_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 16,
                'description': 'User-Agent: clic fuera de extensión (user_agent_outside_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN user_agent_outside_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 17,
                'description': 'Post-registro: abrir nueva pestaña (new_tab_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN new_tab_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 18,
                'description': 'Post-registro: nueva pestaña LinkedIn (linkedin_new_tab_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN linkedin_new_tab_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 19,
                'description': 'Post-registro: pegar contraseña (paste_password_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN paste_password_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 20,
                'description': 'Post-registro: opciones de usuario (user_options_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN user_options_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 21,
                'description': 'Post-registro: cerrar sesión (logout_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN logout_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 22,
                'description': 'Post-éxito: barra búsqueda LinkedIn (search_bar_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN search_bar_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 23,
                'description': 'Post-éxito: Jobs (jobs_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN jobs_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 24,
                'description': 'Post-éxito: logo LinkedIn (linkedin_logo_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN linkedin_logo_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 25,
                'description': 'Post-éxito: login with email (login_with_email_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN login_with_email_click TEXT NOT NULL DEFAULT ''"
            },
            {
                'version': 26,
                'description': 'Post-éxito: clic Email (clic_email_click)',
                'sql': "ALTER TABLE creator_coordinates ADD COLUMN clic_email_click TEXT NOT NULL DEFAULT ''"
            },
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



def save_bot_settings(
    iterations,
    pause_minutes=20,
    enable_adb=True,
    emails_per_batch=5,
    proxy_via_coordinates=False,
    proxy_via_windows=False,
    enable_creator_user_agent_actions=False,
):
    """Guarda ajustes del bot. enable_proxy se deriva: True si algún modo de proxy está activo."""
    enable_proxy = bool(proxy_via_coordinates or proxy_via_windows)
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Verificamos si ya hay una configuración guardada
        cursor.execute("SELECT id FROM bot_settings LIMIT 1")
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE bot_settings
                SET iterations = ?, pause_minutes = ?, enable_adb = ?, enable_proxy = ?, emails_per_batch = ?,
                    proxy_via_coordinates = ?, proxy_via_windows = ?,
                    enable_creator_user_agent_actions = ?
                WHERE id = ?
                """,
                (
                    iterations,
                    pause_minutes,
                    int(enable_adb),
                    int(enable_proxy),
                    emails_per_batch,
                    int(bool(proxy_via_coordinates)),
                    int(bool(proxy_via_windows)),
                    int(bool(enable_creator_user_agent_actions)),
                    existing[0],
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO bot_settings (
                    iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch,
                    proxy_via_coordinates, proxy_via_windows, enable_creator_user_agent_actions
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    iterations,
                    pause_minutes,
                    int(enable_adb),
                    int(enable_proxy),
                    emails_per_batch,
                    int(bool(proxy_via_coordinates)),
                    int(bool(proxy_via_windows)),
                    int(bool(enable_creator_user_agent_actions)),
                ),
            )

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
        cursor.execute("PRAGMA table_info(bot_settings)")
        cols = [r[1] for r in cursor.fetchall()]
        has_proxy_mode = "proxy_via_coordinates" in cols and "proxy_via_windows" in cols
        has_ua_actions = "enable_creator_user_agent_actions" in cols
        if has_proxy_mode:
            if has_ua_actions:
                cursor.execute(
                    """
                    SELECT iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch,
                           COALESCE(proxy_via_coordinates, 0), COALESCE(proxy_via_windows, 0),
                           COALESCE(enable_creator_user_agent_actions, 0)
                    FROM bot_settings LIMIT 1
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch,
                           COALESCE(proxy_via_coordinates, 0), COALESCE(proxy_via_windows, 0)
                    FROM bot_settings LIMIT 1
                    """
                )
        else:
            cursor.execute(
                "SELECT iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch FROM bot_settings LIMIT 1"
            )
        row = cursor.fetchone()
        conn.close()
        if row:
            if has_proxy_mode and len(row) >= 7:
                pc, pw = bool(row[5]), bool(row[6])
            else:
                pc, pw = False, bool(row[3])
            if has_proxy_mode and has_ua_actions and len(row) >= 8:
                ua_act = bool(row[7])
            else:
                ua_act = False
            return {
                "iterations": row[0],
                "pause_minutes": row[1],
                "enable_adb": bool(row[2]),
                "enable_proxy": bool(row[3]),
                "emails_per_batch": row[4],
                "proxy_via_coordinates": pc,
                "proxy_via_windows": pw,
                "enable_creator_user_agent_actions": ua_act,
            }
        else:
            return None
    except Exception as e:
        print(f"❌ Error al obtener configuración: {e}")
        return None


def save_bot_connection_config(bot_name, bot_type='creador'):
    """Guarda la configuración de conexión del bot (nombre y tipo)
    Nota: Se guarda como 'creador' para compatibilidad con la API"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Asegurar que siempre se guarde como 'creador' para la API
        if bot_type == 'confirmador':
            bot_type = 'creador'
        
        cursor.execute("SELECT id FROM bot_settings LIMIT 1")
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE bot_settings
                SET bot_name = ?, bot_type = ?
                WHERE id = ?
            ''', (bot_name, bot_type, existing[0]))
        else:
            # Si no existe configuración, crear una con valores por defecto
            cursor.execute('''
                INSERT INTO bot_settings (iterations, pause_minutes, bot_name, bot_type)
                VALUES (?, ?, ?, ?)
            ''', (1, 20, bot_name, bot_type))
        
        conn.commit()
        conn.close()
        print(f"✅ Configuración de conexión guardada: {bot_name} ({bot_type})")
        return True
    except Exception as e:
        print(f"❌ Error al guardar configuración de conexión: {e}")
        return False


def get_bot_connection_config():
    """Obtiene la configuración de conexión del bot (nombre y tipo)
    Nota: Este bot se conecta como tipo 'creador' para compatibilidad con la API"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT bot_name, bot_type FROM bot_settings LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            # Si el tipo guardado es 'confirmador', usar 'creador' para la conexión
            bot_type = row[1] if row[1] else "creador"
            if bot_type == "confirmador":
                bot_type = "creador"
            return {
                "bot_name": row[0],
                "bot_type": bot_type
            }
        return {
            "bot_name": "ConfirmaBot",
            "bot_type": "creador"  # Se conecta como 'creador' para compatibilidad con la API
        }
    except Exception as e:
        print(f"❌ Error al obtener configuración de conexión: {e}")
        return {
            "bot_name": "ConfirmaBot",
            "bot_type": "creador"
        }



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


def set_active_browser_by_name(browser_name):
    """
    Activa solo el navegador indicado por nombre (case-insensitive)
    y desactiva los demás.

    Args:
        browser_name (str): Nombre del navegador a activar

    Returns:
        tuple: (bool, str) -> (éxito, mensaje)
    """
    try:
        if not browser_name or not str(browser_name).strip():
            return False, "Nombre de navegador vacío"

        target_name = str(browser_name).strip()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name
            FROM browsers
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
            LIMIT 1
            """,
            (target_name,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, f"Navegador '{target_name}' no existe en la configuración local"

        selected_id, selected_name = row[0], row[1]

        cursor.execute("UPDATE browsers SET isActive = 0 WHERE isActive != 0")
        cursor.execute("UPDATE browsers SET isActive = 1 WHERE id = ?", (selected_id,))

        conn.commit()
        conn.close()
        return True, f"Navegador remoto aplicado: {selected_name}"
    except Exception as e:
        return False, f"Error activando navegador remoto: {e}"


def set_active_browsers_by_names(browser_names):
    """
    Activa exactamente los navegadores indicados (por nombre, case-insensitive)
    y desactiva el resto. Si falta algún nombre en la BD local, no modifica activos.

    Args:
        browser_names: lista de nombres (orden conservado para mensajes)

    Returns:
        tuple: (bool, str) -> (éxito, mensaje)
    """
    try:
        if not browser_names:
            return True, None

        cleaned: list[str] = []
        seen: set[str] = set()
        for x in browser_names:
            s = str(x).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            cleaned.append(s)

        if not cleaned:
            return True, None

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        resolved_ids: list[tuple[int, str]] = []
        missing: list[str] = []
        for name in cleaned:
            cursor.execute(
                """
                SELECT id, name
                FROM browsers
                WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
                LIMIT 1
                """,
                (name,),
            )
            row = cursor.fetchone()
            if not row:
                missing.append(name)
            else:
                resolved_ids.append((row[0], row[1]))

        if missing:
            conn.close()
            return False, (
                "Los siguientes navegadores del servidor no existen en este bot: "
                + ", ".join(missing)
            )

        cursor.execute("UPDATE browsers SET isActive = 0 WHERE isActive != 0")
        for bid, _ in resolved_ids:
            cursor.execute("UPDATE browsers SET isActive = 1 WHERE id = ?", (bid,))

        conn.commit()
        conn.close()
        labels = ", ".join(real for _, real in resolved_ids)
        return True, f"Navegadores remotos aplicados: {labels}"
    except Exception as e:
        return False, f"Error activando navegadores remotos: {e}"


def set_creator_user_agent_by_browser_name(browser_name, user_agent):
    """
    Actualiza el User-Agent del creator para el navegador indicado por nombre.
    Mantiene el resto de configuración existente.
    """
    try:
        if not browser_name or not str(browser_name).strip():
            return False, "Nombre de navegador vacío"
        if not user_agent or not str(user_agent).strip():
            return False, "User-Agent vacío"

        target_name = str(browser_name).strip()
        ua_value = str(user_agent).strip()

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name
            FROM browsers
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
            LIMIT 1
            """,
            (target_name,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, f"Navegador '{target_name}' no existe en la configuración local"

        browser_id, browser_real_name = row[0], row[1]
        current = get_creator_setting(browser_id) or {}

        ok = save_creator_setting(
            browser_id=browser_id,
            user_agent=ua_value,
            accounts_to_create=current.get('accounts_to_create', 1),
            notification_email=current.get('notification_email'),
            isInVps=current.get('isInVps'),
            proxy_rotation_enabled=current.get('proxy_rotation_enabled'),
            proxy_rotation_link=current.get('proxy_rotation_link'),
        )
        if not ok:
            return False, f"No se pudo guardar User-Agent para {browser_real_name}"

        return True, f"User-Agent remoto aplicado para {browser_real_name}"
    except Exception as e:
        return False, f"Error aplicando User-Agent remoto: {e}"


def save_creator_user_agents_pool(user_agents):
    """
    Guarda la lista global de User-Agents de creator enviada por servidor.

    - Entrada esperada: list[str]
    - Limpieza: trim, ignora vacíos, dedup case-insensitive preservando orden.
    """
    try:
        if user_agents is None:
            return True, "Sin cambios: payload de User-Agents no enviado"
        if not isinstance(user_agents, list):
            return False, "Formato inválido: se esperaba lista de User-Agents"

        cleaned = []
        seen = set()
        for raw in user_agents:
            s = str(raw or "").strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            cleaned.append(s)

        payload_json = json.dumps(cleaned, ensure_ascii=False)

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO creator_user_agents_pool (id, user_agents_json, used_user_agents_json, updated_at)
            VALUES (1, ?, '[]', CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                user_agents_json = excluded.user_agents_json,
                used_user_agents_json = '[]',
                updated_at = CURRENT_TIMESTAMP
            """,
            (payload_json,),
        )
        conn.commit()
        conn.close()
        return True, f"Pool de User-Agents creator actualizado ({len(cleaned)} elementos)"
    except Exception as e:
        return False, f"Error guardando pool de User-Agents creator: {e}"


def get_creator_user_agents_pool():
    """
    Devuelve la lista global de User-Agents de creator almacenada localmente.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT user_agents_json FROM creator_user_agents_pool WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if not row or not row[0]:
            return []
        data = json.loads(row[0])
        if not isinstance(data, list):
            return []
        return [str(x).strip() for x in data if str(x).strip()]
    except Exception as e:
        print(f"❌ Error obteniendo pool de User-Agents creator: {e}")
        return []


def get_next_creator_user_agent_random():
    """
    Obtiene un User-Agent aleatorio sin repetir hasta agotar el pool.
    Cuando se agotan, reinicia el ciclo automáticamente.
    """
    try:
        import random

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_agents_json, used_user_agents_json FROM creator_user_agents_pool WHERE id = 1"
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        all_raw = json.loads(row[0] or "[]")
        used_raw = json.loads(row[1] or "[]")
        all_list = [str(x).strip() for x in all_raw if str(x).strip()]
        if not all_list:
            conn.close()
            return None

        used_set = {str(x).strip().lower() for x in used_raw if str(x).strip()}
        available = [ua for ua in all_list if ua.lower() not in used_set]

        # Si ya se usaron todos, reiniciar ciclo
        if not available:
            used_set = set()
            available = list(all_list)

        picked = random.choice(available)
        used_set.add(picked.lower())
        used_to_save = [ua for ua in all_list if ua.lower() in used_set]

        cursor.execute(
            """
            UPDATE creator_user_agents_pool
            SET used_user_agents_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (json.dumps(used_to_save, ensure_ascii=False),),
        )
        conn.commit()
        conn.close()
        return picked
    except Exception as e:
        print(f"❌ Error obteniendo User-Agent aleatorio: {e}")
        return None


def clear_creator_user_agents_pool():
    """
    Limpia (deja vacía) la lista global de User-Agents de creator.
    """
    return save_creator_user_agents_pool([])


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

        column_names = _creator_coordinates_column_names(cursor)
        if not column_names:
            conn.close()
            return False

        cursor.execute("SELECT * FROM creator_coordinates WHERE browser_id = ?", (browser_id,))
        existing_row = cursor.fetchone()

        if existing_row:
            data = {
                column_names[i]: existing_row[i]
                for i in range(min(len(column_names), len(existing_row)))
            }
        else:
            data = {name: "" for name in column_names}
            data["browser_id"] = browser_id

        data["browser_id"] = browser_id

        if coordinates_dict:
            for field, coord in coordinates_dict.items():
                if field in data:
                    data[field] = coord

        for field, coord in kwargs.items():
            if field in data:
                data[field] = coord

        insert_columns = [c for c in column_names if c != "id"]
        placeholders = ",".join("?" * len(insert_columns))
        columns_sql = ",".join(insert_columns)
        values_tuple = tuple(data.get(c, "") for c in insert_columns)

        cursor.execute(
            f"INSERT OR REPLACE INTO creator_coordinates ({columns_sql}) VALUES ({placeholders})",
            values_tuple,
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
        column_names = _creator_coordinates_column_names(cursor)
        cursor.execute("SELECT * FROM creator_coordinates WHERE browser_id = ?", (browser_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        full = {
            column_names[i]: row[i] if i < len(row) else ""
            for i in range(len(column_names))
        }

        # Misma forma que antes: solo campos de coordenadas (sin id ni browser_id)
        coord_keys = [c for c in column_names if c not in ("id", "browser_id")]
        all_coords = {k: full.get(k, "") for k in coord_keys}

        if not field_names:
            return all_coords

        result = {name: all_coords.get(name, "") for name in field_names if name in all_coords}
        return result if result else None

    except Exception as e:
        print(f"❌ Error al obtener coordenadas del creator: {e}")
        return None


#! FUNCIONES DE CREATOR_SETTING
def save_creator_setting(browser_id, user_agent, accounts_to_create=1, scheduled_time=None, timezone=None, notification_email=None, cycle_time_minutes=None, time_config_type='manual', accounts_per_cycle=None, isInVps=None, is33mail=None, domain=None, proxy_rotation_enabled=None, proxy_rotation_link=None):
    """
    Guarda o actualiza la configuración del creator para un navegador específico
    NOTA: Los campos de tiempo (scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle) 
    y dominio (is33mail, domain) ahora se ignoran aquí y deben guardarse usando save_global_time_config()
    
    Args:
        browser_id (int): ID del navegador
        user_agent (str): User agent a utilizar
        accounts_to_create (int): Cantidad de cuentas a crear (default: 1)
        scheduled_time (str): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        timezone (str): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        notification_email (str): Email para recibir notificaciones (opcional)
        cycle_time_minutes (int): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        time_config_type (str): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        accounts_per_cycle (int): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        isInVps (bool): Si está ejecutándose en VPS (True) o máquina física (False) (opcional)
        is33mail (bool): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        domain (str): IGNORADO - usar save_global_time_config() (opcional, mantenido por compatibilidad)
        proxy_rotation_enabled (bool|None): Si se usa enlace + coordenadas de rotación de proxy; None conserva el valor guardado
        proxy_rotation_link (str|None): URL del panel de rotación; None conserva el valor guardado
    
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
        
        cursor.execute(
            """
            SELECT COALESCE(proxy_rotation_enabled, 0), proxy_rotation_link
            FROM creator_setting WHERE browser_id = ?
            """,
            (browser_id,),
        )
        ex_proxy = cursor.fetchone()
        pr_en = int(ex_proxy[0]) if ex_proxy else 0
        pr_link = ex_proxy[1] if ex_proxy else None
        if proxy_rotation_enabled is not None:
            pr_en = 1 if proxy_rotation_enabled else 0
        if proxy_rotation_link is not None:
            s = str(proxy_rotation_link).strip()
            pr_link = s if s else None

        # Insertar o actualizar (UPSERT) - NO guardar campos de tiempo ni dominio
        cursor.execute('''
            INSERT OR REPLACE INTO creator_setting (browser_id, user_agent, accounts_to_create, notification_email, isInVps, proxy_rotation_enabled, proxy_rotation_link)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (browser_id, user_agent, accounts_to_create, notification_email, isInVps_int, pr_en, pr_link))
        
        conn.commit()
        conn.close()
        print(f"✅ Configuración del creator guardada para navegador {browser_id}: UA={user_agent}, Cuentas={accounts_to_create}, Notificación={notification_email}, isInVps={isInVps}, proxy_rotación={bool(pr_en)}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar configuración del creator: {e}")
        return False


def get_creator_setting(browser_id):
    """
    Obtiene la configuración del creator para un navegador específico
    Combina la configuración del navegador con la configuración global de tiempo
    
    Args:
        browser_id (int): ID del navegador
    
    Returns:
        dict: Diccionario con user_agent, accounts_to_create, scheduled_time, timezone, notification_email, 
              cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps, is33mail y domain, 
              o None si no existe la configuración del navegador
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Habilitar claves foráneas
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_agent, accounts_to_create, notification_email, isInVps, COALESCE(proxy_rotation_enabled, 0), proxy_rotation_link FROM creator_setting WHERE browser_id = ?",
            (browser_id,),
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Convertir integer a boolean para isInVps (None si no está configurado)
            isInVps_bool = None
            if row[3] is not None:
                isInVps_bool = bool(row[3])
            
            # Obtener configuración global de tiempo y dominio
            global_time_config = get_global_time_config()
            
            return {
                'user_agent': row[0],
                'accounts_to_create': row[1],
                'notification_email': row[2],
                'isInVps': isInVps_bool,  # Boolean o None
                'proxy_rotation_enabled': bool(row[4]),
                'proxy_rotation_link': row[5],
                # Campos de tiempo y dominio desde configuración global
                'scheduled_time': global_time_config['scheduled_time'],
                'timezone': global_time_config['timezone'],
                'cycle_time_minutes': global_time_config['cycle_time_minutes'],
                'time_config_type': global_time_config['time_config_type'],
                'accounts_per_cycle': global_time_config['accounts_per_cycle'],
                'is33mail': global_time_config['is33mail'],  # Boolean o None
                'domain': global_time_config['domain'],  # String o None
                'fill_domain': global_time_config['fill_domain'],  # Boolean o None
                'random_domains': global_time_config.get('random_domains', False),
                'random_domain_tlds': global_time_config.get('random_domain_tlds'),
                'random_tld_list': get_random_tld_strings_ordered(),
            }
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener configuración del creator: {e}")
        return None


def clear_scheduled_time(browser_id):
    """
    Elimina la hora programada de la configuración del creator para un navegador específico
    (DEPRECADO: Ahora se usa configuración global)
    
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


#! FUNCIONES DE CONFIGURACIÓN GLOBAL DE TIEMPO Y DOMINIO
def save_global_time_config(scheduled_time=None, timezone=None, cycle_time_minutes=None, time_config_type='manual', accounts_per_cycle=None, is33mail=None, domain=None, fill_domain=None, random_domains=None, random_domain_tlds=...):
    """
    Guarda o actualiza la configuración global de tiempo (hora programada y ciclo) y dominio
    Esta configuración es global para todos los navegadores
    
    Args:
        scheduled_time (str): Hora programada en formato HH:MM (opcional)
        timezone (str): Zona horaria (opcional)
        cycle_time_minutes (int): Tiempo en minutos para el ciclo (opcional)
        time_config_type (str): Tipo de configuración ('scheduled', 'cycle', 'both', 'manual')
        accounts_per_cycle (int): Cantidad de cuentas a crear por ciclo (opcional)
        is33mail (bool): Si se usa 33mail (True) o no (False) (opcional)
        domain (str): Dominio a utilizar (opcional)
        fill_domain (bool): Si se debe rellenar el dominio (True) o no (False) (opcional)
        random_domains (bool): Si se generan dominios aleatorios locales en lugar de 33mail o la tabla domains (opcional)
        random_domain_tlds (str|None): Texto com,net,gov para TLDs de dominios aleatorios; None limpia el campo (usa lista por defecto).
            Omitir el argumento (dejar default) conserva el valor guardado.
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Obtener configuración actual directamente de la base de datos para preservar valores que no se están actualizando
        cursor.execute("SELECT is33mail, domain, fill_domain, random_domains, random_domain_tlds FROM global_time_config WHERE id = 1")
        current_row = cursor.fetchone()
        
        # Preservar valores existentes si no se proporcionan nuevos valores
        if is33mail is None:
            if current_row and current_row[0] is not None:
                is33mail = bool(current_row[0])
            else:
                is33mail = True  # Valor por defecto
        if domain is None:
            if current_row and current_row[1] is not None:
                domain = current_row[1]
            else:
                domain = None
        if fill_domain is None:
            if current_row and current_row[2] is not None:
                fill_domain = bool(current_row[2])
            else:
                fill_domain = False  # Valor por defecto
        if random_domains is None:
            if current_row and len(current_row) > 3 and current_row[3] is not None:
                random_domains = bool(current_row[3])
            else:
                random_domains = False
        if random_domain_tlds is ...:
            if current_row and len(current_row) > 4:
                random_domain_tlds = current_row[4]
            else:
                random_domain_tlds = None
        
        # Convertir boolean a integer para SQLite (True = 1, False = 0)
        is33mail_int = 1 if is33mail is True else (0 if is33mail is False else None)
        fill_domain_int = 1 if fill_domain is True else (0 if fill_domain is False else None)
        random_domains_int = 1 if random_domains is True else (0 if random_domains is False else None)
        
        # Actualizar el único registro (siempre ID 1)
        cursor.execute('''
            UPDATE global_time_config 
            SET scheduled_time = ?, timezone = ?, cycle_time_minutes = ?, 
                time_config_type = ?, accounts_per_cycle = ?, is33mail = ?, domain = ?, fill_domain = ?, random_domains = ?, random_domain_tlds = ?
            WHERE id = 1
        ''', (scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail_int, domain, fill_domain_int, random_domains_int, random_domain_tlds))
        
        # Si no existe ningún registro, crear uno
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO global_time_config (id, scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail, domain, fill_domain, random_domains, random_domain_tlds)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail_int, domain, fill_domain_int, random_domains_int, random_domain_tlds))
        
        conn.commit()
        conn.close()
        print(f"✅ Configuración global guardada: Hora={scheduled_time}, Zona={timezone}, Ciclo={cycle_time_minutes}min, Tipo={time_config_type}, CuentasPorCiclo={accounts_per_cycle}, is33mail={is33mail}, domain={domain}, fill_domain={fill_domain}, random_domains={random_domains}, random_domain_tlds={random_domain_tlds}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar configuración global: {e}")
        return False


def get_global_time_config():
    """
    Obtiene la configuración global de tiempo (hora programada y ciclo) y dominio
    Esta configuración es global para todos los navegadores
    
    Returns:
        dict: Diccionario con scheduled_time, timezone, cycle_time_minutes, time_config_type, 
              accounts_per_cycle, is33mail y domain, o valores por defecto si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail, domain, fill_domain, random_domains, random_domain_tlds FROM global_time_config WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Convertir integer a boolean para is33mail (None si no está configurado)
            is33mail_bool = None
            if row[5] is not None:
                is33mail_bool = bool(row[5])
            
            # Convertir integer a boolean para fill_domain (None si no está configurado)
            fill_domain_bool = None
            if row[7] is not None:
                fill_domain_bool = bool(row[7])
            
            random_domains_bool = False
            if len(row) > 8 and row[8] is not None:
                random_domains_bool = bool(row[8])
            
            random_tlds_str = row[9] if len(row) > 9 else None
            
            return {
                'scheduled_time': row[0],
                'timezone': row[1],
                'cycle_time_minutes': row[2] if row[2] is not None else 60,
                'time_config_type': row[3] if row[3] is not None else 'manual',
                'accounts_per_cycle': row[4] if row[4] is not None else 1,
                'is33mail': is33mail_bool,  # Boolean o None
                'domain': row[6],  # String o None
                'fill_domain': fill_domain_bool,  # Boolean o None
                'random_domains': random_domains_bool,
                'random_domain_tlds': random_tlds_str
            }
        
        # Valores por defecto si no existe
        return {
            'scheduled_time': None,
            'timezone': None,
            'cycle_time_minutes': 60,
            'time_config_type': 'manual',
            'accounts_per_cycle': 1,
            'is33mail': True,  # Por defecto True
            'domain': None,
            'fill_domain': False,  # Por defecto False
            'random_domains': False,
            'random_domain_tlds': None
        }
        
    except Exception as e:
        print(f"❌ Error al obtener configuración global: {e}")
        # Retornar valores por defecto en caso de error
        return {
            'scheduled_time': None,
            'timezone': None,
            'cycle_time_minutes': 60,
            'time_config_type': 'manual',
            'accounts_per_cycle': 1,
            'is33mail': True,  # Por defecto True
            'domain': None,
            'fill_domain': False,  # Por defecto False
            'random_domains': False,
            'random_domain_tlds': None
        }


# =================================
#         DOMAINS MANAGEMENT
# =================================

def create_domain(domain, fill_domain=False, is_active=True):
    """
    Crea un nuevo dominio
    
    Args:
        domain (str): Dominio (con o sin @ al inicio)
        fill_domain (bool): Si se debe aplicar relleno a este dominio
        is_active (bool): Si el dominio está activo
    
    Returns:
        int: ID del dominio creado, o None si hay error
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Asegurar que el dominio tenga @ al inicio
        domain_clean = domain if domain.startswith('@') else f"@{domain}"
        
        # Verificar que no exista ya este dominio
        cursor.execute("SELECT id FROM domains WHERE domain = ?", (domain_clean,))
        if cursor.fetchone():
            print(f"⚠️ El dominio {domain_clean} ya existe")
            conn.close()
            return None
        
        # Convertir boolean a integer
        fill_domain_int = 1 if fill_domain else 0
        is_active_int = 1 if is_active else 0
        
        cursor.execute('''
            INSERT INTO domains (domain, fill_domain, is_active)
            VALUES (?, ?, ?)
        ''', (domain_clean, fill_domain_int, is_active_int))
        
        domain_id = cursor.lastrowid
        conn.commit()
        conn.close()
        print(f"✅ Dominio creado: {domain_clean} (ID: {domain_id}, Relleno: {fill_domain}, Activo: {is_active})")
        return domain_id
        
    except Exception as e:
        print(f"❌ Error al crear dominio: {e}")
        return None

def get_all_domains(active_only=False):
    """
    Obtiene todos los dominios
    
    Args:
        active_only (bool): Si True, solo retorna dominios activos
    
    Returns:
        list: Lista de diccionarios con información de los dominios
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT id, domain, fill_domain, is_active FROM domains WHERE is_active = 1 ORDER BY id")
        else:
            cursor.execute("SELECT id, domain, fill_domain, is_active FROM domains ORDER BY id")
        
        rows = cursor.fetchall()
        conn.close()
        
        domains = []
        for row in rows:
            domains.append({
                'id': row[0],
                'domain': row[1],
                'fill_domain': bool(row[2]),
                'is_active': bool(row[3])
            })
        
        return domains
        
    except Exception as e:
        print(f"❌ Error al obtener dominios: {e}")
        return []

def get_domain_by_id(domain_id):
    """
    Obtiene un dominio por su ID
    
    Args:
        domain_id (int): ID del dominio
    
    Returns:
        dict: Información del dominio o None si no existe
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, domain, fill_domain, is_active FROM domains WHERE id = ?", (domain_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'domain': row[1],
                'fill_domain': bool(row[2]),
                'is_active': bool(row[3])
            }
        return None
        
    except Exception as e:
        print(f"❌ Error al obtener dominio: {e}")
        return None

def update_domain(domain_id, domain=None, fill_domain=None, is_active=None):
    """
    Actualiza un dominio
    
    Args:
        domain_id (int): ID del dominio
        domain (str, optional): Nuevo dominio (con o sin @ al inicio)
        fill_domain (bool, optional): Nueva configuración de relleno
        is_active (bool, optional): Nuevo estado activo/inactivo
    
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if domain is not None:
            domain_clean = domain if domain.startswith('@') else f"@{domain}"
            # Verificar que no exista otro dominio con el mismo nombre
            cursor.execute("SELECT id FROM domains WHERE domain = ? AND id != ?", (domain_clean, domain_id))
            if cursor.fetchone():
                print(f"⚠️ El dominio {domain_clean} ya existe en otro registro")
                conn.close()
                return False
            updates.append("domain = ?")
            values.append(domain_clean)
        
        if fill_domain is not None:
            fill_domain_int = 1 if fill_domain else 0
            updates.append("fill_domain = ?")
            values.append(fill_domain_int)
        
        if is_active is not None:
            is_active_int = 1 if is_active else 0
            updates.append("is_active = ?")
            values.append(is_active_int)
        
        if not updates:
            conn.close()
            return True  # No hay cambios
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(domain_id)
        
        query = f"UPDATE domains SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        print(f"✅ Dominio {domain_id} actualizado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al actualizar dominio: {e}")
        return False

def delete_domain(domain_id):
    """
    Elimina un dominio
    
    Args:
        domain_id (int): ID del dominio
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM domains WHERE id = ?", (domain_id,))
        
        conn.commit()
        conn.close()
        print(f"✅ Dominio {domain_id} eliminado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar dominio: {e}")
        return False


# =================================
#    TERMINACIONES TLD (dominios aleatorios)
# =================================

def get_random_tld_entries():
    """
    Lista todas las terminaciones configuradas para dominios aleatorios (orden de rotación).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, tld, sort_order FROM random_tld_entries ORDER BY sort_order ASC, id ASC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "tld": r[1], "sort_order": r[2]} for r in rows]
    except Exception as e:
        print(f"❌ Error al obtener terminaciones TLD: {e}")
        return []


def get_random_tld_strings_ordered():
    """Lista de strings TLD en orden; vacía = el creator usa TLD aleatorio cada vez."""
    return [e["tld"] for e in get_random_tld_entries()]


def get_domain_sync_payload():
    """Construye payload completo de dominios para sincronizar con servidor."""
    cfg = get_global_time_config() or {}
    return {
        "global_config": {
            "is33mail": bool(cfg.get("is33mail", True)),
            "random_domains": bool(cfg.get("random_domains", False)),
            "fill_domain": bool(cfg.get("fill_domain", False)),
            "domain": cfg.get("domain"),
        },
        "domains": get_all_domains(active_only=False),
        "random_tlds": get_random_tld_entries(),
    }


def apply_remote_domain_config(remote_payload):
    """
    Aplica configuración de dominios recibida desde servidor de forma atómica.
    Reemplaza tabla `domains` y `random_tld_entries`, y actualiza `global_time_config`.
    """
    try:
        if not isinstance(remote_payload, dict):
            return False, "Payload remoto inválido"

        global_cfg = remote_payload.get("global_config") or {}
        domains = remote_payload.get("domains") or []
        random_tlds = remote_payload.get("random_tlds") or []

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM domains")
        for item in domains:
            if not isinstance(item, dict):
                continue
            domain = (item.get("domain") or "").strip()
            if not domain:
                continue
            if not domain.startswith("@"):
                domain = f"@{domain}"
            fill_domain = 1 if bool(item.get("fill_domain", False)) else 0
            is_active = 1 if bool(item.get("is_active", True)) else 0
            cursor.execute(
                "INSERT INTO domains (domain, fill_domain, is_active) VALUES (?, ?, ?)",
                (domain, fill_domain, is_active),
            )

        cursor.execute("DELETE FROM random_tld_entries")
        from app.creator.computer_actions import _normalize_single_tld
        for index, item in enumerate(random_tlds):
            raw_tld = item.get("tld") if isinstance(item, dict) else item
            tld = _normalize_single_tld((raw_tld or "").strip())
            if not tld:
                continue
            cursor.execute(
                "INSERT OR IGNORE INTO random_tld_entries (tld, sort_order) VALUES (?, ?)",
                (tld, index),
            )

        conn.commit()
        conn.close()
        _sync_random_tlds_global_column()

        # No pisar ciclo/hora programada: save_global_time_config usa 'manual' por defecto y NULL en el resto.
        cfg_before = get_global_time_config() or {}
        ok = save_global_time_config(
            scheduled_time=cfg_before.get("scheduled_time"),
            timezone=cfg_before.get("timezone"),
            cycle_time_minutes=cfg_before.get("cycle_time_minutes"),
            time_config_type=cfg_before.get("time_config_type", "manual"),
            accounts_per_cycle=cfg_before.get("accounts_per_cycle"),
            is33mail=bool(global_cfg.get("is33mail", True)),
            random_domains=bool(global_cfg.get("random_domains", False)),
            fill_domain=bool(global_cfg.get("fill_domain", False)),
            domain=(global_cfg.get("domain") or None),
        )
        if not ok:
            return False, "No se pudo guardar configuración global de dominios"
        return True, "Configuración de dominios remota aplicada"
    except Exception as e:
        print(f"❌ Error al aplicar configuración remota de dominios: {e}")
        return False, str(e)


def add_random_tld_entry(raw_tld):
    """
    Añade una terminación (com, co.uk, ...). Devuelve id o None si inválida o duplicada.
    """
    try:
        from app.creator.computer_actions import _normalize_single_tld

        tld = _normalize_single_tld((raw_tld or "").strip())
        if not tld:
            return None
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM random_tld_entries")
        next_order = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO random_tld_entries (tld, sort_order) VALUES (?, ?)",
            (tld, next_order),
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        _sync_random_tlds_global_column()
        print(f"✅ TLD añadido: {tld} (id={new_id})")
        return new_id
    except sqlite3.IntegrityError:
        print(f"⚠️ La terminación '{raw_tld}' ya existe")
        return None
    except Exception as e:
        print(f"❌ Error al añadir TLD: {e}")
        return None


def update_random_tld_entry(entry_id, raw_tld):
    """Actualiza el texto de una terminación. True si OK."""
    try:
        from app.creator.computer_actions import _normalize_single_tld

        tld = _normalize_single_tld((raw_tld or "").strip())
        if not tld:
            return False
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("UPDATE random_tld_entries SET tld = ? WHERE id = ?", (tld, entry_id))
        if cursor.rowcount == 0:
            conn.close()
            return False
        conn.commit()
        conn.close()
        _sync_random_tlds_global_column()
        print(f"✅ TLD {entry_id} actualizado a {tld}")
        return True
    except sqlite3.IntegrityError:
        print("⚠️ Ya existe otra fila con ese TLD")
        return False
    except Exception as e:
        print(f"❌ Error al actualizar TLD: {e}")
        return False


def delete_random_tld_entry(entry_id):
    """Elimina una terminación. True si OK."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM random_tld_entries WHERE id = ?", (entry_id,))
        if cursor.rowcount == 0:
            conn.close()
            return False
        conn.commit()
        conn.close()
        _sync_random_tlds_global_column()
        print(f"✅ TLD {entry_id} eliminado")
        return True
    except Exception as e:
        print(f"❌ Error al eliminar TLD: {e}")
        return False


def get_next_domain_for_rotation():
    """
    Obtiene el siguiente dominio activo para rotación.
    Usa un contador simple basado en el timestamp para rotar entre dominios.
    
    Returns:
        dict: Información del dominio siguiente, o None si no hay dominios activos
    """
    try:
        domains = get_all_domains(active_only=True)
        if not domains:
            return None
        
        # Obtener el último dominio usado (almacenado en una tabla temporal o usar round-robin simple)
        # Por simplicidad, usaremos round-robin basado en el tiempo
        import time
        index = int(time.time()) % len(domains)
        return domains[index]
        
    except Exception as e:
        print(f"❌ Error al obtener siguiente dominio: {e}")
        return None

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
        url = build_api_url(f"/api/emails/next/{user_id}")
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