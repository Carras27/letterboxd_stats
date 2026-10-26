import os
import requests
import time
import json
import pandas as pd
import matplotlib.pyplot as plt

# Lista de ficheros de interés del export de Letterboxd.
ARCHIVOS =  ["ratings.csv", "diary.csv", "watched.csv"]

# API de TMDB (The Movie DataBase)
API = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {os.environ['TMDB_TOKEN']}"}

def elegir_fichero(ruta_carpeta: str, sep: str = ",") -> pd.DataFrame:
    """
    Dada la ruta a una carpeta, da las opciones de ficheros y devuelve el elegido.
    """

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

    # Guarda la ruta elegida.
    fichero_elegido = os.path.join(ruta_carpeta, disponibles[int(eleccion) - 1])

    # Obtiene el Dataframe a aprtir del fichero.
    df = pd.read_csv(fichero_elegido, sep=sep, encoding="utf-8")

    for columna in ("Name", "Year"):
        if columna not in df.columns:
            raise ValueError(f"El fichero {fichero_elegido} no tiene la columna '{columna}'")

    # Años no válidos pasan a NaN en lugar de romper el programa.
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    return df


def buscar_creditos(nombre: str, anio: int, n_actores: int = 7) -> dict:
    """
    Busca la película en TMDB y devuelve director(es) y los primeros actores.
    """
    vacio = {"Director": "", "Actores": ""}

    # Busca la película por título y año
    r = requests.get(
        f"{API}/search/movie",
        headers=HEADERS,
        params={"query": nombre, "year": anio},
        timeout=10,
    )
    r.raise_for_status()
    resultados = r.json()["results"]
    if not resultados:
        return vacio

    # Pide los créditos de la película
    r = requests.get(
        f"{API}/movie/{resultados[0]['id']}",
        headers=HEADERS,
        params={"append_to_response": "credits"},
        timeout=10,
    )
    r.raise_for_status()
    creditos = r.json()["credits"]

    directores = [p["name"] for p in creditos["crew"] if p["job"] == "Director"]
    actores = [p["name"] for p in creditos["cast"][:n_actores]]
    return {"Director": ", ".join(directores), "Actores": ", ".join(actores)}

def anadir_creditos(df: pd.DataFrame, ruta_cache: str = "creditos_cache.json") -> pd.DataFrame:
    """
    Añade las columnas Director y Actores, guardando lo ya consultado en un caché.
    """

    # Carga el fichero caché
    cache = {}
    if os.path.isfile(ruta_cache):
        with open(ruta_cache, encoding="utf-8") as f:
            cache = json.load(f)

    # Recorre las películas del Dataframe.
    filas = []
    for nombre, anio in zip(df["Name"], df["Year"]):
        clave = f"{nombre} ({anio})"
        if clave not in cache: # Si no está en caché, los busca en TMDB para añadirlo.
            try:
                cache[clave] = buscar_creditos(nombre, int(anio))
            except (requests.RequestException, ValueError):
                cache[clave] = {"Director": "", "Actores": ""}
            time.sleep(0.1)  # no saturar la API
        filas.append(cache[clave]) # Añade el resultado a la caché.

    # Guarda el nuevo resultado en caché.
    with open(ruta_cache, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # Une las nuevas columnas al Dataframe
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(filas)], axis=1)

def agrupar_por_anio(df: pd.DataFrame, agrupacion: str | None = None) -> pd.DataFrame:
    """
    Lee el csv indicado, agrupa las peliculas por año de salida
    y devuelve un DataFrame con el número de películas vistas por año.
    """
    
    if "Year" not in df.columns:
        raise ValueError("El DataFrame no tiene columna 'Year'")

    # Convierte a enteros y descarta posibles valores no válidos
    anios = pd.to_numeric(df["Year"], errors="coerce").dropna().astype(int)

    # Elegir el tipo de agrupación
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


def agrupar_por_director(df: pd.DataFrame, minimo: int = 3) -> pd.DataFrame:
    """
    Cuenta cuántas películas hay de cada director y muestra en un gráfico
    solo los que tienen más de `minimo` películas.
    """
    if "Director" not in df.columns:
        raise ValueError("Falta la columna 'Director'. Ejecuta antes anadir_creditos(df)")

    # Una película puede tener varios directores. Se separa y se cuenta a cada uno.
    directores = (
        df["Director"]
        .fillna("")
        .str.split(", ")
        .explode()
        .str.strip()
    )
    directores = directores[directores != ""]   # descarta las películas sin director

    conteo = directores.value_counts()
    conteo = conteo[conteo > minimo]            # solo los que superan el mínimo

    if conteo.empty:
        print(f"Ningún director tiene más de {minimo} películas")
        return pd.DataFrame(columns=["Director", "Películas"])

    resultado = conteo.rename_axis("Director").reset_index(name="Películas")

    # Gráfico de barras horizontales, el director con más películas arriba
    fig, ax = plt.subplots(figsize=(10, max(4, len(resultado) * 0.4)))
    barras = ax.barh(resultado["Director"], resultado["Películas"], color="#4C78A8")
    ax.invert_yaxis()
    ax.bar_label(barras, padding=3, fontsize=9)
    ax.set_xlabel("Número de películas")
    ax.set_title(f"Directores con más de {minimo} películas")
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.margins(x=0.08)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()

    return resultado