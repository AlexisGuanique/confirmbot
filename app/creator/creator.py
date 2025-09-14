def execute_creator():
    """
    Función principal del creator que ejecuta todas las acciones
    """
    from app.database.database import get_creator_coordinates
    from app.creator.computer_actions import click_coordinates
    import time
    
    coordinates = get_creator_coordinates()
    if not coordinates:
        print("❌ No se encontraron coordenadas configuradas")
        return
    
    # Click en Brave
    brave_coords = coordinates.get("brave_click")
    if brave_coords:
        click_coordinates(brave_coords, double_click=True)
    else:
        print("⚠️ No se encontraron coordenadas para Brave")
        return
    
    # Esperar medio segundo antes del siguiente click
    time.sleep(0.5)
    
    # Click en LinkedIn fav
    linkedin_coords = coordinates.get("linkedin_fav_click")
    if linkedin_coords:
        click_coordinates(linkedin_coords)
    else:
        print("⚠️ No se encontraron coordenadas para LinkedIn fav")
