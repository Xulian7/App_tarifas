import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import os
import json
from datetime import datetime
import pandas as pd
import tkinter.font as tkFont
from logica import *  # Importar todas las funciones de logica.py

# Función para cargar las opciones de cuentas disponibles en la DB
nequi_opciones = cargar_nequi_opciones()

# Crear ventana principal
ventana = tk.Tk()
ventana.title("Registro de Motos")
ventana.geometry("800x500")
icono_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'inicio.ico')
if os.path.exists(icono_path):
    ventana.iconbitmap(icono_path)
else:
    print("No se encontró el icono en la ruta especificada")

# Frame para el formulario y los botones
frame_superior = tk.Frame(ventana)
frame_superior.pack(fill="x", padx=10, pady=10)

# Definir el ancho común para todos los widgets
ancho_widget = 20  # Puedes ajustar este valor según tus necesidades

# Crear Frame para el formulario
frame_formulario = tk.Frame(frame_superior)
frame_formulario.grid(row=0, column=0, padx=5, pady=5, sticky="w")

# Campos del formulario organizados en filas
tk.Label(frame_formulario, text="Cédula:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_cedula = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_cedula.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entry_nombre = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Placa:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_placa = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_placa.grid(row=2, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Monto:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entry_monto = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_monto.grid(row=3, column=1, padx=5, pady=5, sticky="w")

tk.Label(frame_formulario, text="Referencia:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entry_referencia = tk.Entry(frame_formulario, width=ancho_widget, justify="center")
entry_referencia.grid(row=4, column=1, padx=5, pady=5, sticky="w")

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
tipos_opciones = ["Consignación", "Efectivo"]
combo_tipo = ttk.Combobox(frame_formulario, values=tipos_opciones, state="readonly", width=ancho_widget)
combo_tipo.grid(row=2, column=4, padx=5, pady=5, sticky="w")

# Combobox cargando las opciones de nequis.json
tk.Label(frame_formulario, text="Cuenta:").grid(row=3, column=3, padx=5, pady=5, sticky="e")
combo_nequi = ttk.Combobox(frame_formulario, values=nequi_opciones, state="disabled", width=ancho_widget)
combo_nequi.grid(row=3, column=4, padx=5, pady=5, sticky="w")

# Función para habilitar/deshabilitar el combo "Nequi" según el valor del combo "Tipo"
def actualizar_nequi(*args):
    if combo_tipo.get() == "Consignación":
        combo_nequi.config(state="normal")  # Habilitar el combo
    else:
        combo_nequi.config(state="disabled")  # Deshabilitar el combo
        combo_nequi.set("")  # Limpiar el contenido del combo
# Asociar el cambio en el combo "Tipo" a la función
combo_tipo.bind("<<ComboboxSelected>>", actualizar_nequi)

tk.Label(frame_formulario, text="Verificada:").grid(row=4, column=3, padx=5, pady=5, sticky="e")
verificada_opciones = ["", "Sí", "No"]
combo_verificada = ttk.Combobox(frame_formulario, values=verificada_opciones, state="readonly", width=ancho_widget)
combo_verificada.grid(row=4, column=4, padx=5, pady=5, sticky="w")

# Frame para los botones
frame_botones = tk.Frame(frame_superior)
frame_botones.grid(row=1, column=0, pady=10, sticky="w")
# Botones con el mismo ancho
btn_agregar = tk.Button(frame_botones, text="Registrar", width=ancho_widget)
btn_agregar.grid(row=0, column=0, padx=5, pady=10, sticky="ew")


btn_consultar = tk.Button(frame_botones, text="Consultar", width=ancho_widget, command=lambda: cargar_db(tree, entry_cedula, entry_nombre, entry_placa, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada))
btn_consultar.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

btn_limpiar = tk.Button(frame_botones, text="Limpiar", bg="red", fg="white", width=ancho_widget, command=lambda: limpiar_formulario(entry_cedula, entry_nombre, entry_placa, entry_monto, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada, tree))
btn_limpiar.grid(row=0, column=2, padx=5, pady=10, sticky="ew")

btn_cuentas = tk.Button(frame_botones, text="Cuentas", bg="green", fg="white", width=ancho_widget, command=abrir_ventana_cuentas)
btn_cuentas.grid(row=0, column=3, padx=5, pady=10, sticky="ew")




# Reservar espacio para la sección vacía
frame_vacio = tk.Frame(frame_superior, height=20)
frame_vacio.grid(row=2, column=0, pady=5)



# Treeview con scrollbar
tree_frame = tk.Frame(ventana)
tree_frame.pack(fill="both", expand=True)
scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
scroll_y.pack(side="right", fill="y")
tree = ttk.Treeview(tree_frame, columns=("Fecha_sistema", "Fecha_registro", "Cedula", "Nombre", "Placa", "Valor", "Tipo", "Nombre_cuenta", "Referencia", "Verificada"), show="headings", yscrollcommand=scroll_y.set)
scroll_y.config(command=tree.yview)
tree.tag_configure("rojo_bold", foreground="red", font=("Helvetica", 10, "bold"))
for col in tree["columns"]:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")
tree.pack(fill="both", expand=True)


ventana.mainloop()
