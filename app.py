import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from threading import RLock

import datos as dat

# Traducciones
TEXTOS = {
    "es": {
        "titulo": "🎬 Estadísticas Letterboxd",
        "sidebar_datos": "Datos",
        "subir_csv": "Sube ratings.csv, diary.csv o watched.csv",
        "cargadas": "{n} filas cargadas",
        "enriquecer": "Enriquecer con TMDB",
        "enriqueciendo": "Consultando TMDB...",
        "enriquecido": "Datos enriquecidos",
        "limpiar": "Limpiar datos",
        "info_inicial": "Sube un CSV para empezar.",
        "tab_resumen": "Resumen",
        "tab_periodo": "Año / Década",
        "tab_personas": "Directores y actores",
        "tab_generos": "Géneros",
        "tab_actividad": "Actividad",
        "peliculas": "Películas",
        "rating_medio": "Valoración media",
        "duracion_media": "Duración media",
        "vista_previa": "Vista previa",
        "agrupar_por": "Agrupar por",
        "anio": "Año",
        "decada": "Década",
        "peliculas_periodo": "Películas por periodo",
        "rating_periodo": "Valoración media por periodo",
        "comparar_tmdb": "Comparar con TMDB",
        "generando": "Generando gráfico...",
        "minimo": "Mínimo de películas por persona",
        "directores": "Directores",
        "actores": "Actores",
        "top_generos": "N géneros más vistos",
        "aviso_enriquecer": "Ejecuta primero 'Enriquecer con TMDB'.",
        "aviso_diary": "Sube diary.csv para ver el heatmap de actividad.",
        "anio_heatmap": "Año (0 = el de más actividad)",
        "idioma": "Idioma",
        "enlace_export": ("📥 **¿No tienes los CSV?**  \n"
        "Ve a https://letterboxd.com/user/exportdata/ "
        "y pulsa **Export Data**. Descargarás un ZIP con `ratings.csv`, "
        "`diary.csv` y `watched.csv`."),
        "cargando_tmdb": "Cargando datos y consultando TMDB...",
        
    },
    "en": {
        "titulo": "🎬 Letterboxd Statistics",
        "sidebar_datos": "Data",
        "subir_csv": "Upload ratings.csv, diary.csv or watched.csv",
        "cargadas": "{n} rows loaded",
        "enriquecer": "Enrich with TMDB",
        "enriqueciendo": "Querying TMDB...",
        "enriquecido": "Data enriched",
        "limpiar": "Clear data",
        "info_inicial": "Upload a CSV to start.",
        "tab_resumen": "Summary",
        "tab_periodo": "Year / Decade",
        "tab_personas": "Directors & actors",
        "tab_generos": "Genres",
        "tab_actividad": "Activity",
        "peliculas": "Movies",
        "rating_medio": "Average rating",
        "duracion_media": "Average runtime",
        "vista_previa": "Preview",
        "agrupar_por": "Group by",
        "anio": "Year",
        "decada": "Decade",
        "peliculas_periodo": "Movies per period",
        "rating_periodo": "Average rating per period",
        "comparar_tmdb": "Compare with TMDB",
        "generando": "Generating chart...",
        "minimo": "Minimum movies per person",
        "directores": "Directors",
        "actores": "Actors",
        "top_generos": "Top N genres",
        "aviso_enriquecer": "Run 'Enrich with TMDB' first.",
        "aviso_diary": "Upload diary.csv to see the activity heatmap.",
        "anio_heatmap": "Year (0 = most active one)",
        "idioma": "Language",
        "enlace_export": ("📥 **Don't have the CSVs?**  \n"
        "Go to https://letterboxd.com/user/exportdata/ "
        "and click **Export Data**. You'll get a ZIP with `ratings.csv`, "
        "`diary.csv` and `watched.csv`."),
        "cargando_tmdb": "Loading data and querying TMDB...",
    },
    "eu": {
        "titulo": "🎬 Letterboxd Estatistikak",
        "sidebar_datos": "Datuak",
        "subir_csv": "Igo ratings.csv, diary.csv edo watched.csv",
        "cargadas": "{n} errenkada kargatuta",
        "enriquecer": "Aberastu TMDB-rekin",
        "enriqueciendo": "TMDB kontsultatzen...",
        "enriquecido": "Datuak aberastuta",
        "limpiar": "Garbitu datuak",
        "info_inicial": "Igo CSV bat hasteko.",
        "tab_resumen": "Laburpena",
        "tab_periodo": "Urtea / Hamarkada",
        "tab_personas": "Zuzendariak eta aktoreak",
        "tab_generos": "Generoak",
        "tab_actividad": "Jarduera",
        "peliculas": "Filmak",
        "rating_medio": "Batez besteko balorazioa",
        "duracion_media": "Batez besteko iraupena",
        "vista_previa": "Aurrebista",
        "agrupar_por": "Taldekatu",
        "anio": "Urtea",
        "decada": "Hamarkada",
        "peliculas_periodo": "Filmak periodoko",
        "rating_periodo": "Batez besteko balorazioa periodoko",
        "comparar_tmdb": "Alderatu TMDB-rekin",
        "generando": "Grafikoa sortzen...",
        "minimo": "Gutxieneko filmak pertsonako",
        "directores": "Zuzendariak",
        "actores": "Aktoreak",
        "top_generos": "N genero ikusienak",
        "aviso_enriquecer": "Exekutatu lehenago 'Aberastu TMDB-rekin'.",
        "aviso_diary": "Igo diary.csv jarduera-mapa ikusteko.",
        "anio_heatmap": "Urtea (0 = jarduera handiena)",
        "idioma": "Hizkuntza",
        "enlace_export": ("📥 **Ez dituzu CSVak?**  \n"
        "Joan https://letterboxd.com/user/exportdata/ helbidera "
        "eta sakatu **Export Data**. ZIP bat deskargatuko duzu `ratings.csv`, "
        "`diary.csv` eta `watched.csv` fitxategiekin."),
        "cargando_tmdb": "Datuak kargatzen eta TMDB kontsultatzen...",
    },
}

