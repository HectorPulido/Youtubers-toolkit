import os


def concat_ts_files(folder_path, output_file):
    """
    Recorre una carpeta y sus subcarpetas, concatenando el contenido
    de todos los archivos .ts en un único archivo de salida.

    Args:
        folder_path (str): Ruta de la carpeta raíz a recorrer.
        output_file (str): Ruta del archivo de salida.
    """
    with open(output_file, "w", encoding="utf-8") as outfile:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if "./.venv/" in file_path:
                        continue
                    if "ignore_" in file_path:
                        continue
                    if "__" in file_path:
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8") as infile:
                            outfile.write(
                                f"// File: {file_path}\n"
                            )  # Indica qué archivo estás incluyendo
                            outfile.write(infile.read())
                            outfile.write("\n\n")  # Espacio entre archivos
                            print(f"Archivo procesado: {file_path}")
                    except Exception as e:
                        print(f"Error al procesar {file_path}: {e}")


if __name__ == "__main__":
    # Cambia estos valores según tu entorno
    carpeta_origen = '.'
    archivo_salida = 'salida.txt'

    concat_ts_files(carpeta_origen, archivo_salida)
    print(f"Contenido concatenado en: {archivo_salida}")
