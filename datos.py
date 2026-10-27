import os
import requests
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Lista de ficheros de interés del export de Letterboxd.
ARCHIVOS =  ["ratings.csv", "diary.csv", "watched.csv"]

# Etiquetas para los gráficos
ETIQUETAS = {
    "es": {
        "anio_salida": "Año de salida",
        "decada_salida": "Década de salida",
        "num_peliculas": "Número de películas",
        "peliculas_por": "Películas por {x}",
        "directores_mas_de": "Directores con más de {n} películas",
        "actores_mas_de": "Actores con más de {n} películas",
        "top_generos": "Top {n} géneros más vistos",
        "anio_estreno": "Año de estreno",
        "decada_estreno": "Década de estreno",
        "rating_medio": "Rating medio",
        "rating_por": "Rating medio por {x}",
        "tu_rating": "Tu rating medio",
        "media_tmdb": "Media TMDB",
        "actividad": "Actividad · {anio} ({n} películas)",
        "peliculas_dia": "Películas/día",
        "meses": ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"],
        "dias": ["L","X","V","S","D"],  # L, X(miércoles), V, S, D
        "sin_datos_director": "Ningún director tiene más de {n} películas",
        "sin_datos_actor": "Ningún actor tiene más de {n} películas",
    }
}

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

def buscar_data(nombre: str, anio: int, n_actores: int = 10) -> dict:
    """
    Busca la película en TMDB y devuelve director(es) y los primeros actores.
    """
    vacio = {"Director": "", "Actores": "",
             "Generos": "", "RatingTMDB": None,
             "Duracion": None, "IdiomaOriginal": "",}

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

    # Pide los créditos y detalles de la película 
    r = requests.get(
        f"{API}/movie/{resultados[0]['id']}",
        headers=HEADERS,
        params={"append_to_response": "credits"},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    creditos = r.json()["credits"]
    # Guarda los directores y algunos actores de la misma.
    directores = [p["name"] for p in creditos["crew"] if p["job"] == "Director"]
    actores = [p["name"] for p in creditos["cast"][:n_actores]]

    # Extrae los géneros de la película
    generos = ", ".join(g["name"] for g in data.get("genres", []))

    # Devuelve directores, actores, géneros, rating, duración e idioma.
    return {
        "Director": ", ".join(directores),
        "Actores": ", ".join(actores),
        "Generos": generos,
        "RatingTMDB": data.get("vote_average"),
        "Duracion": data.get("runtime"),
        "IdiomaOriginal": data.get("original_language", ""),
        }

def anadir_detalles(df: pd.DataFrame, ruta_cache: str = "creditos_cache.json") -> pd.DataFrame:
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
                cache[clave] = buscar_data(nombre, int(anio))
            except (requests.RequestException, ValueError):
                cache[clave] = {"Director": "", "Actores": "", "Generos": "",
                                "RatingTMDB": None, "Duracion": None, "IdiomaOriginal":""}
            time.sleep(0.1)  # no saturar la API
        filas.append(cache[clave]) # Añade el resultado a la caché.

    # Guarda el nuevo resultado en caché.
    with open(ruta_cache, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # Une las nuevas columnas al Dataframe
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(filas)], axis=1)

def agrupar_por_anio(df: pd.DataFrame, agrupacion = None, etq = None):
    """
    Lee el csv indicado, agrupa las peliculas por año de salida
    y devuelve un DataFrame con el número de películas vistas por año.
    """
    etq = etq or ETIQUETAS["es"]

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
        etiqueta_x = etq["decada_salida"]
    elif agrupacion == "anio":
        claves = anios
        paso = 1
        etiqueta_x = etq["anio_salida"]
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
    ax.set_ylabel(etq["num_peliculas"])
    ax.set_title(etq["peliculas_por"].format(x=etiqueta_x.lower()))
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.margins(y=0.08)                           # hueco para que no se corten los números
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()

    return fig, resultado

