from datos import elegir_fichero, anadir_creditos, buscar_creditos, agrupar_por_anio, agrupar_por_director
import pandas as pd

if __name__ == "__main__":
    df = elegir_fichero("carras")
    #agrupar_por_anio(df)
    df = anadir_creditos(df)
    agrupar_por_director(df, 3)