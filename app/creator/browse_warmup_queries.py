"""Consultas de ejemplo para browse_warmup_actions (solo CLI / pruebas).

Una cadena se elige al azar por ejecución. Contenido neutro y variado en español.
"""
from __future__ import annotations

# --- Por categoría (mantenimiento sencillo) ---

_CLIMA_TIEMPO = (
    "clima hoy",
    "pronóstico lluvia fin de semana",
    "temperatura máxima mañana",
    "índice UV qué significa",
    "cuándo cambia la hora",
    "alerta meteorológica qué hacer",
    "humedad relativa explicación",
    "viento fuerte consejos ventanas",
    "niebla conducción precauciones",
    "ola de calor hidratación",
    "tormenta eléctrica seguridad",
    "arcoíris doble por qué",
    "estación meteorológica casera",
    "barómetro para qué sirve",
)

_COCINA = (
    "recetas fáciles con pollo",
    "cómo hacer pan casero",
    "postres sin horno",
    "salsa pesto ingredientes",
    "tiempo de cocción arroz",
    "ensalada de verano ideas",
    "batido de frutas receta",
    "cómo cortar cebolla sin llorar",
    "guiso de lentejas tradicional",
    "tortilla patatas jugosa",
    "crema calabaza thermomix alternativa",
    "masa pizza fina casera",
    "fermentación masa madre pasos",
    "sushi en casa seguridad pescado",
    "marinar carne tiempos",
    "sous vide qué es principiantes",
    "sustituto nata cocina",
    "harina integral vs blanca diferencia",
    "levadura fresca seca equivalencia",
    "truco arroz no pegajoso",
    "cómo pelar tomates fácil",
    "caldo casero verduras",
    "aliño vinagreta proporciones",
    "microondas descongelar seguro",
    "conservas caseras botes esterilizar",
)

_SALUD_BIENESTAR = (
    "cuántas horas dormir recomendado",
    "estiramientos espalda oficina",
    "qué es la hidratación diaria",
    "beneficios caminar 30 minutos",
    "diferencia vitamina d y calcio",
    "ritmo cardíaco reposo normal",
    "qué es el índice masa corporal",
    "hábitos higiene sueño",
    "luz azul pantallas noche",
    "pausas activas trabajo remoto",
    "respiración diafragmática cómo",
    "tensión arterial valores orientativos",
    "qué es glucosa en ayunas",
    "fibra alimentaria alimentos",
    "probióticos naturales ejemplos",
)

_DEPORTE = (
    "resultados fútbol hoy",
    "reglas básicas tenis",
    "cómo empezar a correr principiantes",
    "calentamiento antes de gym",
    "mundial atletismo fechas",
    "entrenamiento fuerza full body",
    "HIIT qué es contraindicaciones",
    "comprar zapatillas running guía",
    "lesión esguince tobillo reposo",
    "hidratación deporte larga duración",
    "ciclismo rutas principiantes",
    "triatlón distancias tipos",
    "escalada bloque vs cuerda",
    "golf swing principiantes",
    "boxeo saco técnica básica",
    "artes marciales diferencias estilos",
    "padel saque flotado consejos",
    "voleibol rotación posiciones",
    "baloncesto reglas viajes",
    "hockey hierba reglas rápidas",
)

_TECNOLOGIA = (
    "mejores auriculares bluetooth calidad precio",
    "diferencia ssd y hdd",
    "qué es vpn para qué sirve",
    "cómo liberar espacio en el móvil",
    "router wifi doble banda",
    "monitor 27 pulgadas recomendaciones",
    "teclado mecánico silencioso",
    "ratón ergonómico síndrome túnel carpiano",
    "webcam 1080p iluminación",
    "micrófono usb podcast barato",
    "hub usb c qué comprar",
    "cable hdmi versiones diferencia",
    "tarjeta gráfica consumo energía",
    "fuente alimentación pc watt recomendado",
    "refrigeración pc pasta térmica",
    "linux distro principiantes ligera",
    "virtualización qué es ejemplo",
    "docker contenedor explicación simple",
    "git commit push diferencia básica",
    "api rest qué significa",
    "cifrado extremo a extremo qué es",
    "2fa autenticación dos pasos activar",
    "nube vs disco local ventajas",
    "smartwatch batería duración real",
    "tablet dibujo lápiz presión",
)

