import os
import pandas as pd
import matplotlib.pyplot as plt

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

def agrupar_por_anio(ruta_csv: str, sep: str = ","):
    """
    Lee el csv indicado, agrupa las peliculas por año de salida
    y devuelve un DataFrame con el número de películas vistas por año.
    """

    # Convierte el fichero en un DataFrame de pandas.
    df = pd.read_csv(ruta_csv, encoding="utf-8")

    # Convierte a enteros y descarta posibles valores no válidos
    anios = pd.to_numeric(df["Year"], errors="coerce").dropna().astype(int)

    # Elegir el tipo de agrupación
    agrupacion = None
    if agrupacion is None:
        print("Agrupar por:")
        print("1. Años")
        print("2. Décadas")
        while True:
            eleccion = input("> ").strip()
            if eleccion in ("1", "2"):
                agrupacion = "anio" if eleccion == "1" else "decada"
                break
            print("Introduce 1 o 2")

    if agrupacion == "decada":
        claves = (anios // 10) * 10
        paso = 10
        etiqueta_x = "Década de Salida"
    elif agrupacion == "anio":
        claves = anios
        paso = 1
        etiqueta_x = "Año de salida"
    else:
        raise ValueError("agrupacion debe ser 'anio', 'decada' o None")

    # Cuenta y rellena con 0 los periodos sin películas
    conteo = claves.value_counts().sort_index()
    rango = range(conteo.index.min(), conteo.index.max() + 1, paso)
    conteo = conteo.reindex(rango, fill_value=0)

    resultado = conteo.rename_axis(etiqueta_x).reset_index(name="Películas")

   # Gráfico de barras
    n = len(conteo)
    posiciones = list(range(n))
    valores = conteo.values
    textos = [str(v) if v > 0 else "" for v in valores]  # no escribe los 0

    fig, ax = plt.subplots(figsize=(max(10, min(n * 0.25, 22)), 6))
    barras = ax.bar(posiciones, valores, color="#4C78A8")
    ax.bar_label(barras, labels=textos, padding=2, fontsize=7)

    # Etiquetas del eje X
    if agrupacion == "decada":
        marcas = posiciones                      # todas las décadas
        etiquetas = [f"{k}s" for k in conteo.index]
    else:
        # solo los años múltiplos de 5: 1990, 1995, 2000...
        marcas = [i for i, k in enumerate(conteo.index) if k % 5 == 0]
        etiquetas = [str(conteo.index[i]) for i in marcas]

    ax.set_xticks(marcas)
    ax.set_xticklabels(etiquetas, rotation=45, ha="right")
    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel("Número de películas")
    ax.set_title(f"Películas por {etiqueta_x.lower()}")
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.margins(y=0.08)                           # hueco para que no se corten los números
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()
    return resultado

    
