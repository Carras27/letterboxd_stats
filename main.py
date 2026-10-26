from datos import elegir_fichero, agrupar_por_anio 


if __name__ == "__main__":
    fichero = elegir_fichero("carras")
    agrupar_por_anio(fichero)