_HOGAR_BRICOLAJE = (
    "cómo quitar mancha de café ropa",
    "pintar pared paso a paso",
    "organizar armario pequeño",
    "plantas de interior poca luz",
    "filtro agua grifo tipos",
    "quitar cal mampara ducha",
    "desatascar fregadero métodos",
    "limpiar horno sin químicos fuertes",
    "quitar papel pintado fácil",
    "rellenar agujero pared yeso",
    "instalar estantería tacos pared",
    "nivel láser cómo usar",
    "sierra caladora seguridad",
    "lijadora orbital papel grano",
    "masilla madera secado",
    "barniz mate vs brillo",
    "cambiar mecanismo wc cisterna",
    "grifo gotea arandela",
    "termoestato programable ahorro",
    "purgar radiador pasos",
)

_VIAJES = (
    "lugares para visitar en europa",
    "qué llevar en maleta cabina",
    "mejor época viajar canarias",
    "cambio de moneda consejos",
    "seguro viaje qué cubre",
    "jet lag consejos vuelo largo",
    "documentación coche rent abroad genérico",
    "adaptador enchufe tipos países",
    "roaming datos móvil europa",
    "duty free líquidos avión",
    "check in online equipaje facturar",
    "asiento avión ventana pasillo",
    "mochila viaje 40 litros",
    "cubos compresión maleta",
    "botella plegable viaje",
)

_CULTURA_OCIO = (
    "estrenos cine esta semana",
    "series recomendadas drama",
    "libros bestseller no ficción",
    "museos gratis madrid",
    "festivales música verano",
    "teatro musical famoso títulos",
    "ópera principiantes por dónde empezar",
    "galería arte movimientos siglo XX",
    "fotografía calle composición",
    "cómic europeo recomendaciones",
    "podcast historia español",
    "documentales naturaleza streaming",
    "escape room consejos equipo",
    "juegos mesa estrategia familia",
    "rompecabezas 2000 piezas marcas",
)

_MUSICA_AUDIO = (
    "cómo afinar guitarra",
    "géneros música electrónica",
    "auriculares para estudiar",
    "ukulele acordes básicos",
    "piano teclado weighted keys",
    "bajo eléctrico amplificador casa",
    "interfaz audio home studio",
    "DAW gratuito principiantes",
    "sample rate audio explicación",
    "compresión dinámica música qué es",
)

_NATURALEZA_CIENCIA = (
    "por qué el cielo es azul",
    "tipos de nubes nombres",
    "cómo se forma un arcoíris",
    "animales en extinción lista",
    "diferencia meteorito asteroide",
    "fases de la luna hoy",
    "qué es la fotosíntesis simple",
    "cadena alimenticia ejemplo bosque",
    "bioma desierto características",
    "volcán tipos erupción",
    "terremoto escala richter",
    "marea alta baja causa",
    "corriente océano gulf stream",
    "árbol más alto del mundo",
    "flor nacional varios países",
    "abeja polinización importancia",
    "mariposa monarca migración",
    "oso panda alimentación",
    "delfín inteligencia estudios",
    "coral arrecife amenazas",
)

_HISTORIA_CURIOSIDADES = (
    "historia del café origen",
    "cuándo se inventó la imprenta",
    "antigua roma datos curiosos",
    "revolución industrial resumen corto",
    "edad media castillos función",
    "descubrimiento américa contexto simple",
    "revolución francesa causas breve",
    "primera guerra mundial inicio resumen",
    "muro berlín caída año",
    "línea tiempo evolución humano",
    "piratas caribe realidad vs ficción",
    "faros historia navegación",
    "ferrocarril revolución transporte",
    "telégrafo morse cómo funcionaba",
)

