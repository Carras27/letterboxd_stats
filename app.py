import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from threading import RLock

import datos as dat

st.set_page_config(page_title="Letterboxd Dashboard", layout="wide")
st.title("🎬 Mi Letterboxd Dashboard")

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
    st.header("Datos")
    uploaded = st.file_uploader(
        "Sube ratings.csv, diary.csv o watched.csv",
        type=["csv"],
    )

    if uploaded is not None:
        df = pd.read_csv(uploaded, encoding="utf-8")
        if "Year" in df.columns:
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        st.session_state["df"] = df
        st.success(f"{len(df)} filas cargadas")

    if "df" in st.session_state:
        if st.button("Enriquecer con TMDB"):
            with st.spinner("Consultando TMDB..."):
                st.session_state["df_enriched"] = dat.anadir_detalles(
                    st.session_state["df"]
                )
            st.success("Datos enriquecidos")

    if st.button("Limpiar datos"):
        for k in ("df", "df_enriched"):
            st.session_state.pop(k, None)
        st.rerun()

# Cuerpo principal
if "df_enriched" not in st.session_state:
    st.info("Sube un CSV y pulsa 'Enriquecer con TMDB' para empezar.")
    st.stop()

df = st.session_state["df_enriched"]

tab_resumen, tab_periodo, tab_personas, tab_generos, tab_actividad = st.tabs(
    ["Resumen", "Año / Década", "Directores y Actores", "Géneros", "Actividad"]
)
# Resumen
with tab_resumen:
    col1, col2, col3 = st.columns(3)
    col1.metric("Películas", len(df))
    if "Rating" in df.columns:
        col2.metric("Rating medio", f"{df['Rating'].mean():.2f}")
    if "Duracion" in df.columns:
        col3.metric("Duración media", f"{df['Duracion'].mean():.0f} min")

    st.subheader("Vista previa")
    cols = [c for c in ["Name", "Year", "Rating", "Generos", "Director"]
            if c in df.columns]
    st.dataframe(df[cols].head(30), use_container_width=True)
# Año / Década
with tab_periodo:
    agrupacion = st.radio(
        "Agrupar por", ["Año", "Década"], horizontal=True, key="radio_anio"
    )
    modo = "anio" if agrupacion == "Año" else "decada"

    st.subheader("Películas por periodo")
    with st.spinner("Generando gráfico..."):
        mostrar_fig(dat.agrupar_por_anio(df, agrupacion=modo))

    if "Rating" in df.columns:
        st.subheader("Rating medio por periodo")
        usar_tmdb = st.checkbox("Comparar con TMDB", value=False)
        with st.spinner("Generando gráfico..."):
            mostrar_fig(dat.rating_por_anio(df, agrupacion=modo, usar_tmdb=usar_tmdb))
# Directores y Actores
with tab_personas:
    minimo = st.slider("Mínimo de películas por persona", 1, 15, 3)

    st.subheader("Directores")
    with st.spinner("Generando gráfico..."):
        mostrar_fig(dat.agrupar_por_director(df, minimo=minimo))

    st.subheader("Actores")
    with st.spinner("Generando gráfico..."):
        mostrar_fig(dat.agrupar_por_actor(df, minimo=minimo))
# Géneros
with tab_generos:
    if "Generos" not in df.columns:
        st.warning("Ejecuta primero 'Enriquecer con TMDB'.")
    else:
        top_n = st.slider("Top N géneros", 5, 20, 12)
        with st.spinner("Generando gráfico..."):
            mostrar_fig(dat.agrupar_por_genero(df, top_n=top_n))
# Actividad
with tab_actividad:
    if "Watched Date" not in df.columns:
        st.warning("Sube diary.csv para ver el heatmap de actividad.")
    else:
        anio = st.number_input(
            "Año (0 = el de más actividad)",
            min_value=0, max_value=2100, value=0, step=1,
        )
        anio_param = int(anio) if anio > 0 else None
        with st.spinner("Generando heatmap..."):
            mostrar_fig(dat.heatmap_actividad(df, anio=anio_param))