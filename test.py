import pandas as pd
import tkinter as tk
from tkinter import filedialog

from datetime import datetime, timedelta

# Función para convertir fechas de texto a objetos datetime
def convertir_fecha(fecha_str):
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d")
    except ValueError:
        return None

# Crear ventana oculta de Tkinter
root = tk.Tk()
root.withdraw()

# Abrir diálogo para seleccionar archivo
file_path = filedialog.askopenfilename(title="Selecciona un archivo Excel", filetypes=[("Archivos Excel", "*.xlsx *.xls")])

if file_path:
    # Cargar las hojas "clientes" y "registros"
    xls = pd.ExcelFile(file_path)
    df_clientes = pd.read_excel(xls, sheet_name="clientes")
    df_registros = pd.read_excel(xls, sheet_name="registros")

    # Lista para almacenar los nuevos registros
    nuevos_registros = []

    # Iterar sobre los clientes únicos
    for _, row in df_clientes.iterrows():
        cedula = row["Cedula"]
        fecha_inicio = convertir_fecha(str(row["Fecha_inicio"]))
        placa = row["Placa"]
        valor_cuota = row["Valor_cuota"]

        # Verificar si la fecha es válida y anterior a 2025-01-01
        if fecha_inicio and fecha_inicio < datetime(2025, 1, 1):
            fecha_actual = fecha_inicio
            while fecha_actual <= datetime(2024, 12, 31):
                nuevos_registros.append({
                    "Cedula": cedula,
                    "Fecha_registro": fecha_actual.strftime("%Y-%m-%d"),
                    "Placa": placa,
                    "Valor": valor_cuota
                })
                fecha_actual += timedelta(days=1)

    # Convertir a DataFrame y agregar a df_registros
    df_nuevos_registros = pd.DataFrame(nuevos_registros)
    df_registros = pd.concat([df_registros, df_nuevos_registros], ignore_index=True)

    # Guardar en el mismo archivo
    with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_registros.to_excel(writer, sheet_name="registros", index=False)

    print(f"Se agregaron {len(nuevos_registros)} registros a la hoja 'registros'.")
else:
    print("No se seleccionó ningún archivo.")