_AUTO_MOVILIDAD = (
    "revisión coche cuánto cuesta",
    "neumáticos invierno verano diferencia",
    "coche eléctrico autonomía real",
    "cómo cambiar rueda repuesto",
    "aceite motor cuándo cambiar",
    "filtro aire habitáculo síntomas",
    "pastillas freno desgaste señales",
    "batería coche arranque frío",
    "avería alternador síntomas",
    "adblue qué es diesel",
    "itv documentos necesarios genérico",
    "peaje telepeaje cómo funciona",
    "aparcamiento paralelo truco",
    "roundabout normas básicas",
    "bicicleta carril bici seguridad",
)

_EDUCACION_PRODUCTIVIDAD = (
    "técnicas estudio pomodoro",
    "cómo tomar apuntes eficaces",
    "aprender idiomas apps gratis",
    "qué es un mapa conceptual",
    "lectura rápida mitos",
    "memoria espaciada qué es",
    "resúmenes con IA uso responsable",
    "calendario bloques tiempo deep work",
    "bandeja entrada cero email",
    "reuniones efectivas agenda",
)

_FINANZAS_NEUTRO = (
    "qué es inflación explicación simple",
    "diferencia débito y crédito tarjeta",
    "fondo de emergencia cuánto ahorrar",
    "interés compuesto ejemplo numérico",
    "hipoteca tipo fijo variable diferencia",
    "comisión bancaria qué revisar",
    "transferencia sepa plazo orientativo",
    "criptomoneda riesgos generales",
    "ETF qué significa simple",
    "diversificar cartera qué implica",
)

_JARDIN_MASCOTAS = (
    "cómo regar orquídeas",
    "abono plantas cuándo usar",
    "perro no come causas comunes",
    "arena gato cambiar frecuencia",
    "poda rosales época",
    "semilleros tomate interior",
    "compost casero capas",
    "plaga pulgón remedios suaves",
    "césped sequía riego",
    "bonsái riego luz",
    "hamster jaula tamaño mínimo",
    "conejo heno tipos",
    "pez acuario ciclo nitrógeno simple",
    "tortuga agua temperatura",
)

_MODA_CUIDADO = (
    "tallas zapatos equivalencia",
    "cómo quitar chewing gum pelo",
    "protector solar fps diferencia",
    "lavar ropa deportiva olor",
    "quitar bolitas lana jersey",
    "planchar camisa orden correcto",
    "nudo corbata windsor simple",
    "barba recortadora longitud peines",
    "uñas fortalecer hábitos",
    "corte pelo capas vs degradado",
)

_ARTE_DIY = (
    "acuarelas para principiantes",
    "origami figura fácil",
    "cómo enmarcar un póster",
    "cerámica horno casero precauciones",
    "resina epoxi principiantes capa",
    "punto de cruz patrón gratis",
    "costura botón camisa",
    "patchwork trozos tela ideas",
    "vela aromática cera soja",
    "jabón casero sosa cuidado",
)

_IDIOMAS_REFERENCIA = (
    "traducir frases cortesía inglés",
    "sinónimos de importante",
    "convertir km a millas",
    "convertir celsius fahrenheit",
    "abreviaturas medidas internacionales",
    "prefijos métricos tabla",
    "mayúsculas títulos español normas",
    "diferencia hay ahí ay",
    "por qué porque cuándo tilde",
    "signos puntuación punto y coma",
)

_LOCAL_SERVICIOS = (
    "farmacia de guardia horario",
    "biblioteca pública cerca",
    "reciclaje plásticos tipos",
    "punto limpio residuos",
    "contenedor aceite usado",
    "compostaje urbano normas genéricas",
    "horario correos orientativo genérico",
    "cita médica app salud genérico",
)

_ENTRETENIMIENTO_LIGERO = (
    "chistes cortos buenos",
    "acertijos con respuesta",
    "cómo hacer burbujas jabón grandes",
    "tour virtual museo famoso",
    "karaoke canciones fáciles",
    "trivial cultura general online",
    "wordle variantes español",
    "meme historia internet resumen",
)

