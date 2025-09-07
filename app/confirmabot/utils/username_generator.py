from faker import Faker

import random


def generate_custom_username():
    # Listas extensas de nombres y apellidos reales
    nombres = [
        "alex", "maria", "carlos", "ana", "david", "laura", "jose", "sofia", "miguel", "elena",
        "antonio", "carmen", "francisco", "isabel", "manuel", "patricia", "rafael", "monica", "juan", "cristina",
        "pedro", "beatriz", "luis", "rocio", "javier", "teresa", "fernando", "mercedes", "sergio", "angeles",
        "daniel", "dolores", "pablo", "concepcion", "alejandro", "pilar", "ruben", "rosario", "oscar", "cristina",
        "adrian", "francisca", "victor", "josefa", "alberto", "dolores", "enrique", "mercedes", "ignacio", "angeles",
        "james", "sarah", "michael", "jennifer", "robert", "linda", "william", "elizabeth", "richard", "barbara",
        "joseph", "susan", "thomas", "jessica", "christopher", "sarah", "charles", "karen", "daniel", "nancy",
        "matthew", "lisa", "anthony", "betty", "mark", "helen", "donald", "sandra", "steven", "donna",
        "paul", "carol", "andrew", "ruth", "joshua", "sharon", "kenneth", "michelle", "kevin", "laura",
        "brian", "sarah", "george", "kimberly", "edward", "deborah", "ronald", "dorothy", "timothy", "lisa",
        "jason", "nancy", "jeffrey", "karen", "ryan", "betty", "jacob", "helen", "gary", "sandra",
        "nicholas", "donna", "eric", "carol", "jonathan", "ruth", "stephen", "sharon", "larry", "michelle",
        "justin", "laura", "scott", "sarah", "brandon", "kimberly", "benjamin", "deborah", "samuel", "dorothy",
        "gregory", "lisa", "frank", "nancy", "raymond", "karen", "alexander", "betty", "patrick", "helen",
        "jack", "sandra", "dennis", "donna", "jerry", "carol", "tyler", "ruth", "aaron", "sharon",
        "jose", "michelle", "henry", "laura", "adam", "sarah", "douglas", "kimberly", "nathan", "deborah",
        "peter", "dorothy", "zachary", "lisa", "kyle", "nancy", "walter", "karen", "harold", "betty",
        "carl", "helen", "jeremy", "sandra", "arthur", "donna", "gerald", "carol", "lawrence", "ruth",
        "sean", "sharon", "christian", "michelle", "ethan", "laura", "austin", "sarah", "joe", "kimberly",
        "albert", "deborah", "jesse", "dorothy", "ernest", "lisa", "jonathan", "nancy", "terry", "karen",
        "roger", "betty", "keith", "helen", "harold", "sandra", "arthur", "donna", "gerald", "carol",
        "lawrence", "ruth", "sean", "sharon", "christian", "michelle", "ethan", "laura", "austin", "sarah"
    ]
    
    apellidos = [
        "garcia", "rodriguez", "gonzalez", "fernandez", "lopez", "martinez", "sanchez", "perez", "gomez", "martin",
        "jimenez", "ruiz", "diaz", "moreno", "alvarez", "romero", "alonso", "gutierrez", "navarro", "torres",
        "dominguez", "vazquez", "ramos", "gil", "ramirez", "serrano", "blanco", "munoz", "molina", "delgado",
        "castillo", "ortiz", "rubio", "marin", "sanz", "medina", "castro", "vargas", "herrera", "aguilar",
        "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez",
        "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
        "lee", "perez", "thompson", "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson",
        "walker", "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
        "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell", "carter", "roberts",
        "gomez", "phillips", "evans", "turner", "diaz", "parker", "cruz", "edwards", "collins", "reyes",
        "stewart", "morris", "morales", "murphy", "cook", "rogers", "gutierrez", "ortiz", "morgan", "cooper",
        "peterson", "bailey", "reed", "kelly", "howard", "ramos", "kim", "cox", "ward", "richardson",
        "watson", "brooks", "chavez", "wood", "james", "bennett", "gray", "mendoza", "ruiz", "hughes",
        "price", "alvarez", "castillo", "sanders", "patel", "myers", "long", "ross", "foster", "jimenez",
        "powell", "jenkins", "perry", "russell", "sullivan", "bell", "coleman", "butler", "henderson", "barnes",
        "gonzales", "fisher", "vasquez", "simmons", "romero", "jordan", "patterson", "alexander", "hamilton", "graham",
        "reynolds", "griffin", "wallace", "moreno", "west", "cole", "hayes", "bryant", "herrera", "gibson",
        "ellis", "tran", "medina", "aguilar", "stevens", "murray", "ford", "castro", "marshall", "owens",
        "harrison", "fernandez", "mcdonald", "woods", "washington", "kennedy", "wells", "vargas", "henry", "chen",
        "freeman", "webb", "tucker", "guzman", "burns", "crawford", "olson", "simpson", "porter", "hunter",
        "gordon", "mendez", "silva", "shaw", "rice", "hunt", "black", "daniels", "palmer", "mills",
        "nichols", "grant", "knight", "ferguson", "rose", "stone", "hawkins", "dunn", "perkins", "hudson",
        "spencer", "gardner", "stephens", "payne", "pierce", "berry", "matthews", "arnold", "wagner", "willis",
        "ray", "watkins", "olson", "carroll", "duncan", "snyder", "hart", "cunningham", "bradley", "lane",
        "andrews", "ruiz", "harper", "fox", "riley", "armstrong", "carpenter", "weaver", "greene", "lawrence",
        "elliott", "chavez", "sims", "austin", "peters", "kelley", "franklin", "lawson", "fields", "gutierrez"
    ]
    
    # Seleccionar nombre y apellido aleatorios
    nombre = random.choice(nombres)
    apellido = random.choice(apellidos)
    
    # Crear variaciones de mayúsculas y minúsculas
    variaciones_nombre = [
        nombre.lower(),  # todo minúsculas
        nombre.capitalize(),  # primera letra mayúscula
        nombre.upper(),  # todo mayúsculas
        ''.join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(nombre)]),  # alternado
        ''.join([c.upper() if i % 2 == 1 else c.lower() for i, c in enumerate(nombre)]),  # alternado inverso
        nombre[:1].upper() + nombre[1:].lower(),  # primera mayúscula, resto minúsculas
        nombre[:-1].lower() + nombre[-1:].upper(),  # última mayúscula, resto minúsculas
    ]
    
    variaciones_apellido = [
        apellido.lower(),  # todo minúsculas
        apellido.capitalize(),  # primera letra mayúscula
        apellido.upper(),  # todo mayúsculas
        ''.join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(apellido)]),  # alternado
        ''.join([c.upper() if i % 2 == 1 else c.lower() for i, c in enumerate(apellido)]),  # alternado inverso
        apellido[:1].upper() + apellido[1:].lower(),  # primera mayúscula, resto minúsculas
        apellido[:-1].lower() + apellido[-1:].upper(),  # última mayúscula, resto minúsculas
    ]
    
    # Seleccionar variaciones aleatorias
    nombre_final = random.choice(variaciones_nombre)
    apellido_final = random.choice(variaciones_apellido)
    
    # Combinar nombre y apellido (sin caracteres especiales)
    username = f"{nombre_final}{apellido_final}"
    
    # Agregar número aleatorio (opcional, 30% de probabilidad)
    if random.random() < 0.3:
        numero = random.randint(1, 999)
        username = f"{username}{numero}"
    
    return username