import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from threading import RLock

import datos as dat

st.set_page_config(page_title="Letterboxd Dashboard", layout="wide")

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
        "info_inicial": "Sube un CSV y pulsa 'Enriquecer con TMDB' para empezar.",
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
        "info_inicial": "Upload a CSV and click 'Enrich with TMDB' to start.",
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
        "info_inicial": "Igo CSV bat eta sakatu 'Aberastu TMDB-rekin' hasteko.",
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
    },
}

def t(clave: str, **kwargs) -> str:
    """Devuelve el texto en el idioma activo."""
    texto = TEXTOS[st.session_state["idioma"]][clave]
    return texto.format(**kwargs) if kwargs else texto


#  Idioma
if "idioma" not in st.session_state:
    st.session_state["idioma"] = "es"
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
    uploaded = st.file_uploader(t("subir_csv"), type=["csv"])


    if uploaded is not None:
        df = pd.read_csv(uploaded, encoding="utf-8")
        if "Year" in df.columns:
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        st.session_state["df"] = df
        st.success(t("cargadas", n=len(df)))

    if "df" in st.session_state:
        if st.button(t("enriquecer")):
            with st.spinner(t("enriqueciendo")):
                st.session_state["df_enriched"] = dat.anadir_detalles(
                    st.session_state["df"]
                )
            st.success(t("enriquecido"))

    if st.button(t("limpiar")):
        for k in ("df", "df_enriched"):
            st.session_state.pop(k, None)
        st.rerun()

# Cuerpo principal
if "df_enriched" not in st.session_state:
    st.info(t("info_inicial"))
    st.stop()

df = st.session_state["df_enriched"]

tab_resumen, tab_periodo, tab_personas, tab_generos, tab_actividad = st.tabs(
    [t("tab_resumen"), t("tab_periodo"), t("tab_personas"), t("tab_generos"), t("tab_actividad")]
)
# Resumen
with tab_resumen:
    col1, col2, col3 = st.columns(3)
    col1.metric(t("peliculas"), len(df))
    if "Rating" in df.columns:
        col2.metric(t("rating_medio"), f"{df['Rating'].mean():.2f}")
    if "Duracion" in df.columns:
        col3.metric(t("duracion_media"), f"{df['Duracion'].mean():.0f} min")

    st.subheader(t("vista_previa"))
    cols = [c for c in ["Name", "Year", "Rating", "Generos", "Director"]
            if c in df.columns]
    st.dataframe(df[cols].head(30), use_container_width=True)
# Año / Década
with tab_periodo:
    opciones = [t("anio"), t("decada")]
    eleccion = st.radio(t("agrupar_por"), opciones, horizontal=True, key="radio_anio")
    modo = "anio" if eleccion == t("anio") else "decada"

    st.subheader(t("peliculas_periodo"))
    with st.spinner(t("generando")):
        mostrar_fig(dat.agrupar_por_anio(df, agrupacion=modo))

    if "Rating" in df.columns:
        st.subheader(t("rating_periodo"))
        usar_tmdb = st.checkbox(t("comparar_tmdb"), value=False)
        with st.spinner(t("generando")):
            mostrar_fig(dat.rating_por_anio(df, agrupacion=modo, usar_tmdb=usar_tmdb))
# Directores y Actores
with tab_personas:
    minimo = st.slider(t("minimo"), 1, 15, 3)

    st.subheader(t("directores"))
    with st.spinner(t("generando")):
        mostrar_fig(dat.agrupar_por_director(df, minimo=minimo))

    st.subheader(t("actores"))
    with st.spinner(t("generando")):
        mostrar_fig(dat.agrupar_por_actor(df, minimo=minimo))
# Géneros
with tab_generos:
    if "Generos" not in df.columns:
        st.warning(t("aviso_enriquecer"))
    else:
        top_n = st.slider(t("top_generos"), 5, 20, 12)
        with st.spinner(t("generando")):
            mostrar_fig(dat.agrupar_por_genero(df, top_n=top_n))
# Actividad
with tab_actividad:
    if "Watched Date" not in df.columns:
        st.warning(t("aviso_diary"))
    else:
        anio = st.number_input(
            t("anio_heatmap"), min_value=0, max_value=2100, value=0, step=1
        )
        anio_param = int(anio) if anio > 0 else None
        with st.spinner(t("generando")):
            mostrar_fig(dat.heatmap_actividad(df, anio=anio_param))