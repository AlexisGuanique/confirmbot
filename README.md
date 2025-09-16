# confirmbot


# ConfirmaBot

## Construcción del Ejecutable

### Método Rápido (Recomendado)
Usa los scripts de construcción automática:

**Para versión normal:**
```bash
build.bat
```

**Para versión DEBUG (con consola):**
```bash
build-debug.bat
```

### Método Manual
Si prefieres usar PyInstaller directamente:

**Versión normal (sin consola):**
```bash
pyinstaller --onefile --windowed --icon="favicon.ico" --name=ConfirmaBotHostinger main.py
```

**Versión DEBUG (con consola):**
```bash
pyinstaller --onefile --icon="favicon.ico" --name=ConfirmaBotHostinger-Debug main.py
```

## Estructura de Carpetas

Cuando ejecutes la aplicación, se crearán automáticamente estas carpetas al lado del ejecutable:

- `images/` - Carpeta para almacenar las imágenes del Creator
- `linkedin_accounts/` - Carpeta para almacenar las cuentas creadas

## Notas Importantes

- Las carpetas se crean automáticamente cuando la aplicación se ejecuta por primera vez
- Las imágenes se guardan en la carpeta `images/` al lado del ejecutable
- Los archivos de cuentas creadas se guardan en `linkedin_accounts/` al lado del ejecutable
- Esta estructura funciona tanto en desarrollo como en el ejecutable final