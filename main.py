from datos import elegir_fichero, anadir_creditos, agrupar_por_anio, agrupar_por_director, agrupar_por_actor
import pandas as pd

if __name__ == "__main__":
    df = elegir_fichero("carras")
    #agrupar_por_anio(df)
    df = anadir_creditos(df)
    #agrupar_por_director(df, 2)
    agrupar_por_actor(df, 3)