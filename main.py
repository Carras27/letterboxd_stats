import datos as dat
import pandas as pd

if __name__ == "__main__":
    df = dat.elegir_fichero("carras")
    #dat.agrupar_por_anio(df)
    df = dat.anadir_detalles(df)
    #print(df.columns)
    #dat.agrupar_por_director(df, 2)
    #dat.agrupar_por_actor(df, 3)
    #dat.agrupar_por_genero(df, 20)
    #dat.rating_por_anio(df)
    #dat.top_peliculas(df, 10 , False)
    dat.heatmap_actividad(df, 2026)