# Traducciones para métodos en datos.py
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
    },
    "en": {
        "anio_salida": "Release year",
        "decada_salida": "Release decade",
        "num_peliculas": "Number of movies",
        "peliculas_por": "Movies per {x}",
        "directores_mas_de": "Directors with more than {n} movies",
        "actores_mas_de": "Actors with more than {n} movies",
        "top_generos": "Top {n} most watched genres",
        "anio_estreno": "Release year",
        "decada_estreno": "Release decade",
        "rating_medio": "Average rating",
        "rating_por": "Average rating per {x}",
        "tu_rating": "Your average rating",
        "media_tmdb": "TMDB average",
        "actividad": "Activity · {anio} ({n} movies)",
        "peliculas_dia": "Movies/day",
        "meses": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
        "dias": ["M","W","F","S","S"],
        "sin_datos_director": "No director has more than {n} movies",
        "sin_datos_actor": "No actor has more than {n} movies",
    },
    "eu": {
        "anio_salida": "Estreinaldi urte",
        "decada_salida": "Estreinaldi hamarkada",
        "num_peliculas": "Film kopurua",
        "peliculas_por": "Filmak {x}ko",
        "directores_mas_de": "{n} film baino gehiago dituzten zuzendariak",
        "actores_mas_de": "{n} film baino gehiago dituzten aktoreak",
        "top_generos": "Ikusi gabeko {n} genero nagusiak",
        "anio_estreno": "Estreinaldi urte",
        "decada_estreno": "Estreinaldi hamarkada",
        "rating_medio": "Batez besteko ratinga",
        "rating_por": "Batez besteko ratinga {x}ko",
        "tu_rating": "Zure batez besteko ratinga",
        "media_tmdb": "TMDB bataz bestekoa",
        "actividad": "Jarduera · {anio} ({n} film)",
        "peliculas_dia": "Filmak/egun",
        "meses": ["Urt","Ots","Mar","Api","Mai","Eka","Uzt","Abu","Ira","Urr","Aza","Abe"],
        "dias": ["A","A","O","L","I"],  # al, ar, og, lr, ig
        "sin_datos_director": "Zuzendaririk ez du {n} film baino gehiago",
        "sin_datos_actor": "Aktorerik ez du {n} film baino gehiago",
    },
}

# Inicializar la página
st.set_page_config(page_title="Letterboxd Dashboard", layout="wide")

#  Idioma
if "idioma" not in st.session_state:
    st.session_state["idioma"] = "es"

# FUnciones auxiliares
def t(clave: str, **kwargs) -> str:
    """Devuelve el texto en el idioma activo."""
    texto = TEXTOS[st.session_state["idioma"]][clave]
    return texto.format(**kwargs) if kwargs else texto

def etq():
    return ETIQUETAS[st.session_state["idioma"]]

# Título
st.title(t("titulo"))

def mostrar_fig(resultado):
    """Acepta fig o (fig, df) y lo pinta en Streamlit."""
    if isinstance(resultado, tuple):
        fig, _ = resultado
    else:
        fig = resultado
    st.pyplot(fig)
    plt.close(fig)