_VARIOS_LARGO = (
    "ideas desayuno saludable",
    "meriendas para niños fáciles",
    "yoga principiantes 10 minutos",
    "meditación guiada gratis",
    "cómo reducir ruido vecinos",
    "aire acondicionado mantenimiento básico",
    "enchufes viaje adaptadores",
    "mejor época plantar tulipanes",
    "cómo conservar hierbas frescas",
    "tarta de manzana fácil",
    "sopa de verduras clásica",
    "maratón cuidados primeros 10 km",
    "natación estilo crol consejos",
    "bicicleta urbana qué mirar al comprar",
    "patinete eléctrico normativa españa",
    "dron principiantes barato",
    "cámara reflex vs mirrorless",
    "editar fotos móvil apps",
    "comprar segundo mano seguro",
    "etiqueta email formal ejemplo",
    "currículum una página consejos",
    "foto perfil profesional consejos",
    "zoom entrevista trabajo tips",
    "teletrabajo ergonomía silla",
    "luz led calida o fria hogar",
    "humidificador bebé precauciones",
    "alergia polen síntomas",
    "picadura mosquito hinchazón",
    "picor garganta remedios caseros suaves",
    "dolor cabeza tensional qué hacer",
    "horario tiendas domingo",
    "gasolina 95 98 diferencia",
    "cargador coche móvil usb c",
    "memoria ram 8 vs 16 gb",
    "windows actualizar drivers",
    "antivirus gratis fiable",
    "contraseña segura ejemplos",
    "phishing correo cómo detectar",
    "copia seguridad fotos nube",
    "comprimir pdf sin perder calidad",
    "ocr imagen a texto gratis",
    "mapa conceptual online herramientas",
    "excel tablas dinámicas tutorial",
    "notion vs trello diferencias",
    "rss qué es para qué sirve",
)

_GEOGRAFIA_GENERAL = (
    "capital islandia nombre",
    "río más largo europa",
    "desierto más grande mundo",
    "cordillera himalaya altura aproximada",
    "océano más grande superficie",
    "lago más profundo mundo nombre",
    "isla más grande planeta",
    "estrecho famoso europa asia nombre",
    "cascada altura famosa américa",
    "parque nacional definición",
)

_ASTRONOMIA = (
    "planetas sistema solar orden",
    "vía láctea qué es simple",
    "eclipse solar vs lunar",
    "estación espacial iss visible",
    "telescopio principiantes recomendación",
    "constelación osa mayor encontrar",
    "planeta rojo nombre científico popular",
    "cometa cola por qué brilla",
    "agujero negro explicación niños",
    "big bang modelo simple",
)

_COCINA_MAS = (
    "wok carbono acero vs teflón",
    "cuchillo chef afilar piedra",
    "tabla cortar madera vs plástico",
    "termómetro cocina carne puntos",
    "descongelar nevera rápido seguro",
    "aceite oliva virgen extra uso",
    "vinagre blanco limpieza cocina",
    "bicarbonato usos hogar",
    "limón quitamanchas naturales",
    "microondas platos aptos símbolos",
)

_BEBIDAS = (
    "tipos de café espresso americano",
    "té verde vs negro oxidación",
    "infusiones relajantes sin cafeína",
    "cómo hacer kombucha casa",
    "smoothie verde ingredientes base",
    "agua con gas hacer máquina",
    "hielo cristalino truco",
    "coctel sin alcohol refrescante",
    "cerveza ipa qué significa",
    "vino tinto temperatura servicio",
)

NIÑOS_FAMILIA = (
    "manualidades rollos papel higiénico",
    "cuentos cortos leer niños 5 años",
    "juegos motricidad fina casa",
    "rutina sueño bebé orientativa",
    "chupete cuándo quitar consejos suaves",
    "parque infantil edades recomendadas",
    "pintura dedos receta casera segura",
    "masa modelar casera sin cocinar",
)

