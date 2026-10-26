import os


def elegir_fichero(ruta_carpeta):
    """
    Dada la ruta a una carpeta, da las opciones de ficheros y devuelve el elegido.
    """

    ARCHIVOS =  ["ratings.csv", "diary.csv", "watched.csv"]

    disponibles = [ nombre for nombre in ARCHIVOS
    if os.path.isfile(os.path.join(ruta_carpeta, nombre))
    ]

    if not disponibles:
        raise ValueError(f"No se han encontrado {', '.join(ARCHIVOS)} en {ruta_carpeta}")

    print("Elige una opción:")
    for i, nombre in enumerate(disponibles):
        print(f"{i+1}. {nombre}")

    while True:
        eleccion = input()
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(disponibles):
            break
        print(f"Introduce un número entre 1 y {len(disponibles)}")

    fichero_elegido = os.path.join(ruta_carpeta, disponibles[int(eleccion) - 1])
    return fichero_elegido
    
