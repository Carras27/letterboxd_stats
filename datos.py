import os


def elegir_fichero(ruta_carpeta):
    """
    Dada la ruta a una carpeta, da las opciones de ficheros y devuelve el elegido.
    """

    # Lista de ficheros de interés en la carpeta.
    ARCHIVOS =  ["ratings.csv", "diary.csv", "watched.csv"]

    # Guarda los encontrados en una lista.
    disponibles = [ nombre for nombre in ARCHIVOS
    if os.path.isfile(os.path.join(ruta_carpeta, nombre))
    ]

    # Si no encuentra ninguno de los ficheros se acaba la ejecución.
    if not disponibles:
        raise ValueError(f"No se han encontrado {', '.join(ARCHIVOS)} en {ruta_carpeta}")

    # Muestra al usuario las opciones de ficheros disponibles.
    print("Elige una opción:")
    for i, nombre in enumerate(disponibles):
        print(f"{i+1}. {nombre}")

    # El usuario indica por consola el fichero con el que quiere trabajar.
    while True:
        eleccion = input()
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(disponibles):
            break
        print(f"Introduce un número entre 1 y {len(disponibles)}")

    # Se devuelve el fichero elegido.
    fichero_elegido = os.path.join(ruta_carpeta, disponibles[int(eleccion) - 1])
    return fichero_elegido

def agrupar_por_anio(ruta_csv: str, ):
    """
    Agrupa los datos por año y devuelve un DataFrame con el número de películas vistas por año.
    """
    pass
    
