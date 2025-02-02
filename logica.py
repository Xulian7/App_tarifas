import pandas as pd
import tkinter.font as tkFont
from tkinter import messagebox
import tkinter as tk

def cargar_excel(archivo_excel, tree, entry_cedula, entry_nombre, entry_placa, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada):
    try:
        # Obtener los valores actuales de los Entry y Combobox
        cedula = entry_cedula.get()
        nombre = entry_nombre.get()
        placa = entry_placa.get()
        referencia = entry_referencia.get()
        fecha = entry_fecha.get()
        tipo = combo_tipo.get()
        nequi = combo_nequi.get()
        verificada = combo_verificada.get()

        # Leer el archivo Excel con pandas
        df = pd.read_excel(archivo_excel)

        # Limpiar el Treeview antes de agregar nuevos datos
        for row in tree.get_children():
            tree.delete(row)

        # Aplicar filtros basados en los valores de los Entry y Combobox
        if cedula:
            df = df[df['Cedula'].astype(str) == cedula]
        if nombre:
            df = df[df['Nombre'].str.contains(nombre, case=False, na=False)]
        if placa:
            df = df[df['Placa'].str.contains(placa, case=False, na=False)]
        if referencia:
            df = df[df['Referencia'].str.contains(referencia, case=False, na=False)]
        if fecha:
            df['Fecha_registro'] = pd.to_datetime(df['Fecha_registro'], errors='coerce')
            fecha_input = pd.to_datetime(fecha, errors='coerce')
            df = df[df['Fecha_registro'] == fecha_input]
        if tipo:
            df = df[df['Tipo'] == tipo]
        if nequi:
            df = df[df['Nombre_cuenta'] == nequi]
        if verificada:
            df = df[df['Verificada'] == verificada]

        # Asegurar el formato de las fechas en las columnas 'Fecha_sistema' y 'Fecha_registro'
        df['Fecha_sistema'] = pd.to_datetime(df['Fecha_sistema'], errors='coerce').dt.strftime('%d-%m-%Y')
        df['Fecha_registro'] = pd.to_datetime(df['Fecha_registro'], errors='coerce').dt.strftime('%d-%m-%Y')
        df = df.fillna("")  # Reemplazar NaN por cadena vacía

        # Configurar la etiqueta para sombrear
        tree.tag_configure("sombreado", background="lightpink")


        # Insertar las filas del DataFrame en el Treeview
        for index, row in df.iterrows():
            tags = ("sombreado",) if row["Verificada"] == "No" else ()
            tree.insert("", "end", values=row.tolist(), tags=tags)

        # Ajustar el ancho de las columnas según el contenido
        for col in tree["columns"]:
            max_width = max([tkFont.Font().measure(col)] + [tkFont.Font().measure(str(value)) for value in df[col].values])
            tree.column(col, width=max_width)  # Ajusta el ancho de la columna al contenido

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")
        
        
        
def limpiar_formulario(entry_cedula, entry_nombre, entry_placa, entry_monto, entry_referencia, entry_fecha,
combo_tipo, combo_nequi, combo_verificada, tree):
    # Limpiar campos de texto (Entry)
    entry_cedula.focus_set()
    entry_cedula.delete(0, tk.END)
    entry_nombre.delete(0, tk.END)
    entry_placa.delete(0, tk.END)
    entry_monto.delete(0, tk.END)
    entry_referencia.delete(0, tk.END)
    entry_fecha.delete(0, tk.END)
    
    # Limpiar los Combobox
    combo_tipo.set('')  # Resetear el ComboBox de Tipo
    combo_nequi.set('')  # Resetear el ComboBox de Nequi
    combo_verificada.set('')  # Resetear el ComboBox de Verificada
    
    # Limpiar Treeview
    for row in tree.get_children():
        tree.delete(row)
        
    # Colocar el enfoque en entry_cedula
    
    
    
