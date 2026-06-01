"""User-Agents remotos de la sesión actual (comando WebSocket del servidor)."""

_user_agents_by_browser: dict[str, str] = {}


def set_user_agents(mapping: dict | None) -> None:
    """Guarda los User-Agent recibidos del servidor, indexados por nombre de navegador."""
    global _user_agents_by_browser
    _user_agents_by_browser = {}
    if not mapping:
        return
    for name, ua in mapping.items():
        browser_name = str(name).strip()
        ua_value = (ua or "").strip() if ua is not None else ""
        if browser_name and ua_value:
            _user_agents_by_browser[browser_name] = ua_value


def clear_user_agents() -> None:
    """Limpia los User-Agent remotos de la sesión."""
    set_user_agents(None)


def get_remote_user_agent(browser_name: str | None = None) -> str | None:
    """Obtiene el User-Agent remoto para un navegador (búsqueda case-insensitive)."""
    if not browser_name:
        return None
    target = str(browser_name).strip()
    if not target:
        return None
    if target in _user_agents_by_browser:
        return _user_agents_by_browser[target]
    target_lower = target.lower()
    for key, ua in _user_agents_by_browser.items():
        if key.lower() == target_lower:
            return ua
    return None


def get_all_remote_user_agents() -> dict[str, str]:
    """Copia del mapa completo de User-Agents remotos de la sesión."""
    return dict(_user_agents_by_browser)