MASCOTAS_MAS = (
    "perro ansiedad separación señales",
    "gato esterilización recuperación",
    "pájaro jaula tamaño mínimo",
    "tortuga tierra hibernación",
    "erizo mascota legalidad país genérico",
)

PROGRAMACION_SUAVE = (
    "qué es html para principiantes",
    "css color hexadecimal tabla",
    "javascript variables let const simple",
    "python hola mundo explicación",
    "sql select from básico",
    "json qué es ejemplo",
    "markdown encabezados listas",
    "terminal cd ls básico windows",
    "encoding utf8 qué es",
    "bug vs error diferencia coloquial",
)

ECOLOGIA = (
    "huella carbono qué mide",
    "energías renovables tipos lista",
    "plástico un solo uso alternativas",
    "compostaje sin jardín bokashi",
    "papel reciclado proceso simple",
    "pesca sostenible etiquetas genéricas",
    "deforestación causas principales",
    "especies invasoras ejemplo",
    "arrecifes coral blanqueamiento",
    "oso polar hábitat cambio clima",
)

JARDIN_MAS = (
    "mulching qué es ventajas",
    "riego por goteo casero",
    "maceta drenaje capas",
    "tierra universal vs específica",
    "luz artificial plantas led full spectrum",
    "semillas caducidad cuánto duran",
    "trasplante primavera otoño cuándo",
    "hongos plantas hojas amarillas",
    "tutor tomate cómo atar",
    "invernadero casero plástico",
)

BELLEZA_CUIDADO = (
    "rutina facial noche orden productos",
    "exfoliante químico vs físico",
    "cepillo dientes eléctrico vs manual",
    "hilo dental uso correcto",
    "cortar uñas pies forma",
    "caspa champú ingredientes orientativos",
    "encías sangran cepillado causas",
    "protector labial fps importancia",
    "manicura francesa pasos",
    "tinte pelo canas raíces truco",
)

FOTOGRAFIA = (
    "regla tercios fotografía",
    "histograma foto qué es",
    "iso ruido explicación simple",
    "velocidad obturación congelar movimiento",
    "apertura diafragma profundidad campo",
    "lente gran angular vs teleobjetivo",
    "trípode altura peso cámara",
    "filtro polarizador para qué",
    "edición raw vs jpeg diferencia",
    "smartphone hdr modo noche",
)

CASA_INTELIGENTE = (
    "bombilla inteligente wifi setup genérico",
    "enchufe programable ahorro",
    "termostato inteligente compatibilidad genérica",
    "cerradura electrónica batería",
    "sensor movimiento luz pasillo",
    "asistente voz privacidad configuración",
    "cámara ip seguridad hogar consideraciones",
)

JUEGOS_DIGITALES = (
    "juegos cooperativos pc amigos",
    "configuración gráficos vs rendimiento",
    "latencia ping qué es",
    "servidor dedicado juego qué es",
    "crossplay qué significa",
    "dlc expansión diferencia",
    "early access riesgos compra",
    "speedrun qué es comunidad",
)

CINE_SERIES = (
    "subgéneros ciencia ficción lista",
    "diferencia precuela secuela",
    "oscars categorías principales",
    "anime studio ghibli películas conocidas",
    "documental naturaleza bbc style",
    "miniserie vs serie tradicional",
    "spoiler etiqueta redes qué es",
    "bandas sonoras icónicas años 80",
)

LIBROS_ESCRITURA = (
    "género narrativa vs ensayo",
    "sinopsis vs resumen diferencia",
    "personaje protagonista vs antagonista",
    "trama vs subtrama ejemplo",
    "edición libro autopublicación pasos genéricos",
    "lector ebook tinta electrónica ventajas",
    "audiolibro plataformas genéricas",
    "poesía métrica vs libre simple",
)

MUNDO_TRABAJO = (
    "carta presentación empleo estructura",
    "entrevista preguntas frecuentes respuesta",
    "negociación salarial tips neutros",
    "feedback constructivo ejemplo",
    "reunión 1 1 manager preparación",
    "onboarding empresa qué esperar genérico",
    "burnout señales organizacionales genéricas",
    "equilibrio vida trabajo límites",
)

