import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import os
import json
from datetime import datetime
import pandas as pd
import tkinter.font as tkFont
from PIL import Image, ImageTk
import subprocess
from logica import *  # Importar todas las funciones de logica.py




# Función para cargar las opciones de cuentas disponibles en la DB
nequi_opciones = cargar_nequi_opciones()
# Variable global para saber qué Entry se actualizó por último
ultimo_entry = None


# Crear ventana principal
ventana = tk.Tk()
ventana.title("Registro de Tarifas")
ventana.geometry("800x500")
icono_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'inicio.ico')
if os.path.exists(icono_path):
    ventana.iconbitmap(icono_path)
else:
    print("No se encontró el icono en la ruta especificada")

# Frame para el formulario y los botones
frame_superior = tk.Frame(ventana, bd=2, relief="groove", bg="#f0f0f0")
frame_superior.grid(row=0, column=0, sticky="ew", padx=10, pady=10) 
frame_superior.grid_columnconfigure(0, weight=1)  # Frame izquierdo (formulario y botones)
frame_superior.grid_columnconfigure(1, weight=1)  # Frame derecho (info)
# Frame izquierdo que contendrá formulario y botones
frame_izquierdo = tk.Frame(frame_superior)
frame_izquierdo.grid(row=0, column=0, sticky="nsew", padx=5)  # Agregar espacio
#frame_izquierdo.grid_rowconfigure(0, weight=1)
#frame_izquierdo.grid_rowconfigure(1, weight=1)
# Definir el ancho común para todos los widgets
ancho_widget = 20 # ajustar este valor según necesidades
# Crear Frame para el formulario
frame_formulario = tk.Frame(frame_izquierdo, bd=2, relief="solid")
frame_formulario.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

