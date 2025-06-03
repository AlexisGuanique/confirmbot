def clean_domains(raw_lines):
    """Limpia las líneas del archivo, eliminando '@' y espacios."""
    return [line.strip().lstrip('@') for line in raw_lines if line.strip()]