COCHE_ELECTRICO = (
    "cargador wallbox potencia casa",
    "autonomía WLTP vs real explicación",
    "batería litio vida útil orientativa",
    "recarga rápida dc efecto batería",
    "frío autonomía eléctrico consejos",
    "app cargadores mapa genérico",
)

ALIMENTACION = (
    "dieta mediterránea pirámide simple",
    "superalimento marketing vs ciencia",
    "intolerancia lactosa síntomas",
    "gluten qué es celiaquía básico",
    "azúcares añadidos etiqueta leer",
    "ultraprocesados definición simple",
    "ayuno intermitente evidencia general",
    "hidratos simples complejos diferencia",
)

DEPORTE_MAS = (
    "electrolitos deporte cuando usar",
    "espinilla runner tratamiento",
    "fascitis plantar estiramientos",
    "doms agujetas cuánto duran",
    "proteína polvo tipos orientativos",
    "calorías quemadas bicicleta estimación",
    "ritmo carrera 5k principiante",
    "natación aleteo tobillos técnica",
)

_MUSICA_MAS_EXTRA = (
    "pentagrama notas básicas",
    "compás 4 4 explicación",
    "escala mayor menor diferencia oído",
    "metrónomo online practicar",
    "cuerdas guitarra nombres afinación estándar",
    "batería redoblante parche tipos",
)

MANUALIDADES_MAS = (
    "macramé cortina paso a paso simple",
    "velas molde silicona temperatura",
    "jabón glicerina base comprada",
    "tintes naturales tela cúrcuma",
    "decoupage servilleta tutorial",
)

CONSUMO = (
    "etiqueta energética electrodomésticos letras",
    "comparador precio unitario supermercado",
    "fecha consumo preferente vs caducidad",
    "envase reciclaje símbolos triángulo",
    "producto local km0 qué implica genérico",
    "segunda vida objetos ideas",
)

# Concatenar todas las categorías (sin duplicados, orden estable)
def _unique_preserve_order(items: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for s in items:
        t = s.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return tuple(out)


_ALL_PARTS = (
    _CLIMA_TIEMPO
    + _COCINA
    + _SALUD_BIENESTAR
    + _DEPORTE
    + _TECNOLOGIA
    + _HOGAR_BRICOLAJE
    + _VIAJES
    + _CULTURA_OCIO
    + _MUSICA_AUDIO
    + _NATURALEZA_CIENCIA
    + _HISTORIA_CURIOSIDADES
    + _AUTO_MOVILIDAD
    + _EDUCACION_PRODUCTIVIDAD
    + _FINANZAS_NEUTRO
    + _JARDIN_MASCOTAS
    + _MODA_CUIDADO
    + _ARTE_DIY
    + _IDIOMAS_REFERENCIA
    + _LOCAL_SERVICIOS
    + _ENTRETENIMIENTO_LIGERO
    + _VARIOS_LARGO
    + _GEOGRAFIA_GENERAL
    + _ASTRONOMIA
    + _COCINA_MAS
    + _BEBIDAS
    + NIÑOS_FAMILIA
    + MASCOTAS_MAS
    + PROGRAMACION_SUAVE
    + ECOLOGIA
    + JARDIN_MAS
    + BELLEZA_CUIDADO
    + FOTOGRAFIA
    + CASA_INTELIGENTE
    + JUEGOS_DIGITALES
    + CINE_SERIES
    + LIBROS_ESCRITURA
    + MUNDO_TRABAJO
    + COCHE_ELECTRICO
    + ALIMENTACION
    + DEPORTE_MAS
    + _MUSICA_MAS_EXTRA
    + MANUALIDADES_MAS
    + CONSUMO
)

WARMUP_SEARCH_QUERIES: tuple[str, ...] = _unique_preserve_order(_ALL_PARTS)