# Campos del formulario organizados en filas
tk.Label(frame_formulario, text="Cédula:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_cedula = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_cedula.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_nombre = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="w")

def actualizar_sugerencias(event):
    texto = entry_nombre.get()
    listbox_sugerencias.delete(0, tk.END)
    
    if not texto:
        listbox_sugerencias.grid_forget()  # Ocultar si no hay texto
        return

    # Conectar a la base de datos y obtener los resultados
    conn = sqlite3.connect("diccionarios/base_dat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM clientes WHERE nombre LIKE ? ORDER BY LENGTH(nombre) LIMIT 5", (texto + '%',))
    resultados = cursor.fetchall()
    conn.close()

    # Mostrar los resultados en el Listbox
    if resultados:
        for nombre in resultados:
            listbox_sugerencias.insert(tk.END, nombre[0])
        
        # Asegurarse de que el Listbox se coloque correctamente debajo del Entry
        listbox_sugerencias.grid(row=0, column=0, sticky="nsew")
        frame_sugerencias.grid_rowconfigure(0, weight=1)
        frame_sugerencias.grid_columnconfigure(0, weight=1)
        frame_sugerencias.grid()  # Asegura que el frame se muestre
    else:
        listbox_sugerencias.grid_forget()  # Ocultar si no hay resultados

entry_nombre.bind("<KeyRelease>", actualizar_sugerencias)

# Crear la función para seleccionar la sugerencia y actualizar los otros campos
def seleccionar_sugerencia(event):
    # Obtener la selección actual
    seleccion = listbox_sugerencias.curselection()
    
    if seleccion:
        # Obtener el valor del Listbox usando el índice seleccionado
        nombre_seleccionado = listbox_sugerencias.get(seleccion)
        
        # Actualizar el entry_nombre con la sugerencia seleccionada
        entry_nombre.delete(0, tk.END)
        entry_nombre.insert(0, nombre_seleccionado)

        # Buscar la cédula y la placa correspondientes al nombre seleccionado en la DB
        conn = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conn.cursor()

        cursor.execute("SELECT cedula, placa FROM clientes WHERE nombre = ?", (nombre_seleccionado,))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            cedula, placa = resultado
            # Rellenar los entry_cedula y entry_placa con los valores encontrados
            entry_cedula.delete(0, tk.END)
            entry_cedula.insert(0, cedula)
            
            entry_placa.delete(0, tk.END)
            entry_placa.insert(0, placa)
        
        # Ocultar el listbox_sugerencias después de seleccionar
        listbox_sugerencias.place_forget()

tk.Label(frame_formulario, text="Placa:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_placa = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_placa.grid(row=2, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Valor:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_monto = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_monto.grid(row=3, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Saldos:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_saldos = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_saldos.grid(row=4, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Referencia:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
entry_referencia = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_referencia.grid(row=5, column=1, padx=5, pady=5, sticky="w")

# Crea el frame para las sugerencias
frame_sugerencias = tk.Frame(frame_formulario, width=150, height=100)  # Ajusta según necesidad
frame_sugerencias.grid(row=0, column=2, rowspan=5, padx=5, pady=5, sticky="nsew")
# Crea el Listbox dentro del frame_sugerencias
listbox_sugerencias = tk.Listbox(frame_sugerencias, height=10, width=30, justify="center")  # Ajusta el width

listbox_sugerencias.grid(row=0, column=0, sticky="nsew")  # Usar grid() aquí en lugar de pack()
# Hacer que el frame_sugerencias pueda expandirse
frame_sugerencias.grid_rowconfigure(0, weight=1)  # Hace que el Listbox se expanda
frame_sugerencias.grid_columnconfigure(0, weight=1)  # Hace que el Listbox se expanda
# Vínculo para detectar selección
listbox_sugerencias.bind("<<ListboxSelect>>", seleccionar_sugerencia)
# Actualizar las sugerencias

fecha_actual = datetime.now().strftime('%d-%m-%Y')
tk.Label(frame_formulario, text="Fecha_sistema:").grid(row=0, column=3, padx=5, pady=5, sticky="e")
entry_hoy = tk.Entry(frame_formulario, width=ancho_widget, justify="center", font=("Helvetica", 10, "bold"))
entry_hoy.insert(0, fecha_actual) 
entry_hoy.config(state="disabled")
entry_hoy.grid(row=0, column=4, padx=5, pady=5, sticky="e")

tk.Label(frame_formulario, text="Fecha_registro:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
entry_fecha = DateEntry(
    frame_formulario,
    width=ancho_widget,
    background='darkblue',
    foreground='white',
    borderwidth=2,
    date_pattern='dd-MM-yyyy',  # Establecer el formato Día-Mes-Año
    locale='es_ES',  # Establecer la localidad a español para garantizar formato correcto
    textvariable=tk.StringVar()  # Para inicializar vacío
)
entry_fecha.configure(justify="center")
entry_fecha.grid(row=1, column=4, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Tipo:").grid(row=2, column=3, padx=5, pady=5, sticky="e")
tipos_opciones = ["Consignación", "Bancolombia", "Transf Nequi", "Transfiya", "PTM", "Efectivo", "Ajuste P/P"]
 
combo_tipo = ttk.Combobox(frame_formulario, values=tipos_opciones, state="readonly", width=ancho_widget)
combo_tipo.grid(row=2, column=4, padx=5, pady=5, sticky="w")

# Combobox cargando las opciones de nequis.json
tk.Label(frame_formulario, text="Cuenta:").grid(row=3, column=3, padx=5, pady=5, sticky="e")
combo_nequi = ttk.Combobox(frame_formulario, values=nequi_opciones, state="disabled", width=ancho_widget)
combo_nequi.grid(row=3, column=4, padx=5, pady=5, sticky="w")

# Función para habilitar/deshabilitar el combo "Nequi" según el valor del combo "Tipo"
def actualizar_nequi(*args):
    # Lista de opciones que deben deshabilitar el combo_nequi
    opciones_deshabilitadas = ["", "Efectivo", "Ajuste P/P"]

    if combo_tipo.get() in opciones_deshabilitadas:
        combo_nequi.config(state="disabled")  # Deshabilitar el combo
        combo_nequi.set("")  # Limpiar el contenido
    else:
        combo_nequi.config(state="normal")  # Habilitar el combo
# Asociar el cambio en el combo "Tipo" a la función
combo_tipo.bind("<<ComboboxSelected>>", actualizar_nequi)

tk.Label(frame_formulario, text="Verificada:").grid(row=4, column=3, padx=5, pady=5, sticky="e")
verificada_opciones = ["", "Si", "No"]
combo_verificada = ttk.Combobox(frame_formulario, values=verificada_opciones, state="readonly", width=ancho_widget)
combo_verificada.grid(row=4, column=4, padx=5, pady=5, sticky="w")

# Frame para los botones
# Función para cargar imágenes con tamaño uniforme
imagenes = {}
def cargar_imagen(nombre):
    img = Image.open(f"img/{nombre}.png")
    img = img.resize((20, 20), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)
    imagenes[nombre] = img_tk
    return img_tk

# Frame de los botones
frame_botones = tk.Frame(frame_izquierdo, bd=2, relief="solid")
frame_botones.grid(row=1, column=0, padx=5, pady=5, sticky="ew")  # Se expande en X
frame_botones.grid_columnconfigure(0, weight=1)
frame_botones.grid_columnconfigure(1, weight=1)
frame_botones.grid_columnconfigure(2, weight=1)

btn_agregar = tk.Button(frame_botones, text="    Registrar",image=cargar_imagen("Grabar"), compound="left", width=ancho_widget, command=lambda: agregar_registro(tree,entry_hoy, entry_cedula, entry_nombre, entry_placa, entry_monto, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada))
btn_agregar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

btn_consultar = tk.Button(frame_botones, text="  Consultar", image=cargar_imagen("Buscar"), compound="left", width=ancho_widget, command=lambda: cargar_db(tree, entry_cedula, entry_nombre, entry_placa, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada))
btn_consultar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

btn_limpiar = tk.Button(frame_botones, text="    Limpiar", image=cargar_imagen("Borrar"), compound="left", width=ancho_widget, command=lambda: limpiar_formulario(entry_cedula, entry_nombre, entry_placa, entry_monto, entry_saldos, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada, listbox_sugerencias, tree))
btn_limpiar.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

btn_cuentas = tk.Button(frame_botones, text="    Cuentas", image=cargar_imagen("Cuenta"), compound="left", width=ancho_widget, command=abrir_ventana_cuentas)
btn_cuentas.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

btn_clientes = tk.Button(frame_botones, text="   Clientes", image=cargar_imagen("Cliente"), compound="left", width=ancho_widget, command=abrir_ventana_clientes)
btn_clientes.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

btn_extracto = tk.Button(frame_botones, text="   Extracto", image=cargar_imagen("Extracto"), compound="left", width=ancho_widget, command=lambda: mostrar_registros(entry_nombre, entry_fecha))
btn_extracto.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

btn_export = tk.Button(frame_botones, text="   Exportar", image=cargar_imagen("Exportar"), compound="left" , command=join_and_export)
btn_export.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

btn_propietario = tk.Button(frame_botones, text=" Propietarios", image=cargar_imagen("llave"), compound="left" , command=ventana_propietario)
btn_propietario.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

btn_balance = tk.Button(frame_botones, text="   Balance dia", image=cargar_imagen("Balance"), compound="left" , command=arqueo)
btn_balance.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

# Frame de información (derecha)
frame_info = tk.Frame(frame_superior, height=20, bd=0, relief="solid")
frame_info.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
btn_mora = tk.Button(frame_info, text="DashBoard", image=cargar_imagen("Checklist"), compound="left" , command=ui_atrasos)
btn_mora.grid(row=0, column=0, padx=5, pady=5, sticky="ew")


# Frame para el Treeview
tree_frame = tk.Frame(ventana, bd=2, relief="ridge")
tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
# Scrollbar vertical
scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
# Treeview con sus columnas
tree = ttk.Treeview(tree_frame, columns=("id", "Fecha_sistema", "Fecha_registro", "Cedula", "Nombre", 
                                        "Placa","Color", "Valor", "Saldos", "Tipo", "Nombre_cuenta", "Referencia", "Verificada"), 
                    show="headings", yscrollcommand=scroll_y.set)
# Configurar la scrollbar para que funcione con el Treeview
scroll_y.config(command=tree.yview)
# Etiqueta para filas destacadas en rojo y en negrita
#tree.tag_configure("rojo_bold", foreground="red", font=("Helvetica", 10, "bold"))
# Configurar encabezados y alineación de columnas
for col in tree["columns"]:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")
# Ubicar elementos en la grilla
tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
# Configurar expansión para que se adapte correctamente
ventana.grid_rowconfigure(1, weight=1)
ventana.grid_columnconfigure(0, weight=1)
tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

def on_double_click(event, tree):
    # Obtener el item seleccionado
    selected_item = tree.selection()
    if not selected_item:
        return

    # Obtener los valores del item
    item_values = tree.item(selected_item, "values")
    if not item_values:
        return

    # Extraer los valores
    id_registro = item_values[0]  # ID está en la primera columna
    verificada = item_values[12]  # 'Verificada' está en la última columna

    # Verificar si el estado es "NO"
    if verificada.upper() == "NO":
        confirmar = messagebox.askyesno("Confirmación", "¿Desea marcar este registro como verificado?")
        if confirmar:
            try:
                # Conectar a la base de datos y actualizar el estado
                conn = sqlite3.connect("diccionarios/base_dat.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE registros SET Verificada = 'SI' WHERE id = ?", (id_registro,))
                conn.commit()
                conn.close()

                # Actualizar el Treeview
                new_values = list(item_values)
                new_values[12] = "SI"  # Cambiar el estado en la visualización
                tree.item(selected_item, values=new_values)

                messagebox.showinfo("Éxito", "Registro actualizado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el registro: {e}")

# Asociar el evento al Treeview
tree.bind("<Double-1>", lambda event: on_double_click(event, tree))

ventana.mainloop()


