import os


# URL única del backend para TODO el cliente confirmbot.
# Se puede sobreescribir con variable de entorno sin tocar código.
BACKEND_BASE_URL = os.getenv("CONFIRMABOT_BACKEND_URL", "http://34.29.59.97").rstrip("/")

# Base para endpoints de autenticación.
AUTH_API_BASE_URL = f"{BACKEND_BASE_URL}/api/auth"


def build_api_url(path: str) -> str:
    """Construye una URL completa al backend usando la base centralizada."""
    if not path:
        return BACKEND_BASE_URL
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{BACKEND_BASE_URL}{path}"