# Barra lateral
with st.sidebar:
    # Selector de idioma PRIMERO para que todo lo demás ya salga traducido
    idioma_actual = st.selectbox(
        "🌐 " + TEXTOS[st.session_state["idioma"]]["idioma"],
        options=["es", "en", "eu"],
        format_func=lambda x: {"es": "Español", "en": "English", "eu": "Euskara"}[x],
        index=["es", "en", "eu"].index(st.session_state["idioma"]),
    )
    if idioma_actual != st.session_state["idioma"]:
        st.session_state["idioma"] = idioma_actual
        st.rerun()  # recarga para traducir todo lo demás

    st.header(t("sidebar_datos"))

    st.markdown(t("enlace_export"))

    uploaded = st.file_uploader(t("subir_csv"), type=["csv"])


    if uploaded is not None:
        nombre = uploaded.name.lower()
        clave_df = ("df_ratings" if "ratings" in nombre
                else "df_diary" if "diary" in nombre
                else "df_watched" if "watched" in nombre
                else None)

        if clave_df is None:
            st.error("Nombre de fichero no reconocido.")
        elif clave_df not in st.session_state:
            df = pd.read_csv(uploaded, encoding="utf-8")
            if "Year" in df.columns:
                df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

            with st.spinner(t("cargando_tmdb")):
                df = dat.anadir_detalles(df)

            st.session_state[clave_df] = df
            st.success(t("cargadas", n=len(df)))

    if st.button(t("limpiar")):
        for k in ("df_ratings", "df_diary", "df_watched"):
            st.session_state.pop(k, None)
        st.rerun()

# Cuerpo principal
df_principal = None
for clave in ("df_ratings", "df_diary", "df_watched"):
    if clave in st.session_state:
        df_principal = st.session_state[clave]
        break

tab_resumen, tab_periodo, tab_personas, tab_generos, tab_actividad = st.tabs(
    [t("tab_resumen"), t("tab_periodo"), t("tab_personas"), t("tab_generos"), t("tab_actividad")]
)
# Resumen
with tab_resumen:
    if df_principal is None:
        st.warning(t("info_inicial"))
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric(t("peliculas"), len(df_principal))
        if "Rating" in df_principal.columns:
            col2.metric(t("rating_medio"), f"{df_principal['Rating'].mean():.2f}")
        if "Duracion" in df_principal.columns:
            col3.metric(t("duracion_media"), f"{df_principal['Duracion'].mean():.0f} min")
        st.subheader(t("vista_previa"))
        cols = [c for c in ["Name", "Year", "Rating", "Generos", "Director"]
                if c in df_principal.columns]
        st.dataframe(df_principal[cols].head(30), use_container_width=True)
# Año / Década
with tab_periodo:
    if df_principal is None:
        st.warning(t("info_inicial"))
    else:
        opciones = [t("anio"), t("decada")]
        eleccion = st.radio(t("agrupar_por"), opciones,
                            horizontal=True, key="radio_anio")
        modo = "anio" if eleccion == t("anio") else "decada"

        st.subheader(t("peliculas_periodo"))
        with st.spinner(t("generando")):
            mostrar_fig(dat.agrupar_por_anio(df_principal, agrupacion=modo, etq=etq()))

        if "Rating" in df_principal.columns:
            st.subheader(t("rating_periodo"))
            usar_tmdb = st.checkbox(t("comparar_tmdb"), value=False)
            with st.spinner(t("generando")):
                mostrar_fig(dat.rating_por_anio(df_principal, agrupacion=modo, usar_tmdb=usar_tmdb, etq=etq()))
# Directores y Actores
with tab_personas:
    if df_principal is None:
        st.warning(t("info_inicial"))
    else:
        minimo = st.slider(t("minimo"), 1, 15, 3)

        st.subheader(t("directores"))
        with st.spinner(t("generando")):
            mostrar_fig(dat.agrupar_por_director(df_principal, minimo=minimo, etq=etq()))

        st.subheader(t("actores"))
        with st.spinner(t("generando")):
            mostrar_fig(dat.agrupar_por_actor(df_principal, minimo=minimo, etq=etq()))
# Géneros
with tab_generos:
    if df_principal is None or "Generos" not in df_principal.columns:
        st.warning(t("info_inicial"))
    else:
        top_n = st.slider(t("top_generos"), 5, 20, 12)
        with st.spinner(t("generando")):
            mostrar_fig(dat.agrupar_por_genero(df_principal, top_n=top_n, etq=etq()))
# Actividad
with tab_actividad:
    df_fechas = None
    for clave in ("df_diary", "df_watched"):
        if clave in st.session_state and "Watched Date" in st.session_state[clave].columns:
            df_fechas = st.session_state[clave]
            break

    if df_fechas is None:
        st.warning(t("aviso_diary"))
    else:
        anio = st.number_input(t("anio_heatmap"), min_value=0, max_value=2100, value=0, step=1)
        with st.spinner(t("generando")):
            mostrar_fig(dat.heatmap_actividad(df_fechas,anio=int(anio) or None, etq=etq()))