def agrupar_por_director(df: pd.DataFrame, minimo: int = 3, etq = None):
    """
    Cuenta cuántas películas hay de cada director y muestra en un gráfico
    solo los que tienen más de `minimo` películas.
    """
    etq = etq or ETIQUETAS["es"]

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
        print(etq["sin_datos_director"].format(n=minimo))
        return None, pd.DataFrame(columns=["Director", "Películas"])

    resultado = conteo.rename_axis("Director").reset_index(name="Películas")

    # Gráfico de barras horizontales, el director con más películas arriba
    fig, ax = plt.subplots(figsize=(10, max(4, len(resultado) * 0.4)))
    barras = ax.barh(resultado["Director"], resultado["Películas"], color="#4C78A8")
    ax.invert_yaxis()
    ax.bar_label(barras, padding=3, fontsize=9)
    ax.set_xlabel(etq["num_peliculas"])
    ax.set_title(etq["directores_mas_de"].format(n=minimo))
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.margins(x=0.08)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()

    return fig, resultado

def agrupar_por_actor(df: pd.DataFrame, minimo: int = 3, etq = None):
    """
    Cuenta cuántas películas hay de cada actor y muestra en un gráfico
    solo los que tienen más de `minimo` películas.
    """
    etq = etq or ETIQUETAS["es"]

    if "Actores" not in df.columns:
            raise ValueError("Falta la columna 'Actores'. Ejecuta antes anadir_creditos(df)")
    
    # Una película puede tener varios directores. Se separa y se cuenta a cada uno.
    actores = (
        df["Actores"]
        .fillna("")
        .str.split(", ")
        .explode()
        .str.strip()
    )
    actores = actores[actores != ""]   # descarta las películas sin actores
    
    conteo = actores.value_counts()
    conteo = conteo[conteo > minimo]            # solo los que superan el mínimo
    
    if conteo.empty:
        print(etq["sin_datos_actor"].format(n=minimo))
        return None, pd.DataFrame(columns=["Actores", "Películas"])
    
    resultado = conteo.rename_axis("Actores").reset_index(name="Películas")
    
    # Gráfico de barras horizontales, el actor con más películas arriba
    fig, ax = plt.subplots(figsize=(10, max(4, len(resultado) * 0.4)))
    barras = ax.barh(resultado["Actores"], resultado["Películas"], color="#4C78A8")
    ax.invert_yaxis()
    ax.bar_label(barras, padding=3, fontsize=9)
    ax.set_xlabel(etq["num_peliculas"])
    ax.set_title(etq["actores_mas_de"].format(n=minimo))
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.margins(x=0.08)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    return fig, resultado

def agrupar_por_genero(df: pd.DataFrame, top_n: int = 12, etq = None):
    """
    Cuenta cuantas películas hay de cada género y muestra un gráfico de barras con los resultados
    """
    etq = etq or ETIQUETAS["es"]

    if "Generos" not in df.columns:
        raise ValueError("Falta 'Generos'. Ejecuta antes anadir_detalles(df)")

    generos = (
        df["Generos"]
        .fillna("")
        .str.split(", ")
        .explode()
        .str.strip()
    )
    generos = generos[generos != ""]

    conteo = generos.value_counts().head(top_n)
    resultado = conteo.rename_axis("Genero").reset_index(name="Peliculas")

    fig, ax = plt.subplots(figsize=(10, max(4, len(resultado) * 0.45)))
    barras = ax.barh(resultado["Genero"], resultado["Peliculas"], color="#4C78A8")
    ax.invert_yaxis()
    ax.bar_label(barras, padding=3, fontsize=9)
    ax.set_xlabel(etq["num_peliculas"])
    ax.set_title(etq["top_generos"].format(n=top_n))
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.margins(x=0.08)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    plt.tight_layout()

    return fig, resultado

