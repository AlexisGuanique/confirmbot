# Reporte completo de base de datos

Base: `C:/Users/Usuario/workspace/confirmbot/app/database\cookies.db`

Generado: 2026-04-13 09:17:21

## Resumen

| Tabla | Filas | Columnas |
|---|---:|---|
| actions | 0 | id, first_click, second_click, third_click, fourth_click |
| bot_settings | 1 | id, iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch, bot_name, bot_type |
| browser_images | 0 | id, browser_id, image_name, image_path |
| browsers | 10 | id, name, isActive |
| creator_coordinates | 10 | id, browser_id, brave_click, linkedin_fav_click, email_input_click, continue_button_click, name_input_click, continue_button2_click, close_captcha_click, close_number_click, cookie_editor_icon_click, save_cookie_clipboard_click, close_window, continue_button_click_optional, white_captcha_click, close_captcha_error_click, close_proxy_error_click |
| creator_email | 0 | id, email, created_at |
| creator_email_progress | 0 | id, last_used_email_id, total_emails_used, last_updated |
| creator_setting | 10 | id, browser_id, user_agent, accounts_to_create, scheduled_time, timezone, notification_email, google_sheets_enabled, google_sheets_name, google_credentials_file, cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps, is33mail, domain |
| domains | 6 | id, domain, fill_domain, is_active, created_at, updated_at |
| emails | 0 | id, email, email_hostinger, password_hostinger |
| global_time_config | 1 | id, scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail, domain, fill_domain, random_domains, random_domain_tlds |
| migrations | 3 | id, version, description, applied_at |
| nopecha_key | 0 | id, api_key |
| random_tld_entries | 2 | id, tld, sort_order, created_at |
| user | 1 | id, name, lastname, access_token |

## Datos completos por tabla

### actions

- Filas: **0**
- Columnas: id, first_click, second_click, third_click, fourth_click
- Archivo completo: `actions.csv`

### bot_settings

- Filas: **1**
- Columnas: id, iterations, pause_minutes, enable_adb, enable_proxy, emails_per_batch, bot_name, bot_type
- Archivo completo: `bot_settings.csv`

### browser_images

- Filas: **0**
- Columnas: id, browser_id, image_name, image_path
- Archivo completo: `browser_images.csv`

### browsers

- Filas: **10**
- Columnas: id, name, isActive
- Archivo completo: `browsers.csv`

### creator_coordinates

- Filas: **10**
- Columnas: id, browser_id, brave_click, linkedin_fav_click, email_input_click, continue_button_click, name_input_click, continue_button2_click, close_captcha_click, close_number_click, cookie_editor_icon_click, save_cookie_clipboard_click, close_window, continue_button_click_optional, white_captcha_click, close_captcha_error_click, close_proxy_error_click
- Archivo completo: `creator_coordinates.csv`

### creator_email

- Filas: **0**
- Columnas: id, email, created_at
- Archivo completo: `creator_email.csv`

### creator_email_progress

- Filas: **0**
- Columnas: id, last_used_email_id, total_emails_used, last_updated
- Archivo completo: `creator_email_progress.csv`

### creator_setting

- Filas: **10**
- Columnas: id, browser_id, user_agent, accounts_to_create, scheduled_time, timezone, notification_email, google_sheets_enabled, google_sheets_name, google_credentials_file, cycle_time_minutes, time_config_type, accounts_per_cycle, isInVps, is33mail, domain
- Archivo completo: `creator_setting.csv`

### domains

- Filas: **6**
- Columnas: id, domain, fill_domain, is_active, created_at, updated_at
- Archivo completo: `domains.csv`

### emails

- Filas: **0**
- Columnas: id, email, email_hostinger, password_hostinger
- Archivo completo: `emails.csv`

### global_time_config

- Filas: **1**
- Columnas: id, scheduled_time, timezone, cycle_time_minutes, time_config_type, accounts_per_cycle, is33mail, domain, fill_domain, random_domains, random_domain_tlds
- Archivo completo: `global_time_config.csv`

### migrations

- Filas: **3**
- Columnas: id, version, description, applied_at
- Archivo completo: `migrations.csv`

### nopecha_key

- Filas: **0**
- Columnas: id, api_key
- Archivo completo: `nopecha_key.csv`

### random_tld_entries

- Filas: **2**
- Columnas: id, tld, sort_order, created_at
- Archivo completo: `random_tld_entries.csv`

### user

- Filas: **1**
- Columnas: id, name, lastname, access_token
- Archivo completo: `user.csv`