def rating_por_anio(df: pd.DataFrame, agrupacion = None, usar_tmdb: bool = False, etq = None):
    """
    Rating medio por año o por década de estreno.
    Si agrupacion es None, se pregunta por consola (1 = años, 2 = décadas).
    Si usar_tmdb=True añade la media de TMDB.
    """
    etq = etq or ETIQUETAS["es"]

    if "Rating" not in df.columns:
        raise ValueError("Falta columna 'Rating'. Usa ratings.csv")
    if "Year" not in df.columns:
        raise ValueError("Falta columna 'Year'.")

    # Elige agrupación (mismo patrón que agrupar_por_anio)
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
        etiqueta_x = etq["decada_estreno"]
        paso = 10
    elif agrupacion == "anio":
        etiqueta_x = etq["anio_estreno"]
        paso = 1
    else:
        raise ValueError("agrupacion debe ser 'anio', 'decada' o None")

    # Prepara datos
    datos = df.dropna(subset=["Year", "Rating"]).copy()
    if datos.empty:
        print("No hay ratings válidos para calcular la media.")
        return None, pd.DataFrame(columns=["Periodo", "RatingMedio"])
    datos["Year"] = pd.to_numeric(datos["Year"], errors="coerce")
    datos = datos.dropna(subset=["Year"])
    datos["Year"] = datos["Year"].astype(int)

    def clave_periodo(anios: pd.Series) -> pd.Series:
        return (anios // 10) * 10 if agrupacion == "decada" else anios

    datos["Periodo"] = clave_periodo(datos["Year"])

    # Media de tu rating por periodo
    serie = datos.groupby("Periodo")["Rating"].mean()

    # Media de TMDB por periodo (mismo criterio)
    serie_tmdb = None
    if usar_tmdb and "RatingTMDB" in datos.columns:
        sub = datos.dropna(subset=["RatingTMDB"])
        if not sub.empty:
            serie_tmdb = sub.groupby("Periodo")["RatingTMDB"].mean()

    # Rellena huecos (igual que agrupar_por_anio) 
    rango = range(serie.index.min(), serie.index.max() + 1, paso)
    serie = serie.reindex(rango)                 # NaN en periodos sin datos
    if serie_tmdb is not None:
        serie_tmdb = serie_tmdb.reindex(rango)

    # Gráfico
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(serie.index, serie.values, marker="o", markersize=4,
            linewidth=1.4, label=etq["tu_rating"], color="#4C78A8")

    if serie_tmdb is not None:
        ax.plot(serie_tmdb.index, serie_tmdb.values, marker="s", markersize=4,
                linewidth=1.2, label=etq["media_tmdb"], color="#F58518", alpha=0.85)

    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel(etq["rating_medio"])
    ax.set_title(etq["rating_por"].format(x=etiqueta_x.lower()))
    ax.legend()
    ax.grid(alpha=0.3)

    # Eje X: todos los puntos si son décadas; múltiplos de 5 si son años
    if agrupacion == "decada":
        ax.set_xticks(list(serie.index))
        ax.set_xticklabels([f"{k}s" for k in serie.index], rotation=45, ha="right")
    else:
        marcas = [k for k in serie.index if k % 5 == 0]
        ax.set_xticks(marcas)
        ax.set_xticklabels([str(k) for k in marcas], rotation=45, ha="right")

    plt.tight_layout()
    
    # Resultado
    resultado = pd.DataFrame({"Periodo": serie.index, "RatingMedio": serie.values})
    if serie_tmdb is not None:
        resultado["RatingTMDBMedio"] = serie_tmdb.values
    return fig, resultado

def top_peliculas(df, n=10, mejores=True):
    """
    Muestra las películas con mejor valoración por el usuario.
    """
    d = df.dropna(subset=["Rating", "Name"])
    d = d.sort_values("Rating", ascending=not mejores).head(n)
    print(d[["Name", "Year", "Rating", "Director"]].to_string(index=False))

def heatmap_actividad(df: pd.DataFrame, anio = None, columna_fecha: str = "Watched Date", etq = None):
    """
    Heatmap tipo GitHub con las películas vistas por día.
    - anio: si se indica, muestra solo ese año; si es None, muestra el año
            con más actividad (o el actual si hay datos).
    """
    etq = etq or ETIQUETAS["es"]

    if columna_fecha not in df.columns:
        raise ValueError(f"Falta la columna '{columna_fecha}'. "
                         f"¿Estás usando diary.csv?")

    fechas = pd.to_datetime(df[columna_fecha], errors="coerce").dropna()
    if fechas.empty:
        raise ValueError("No hay fechas válidas en el DataFrame.")

    # Conteo por día
    conteo = fechas.dt.normalize().value_counts().sort_index()
    conteo.index = pd.DatetimeIndex(conteo.index)

    # Año a mostrar
    if anio is None:
        # Año con más películas registradas
        anio = int(conteo.groupby(conteo.index.year).sum().idxmax())

    inicio = pd.Timestamp(f"{anio}-01-01")
    fin = pd.Timestamp(f"{anio}-12-31")

    # Serie completa del año (rellena con 0 los días sin películas)
    rango = pd.date_range(inicio, fin, freq="D")
    serie = conteo.reindex(rango, fill_value=0).astype(int)

    # Matriz para el heatmap: filas = día de la semana (L..D), columnas = semana del año
    # weekday(): lunes=0 ... domingo=6
    semana_anio = ((serie.index.dayofyear - 1) // 7).astype(int)
    dia_semana = serie.index.weekday

    n_semanas = semana_anio.max() + 1
    matriz = np.full((7, n_semanas), np.nan)
    for w, d, v in zip(semana_anio, dia_semana, serie.values):
        matriz[d, w] = v

    # Dibujo 
    fig, ax = plt.subplots(figsize=(max(10, n_semanas * 0.35), 3.2))

    # Colormap discreta: 0 = gris muy claro, 1..4 = azules crecientes, 5+ = azul fuerte
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(["#ebedf0", "#c6e2ff", "#7cb8f5", "#3b82d6", "#1f4e9c"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 4.5, np.inf], cmap.N)
    # Rejilla negra entre celdas
    ax.set_xticks(np.arange(-0.5, n_semanas, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 7, 1), minor=True)
    ax.grid(which="minor", color="black", linewidth=0.5)
    ax.tick_params(which="minor", length=0)

    # Reemplaza NaN por -1 para que no se pinten celdas inexistentes (feb 29, etc.)
    matriz_plot = np.where(np.isnan(matriz), 0, matriz)

    ax.imshow(matriz_plot, aspect="auto", cmap=cmap, norm=norm,
              interpolation="nearest")

    # Días: solo se etiquetan L, X, V, S, D (índices 0, 2, 4, 6)
    dias_etiqueta = [etq["dias"][0], "", etq["dias"][1], "",
                     etq["dias"][2], "", etq["dias"][3]]
    ax.set_yticks(range(7))
    ax.set_yticklabels(dias_etiqueta, fontsize=9)
    ax.set_ylabel("")

    # Etiquetas eje X: primera letra de cada mes, en su semana correspondiente
    meses_inicio = pd.date_range(inicio, fin, freq="MS")
    marcas_x = []
    etiquetas_x = []
    for m in meses_inicio:
        idx = (m - inicio).days
        semana = idx // 7
        if semana < n_semanas and (not marcas_x or semana != marcas_x[-1]):
            marcas_x.append(semana)
            etiquetas_x.append(etq["meses"][m.month - 1])

    ax.set_xticks(marcas_x)
    ax.set_xticklabels(etiquetas_x, fontsize=9)
    ax.set_xlabel("")
    ax.set_title(etq["actividad"].format(anio=anio, n=int(serie.sum())))
    ax.tick_params(length=0)

    # Sin grid ni spines para el look "GitHub"
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)

    # Leyenda manual
    leyenda_vals = [0, 1, 2, 3, 4, 5]
    leyenda_txt = ["0", "1", "2", "3-4", "5+"]
    fig.subplots_adjust(bottom=0.25)
    for i, (v, txt) in enumerate(zip(leyenda_vals[:5], leyenda_txt)):
        rect = plt.Rectangle((0.01 + i * 0.03, -0.18), 0.02, 0.06,
                             transform=fig.transFigure,
                             facecolor=cmap(norm(v)), edgecolor="none",
                             clip_on=False)
        fig.add_artist(rect)
        fig.text(0.033 + i * 0.03, -0.16, txt, fontsize=8, va="center")
    fig.text(0.005, -0.16, etq["peliculas_dia"] + ":", fontsize=8, va="center")

    plt.tight_layout()
    return fig