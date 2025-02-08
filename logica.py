import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import os
from datetime import datetime
import pandas as pd
from tkcalendar import DateEntry

def cargar_db(tree, entry_cedula, entry_nombre, entry_placa, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada):
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

        # Conectar a la base de datos SQLite
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()

        # Construir la consulta SQL con filtros
        query = "SELECT id, Fecha_sistema, Fecha_registro, Cedula, Nombre, Placa, Valor, Tipo, Nombre_cuenta, Referencia, Verificada FROM registros WHERE 1=1"

        params = []
        
        if cedula:
            query += " AND Cedula = ?"
            params.append(cedula)
        if nombre:
            query += " AND Nombre LIKE ?"
            params.append(f"%{nombre}%")
        if placa:
            query += " AND Placa LIKE ?"
            params.append(f"%{placa}%")
        if referencia:
            query += " AND Referencia LIKE ?"
            params.append(f"%{referencia}%")
        if fecha:
            query += " AND Fecha_registro = ?"
            params.append(fecha)
        if tipo:
            query += " AND Tipo = ?"
            params.append(tipo)
        if nequi:
            query += " AND Nombre_cuenta = ?"
            params.append(nequi)
        if verificada:
            query += " AND Verificada = ?"
            params.append(verificada)

        # Ejecutar la consulta con los parámetros
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Cerrar la conexión
        conn.close()

        # Limpiar el Treeview antes de agregar nuevos datos
        for row in tree.get_children():
            tree.delete(row)

        # Configurar la etiqueta para sombrear
        tree.tag_configure("sombreado", background="lightpink")

        # Ordenar los datos por 'Cedula'
        rows.sort(key=lambda x: str(x[3]))  # Ordena por el valor de la columna Cedula (índice 3, ya que id ahora está en 0)

        # Insertar las filas en el Treeview
        for row in rows:
            # Formatear las fechas correctamente
            fecha_sistema = pd.to_datetime(row[1]).strftime('%d-%m-%Y')
            fecha_registro = pd.to_datetime(row[2]).strftime('%d-%m-%Y')

            # Crear una lista con los valores modificados
            values = list(row)
            values[1] = fecha_sistema
            values[2] = fecha_registro

            # Aplicar sombreado si "Verificada" es "No"
            tags = ("sombreado",) if row[10] == "No" else ()
            tree.insert("", "end", values=values, tags=tags)

        # Ajustar el ancho de las columnas según el contenido
        for col in tree["columns"]:
            max_width = max([tkFont.Font().measure(col)] + [tkFont.Font().measure(str(value)) for value in rows])
            tree.column(col, width=max_width)  # Ajusta el ancho de la columna al contenido

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar los datos desde la base de datos: {e}")

def limpiar_formulario(entry_cedula, entry_nombre, entry_placa, entry_monto, entry_referencia, entry_fecha,
combo_tipo, combo_nequi, combo_verificada, listbox_sugerencias, tree):
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
    listbox_sugerencias.grid_forget()
    
    # Limpiar Treeview
    for row in tree.get_children():
        tree.delete(row)
        
    # Colocar el enfoque en entry_cedula

def abrir_ventana_cuentas():
    # Crear ventana
    ventana_cuentas = tk.Toplevel()
    ventana_cuentas.title("Gestión de Cuentas")
    ventana_cuentas.geometry("600x400")
    
    # Establecer un icono (si existe)
    icono_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'inicio.ico')
    if os.path.exists(icono_path):
        ventana_cuentas.iconbitmap(icono_path)

    # Estilo para los botones y labels
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10), padding=5)
    style.configure("TLabel", font=("Arial", 10))
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    # Frame superior para la tabla
    frame_tabla = ttk.Frame(ventana_cuentas)
    frame_tabla.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    # Crear Treeview con scrollbar
    columnas = ("ID", "Titular", "Entidad")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    
    # Scrollbar vertical
    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    
    # Configuración de columnas
    for col in columnas:
        tree.heading(col, text=col, anchor="center")
        tree.column(col, anchor="center", width=150 if col == "Entidad" else 100)
    
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Frame medio para formularios
    frame_formulario = ttk.Frame(ventana_cuentas, padding=10)
    frame_formulario.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew")

    label_titular = ttk.Label(frame_formulario, text="Titular:")
    label_titular.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    entry_titular = ttk.Entry(frame_formulario, width=30)
    entry_titular.grid(row=0, column=1, padx=5, pady=5)

    label_entidad = ttk.Label(frame_formulario, text="Entidad:")
    label_entidad.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    entry_entidad = ttk.Entry(frame_formulario, width=30)
    entry_entidad.grid(row=1, column=1, padx=5, pady=5)

    # Función para crear una nueva cuenta
    def crear_cuenta():
        titular_valor = entry_titular.get()
        entidad_valor = entry_entidad.get()

        if not titular_valor or not entidad_valor:
            messagebox.showwarning("Advertencia", "Todos los campos deben ser completados")
            return

        try:
            conn = sqlite3.connect('diccionarios/base_dat.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cuentas (Titular, Entidad) VALUES (?, ?)", (titular_valor, entidad_valor))
            conn.commit()
            conn.close()

            # Insertar en Treeview y limpiar entradas
            tree.insert("", "end", values=(cursor.lastrowid, titular_valor, entidad_valor))
            entry_titular.delete(0, tk.END)
            entry_entidad.delete(0, tk.END)

            messagebox.showinfo("Éxito", "Cuenta creada exitosamente")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la cuenta: {e}")

    # Función para eliminar una cuenta
    def eliminar_cuenta():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un registro para eliminar.")
            return

        item_values = tree.item(selected_item)["values"]
        id_cuenta = item_values[0]

        confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar cuenta ID {id_cuenta}?")
        if confirmacion:
            try:
                conn = sqlite3.connect('diccionarios/base_dat.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cuentas WHERE ID = ?", (id_cuenta,))
                conn.commit()
                conn.close()

                tree.delete(selected_item)
                messagebox.showinfo("Éxito", f"Cuenta ID {id_cuenta} eliminada.")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    # Frame inferior para botones
    frame_botones = ttk.Frame(ventana_cuentas)
    frame_botones.grid(row=2, column=0, columnspan=3, pady=10)

    btn_crear = ttk.Button(frame_botones, text="Crear Cuenta", command=crear_cuenta)
    btn_crear.grid(row=0, column=0, padx=10, pady=5)

    btn_eliminar = ttk.Button(frame_botones, text="Eliminar Cuenta", command=eliminar_cuenta)
    btn_eliminar.grid(row=0, column=1, padx=10, pady=5)

    # Cargar datos desde la base de datos
    try:
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()
        cursor.execute("SELECT ID, Titular, Entidad FROM cuentas")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            tree.insert("", "end", values=row)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar los datos: {e}")

    # Expandir columnas
    ventana_cuentas.columnconfigure(0, weight=1)
    ventana_cuentas.rowconfigure(0, weight=1)

def obtener_datos_clientes():
    """Obtiene los datos de la tabla clientes desde la base de datos y formatea Capital y Fecha_inicio."""
    conexion = sqlite3.connect("diccionarios/base_dat.db")  # Cambia el nombre si es diferente
    cursor = conexion.cursor()
    
    query = "SELECT Cedula, Nombre, Telefono, Direccion, Placa, Fecha_inicio, Fecha_final, Tipo_contrato, Capital, Valor_cuota FROM clientes"
    cursor.execute(query)
    datos = cursor.fetchall()
    
    conexion.close()

    # Formatear los datos
    datos_formateados = []
    for fila in datos:
        cedula, nombre, telefono, direccion, placa, fecha_inicio, fecha_final, tipo_contrato, capital, valor_cuota = fila
        
        # Formatear la fecha si existe
        if fecha_inicio:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                fecha_inicio = "Formato Inválido"  # En caso de error con la fecha
        
        # Formatear capital sin decimales
        capital = int(capital) if capital is not None else 0
        
        datos_formateados.append((cedula, nombre, telefono, direccion, placa, fecha_inicio, fecha_final, tipo_contrato, capital, valor_cuota))

    return datos_formateados

def ajustar_columnas(tree):
    """Ajusta automáticamente el ancho de las columnas en función del contenido."""
    for col in tree["columns"]:
        tree.column(col, anchor="center")  # Justificar contenido al centro
        max_len = len(col)  # Inicia con el ancho del encabezado
        for item in tree.get_children():
            text = str(tree.item(item, "values")[tree["columns"].index(col)])
            max_len = max(max_len, len(text))
        tree.column(col, width=max_len * 10)  # Ajusta el ancho en función del contenido

def abrir_ventana_clientes():
    ventana_clientes = tk.Toplevel()
    ventana_clientes.title("Clientes")
    ventana_clientes.geometry("900x600")

    # Crear un Frame para contener el Treeview y la Scrollbar
    frame_tree = ttk.Frame(ventana_clientes)
    frame_tree.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

    # Crear el Treeview dentro del Frame
    columnas = ("Cédula", "Nombre", "Teléfono", "Dirección", 
                "Placa", "Fecha Inicio", "Fecha_final", "Tipo Contrato", 
                "Capital", "Valor Cuota")

    tree = ttk.Treeview(frame_tree, columns=columnas, show="headings")

    # Configurar encabezados y justificar contenido al centro
    for col in columnas:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    # Crear Scrollbar dentro del Frame
    scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Ubicar Treeview y Scrollbar con grid dentro del Frame
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Configurar expansión del Frame
    frame_tree.columnconfigure(0, weight=1)
    frame_tree.rowconfigure(0, weight=1)

    # Llenar el Treeview con datos de la base de datos (función placeholder)
    # for fila in obtener_datos_clientes():
    #     tree.insert("", "end", values=fila)
    # Llenar el Treeview con datos de la base de datos
    for fila in obtener_datos_clientes():
        tree.insert("", "end", values=fila)
    # Ajustar automáticamente el ancho de las columnas después de insertar los datos
    ajustar_columnas(tree)

            # Función para configurar correctamente los DateEntry
    def create_date_entry(parent):
        return DateEntry(parent, width=27, background='darkblue', 
                        foreground='white', borderwidth=2, 
                        date_pattern='dd-MM-yyyy',  # Establecer el formato Día-Mes-Año
                        locale='es_ES')
    # Frame para los Labels y Entries
    frame_form = ttk.LabelFrame(ventana_clientes, text="Información del Cliente")
    frame_form.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
    # Etiquetas y entradas
    labels_texts = ["Cédula:", "Nombre:", "Teléfono:", "Dirección:", 
                    "Placa:", "Fecha Inicio:", "Fecha final:", "Tipo Contrato:", 
                    "Capital:", "Valor Cuota:"]
    entries = {}

    for i, text in enumerate(labels_texts):
        lbl = ttk.Label(frame_form, text=text)
        lbl.grid(row=i//2, column=(i%2)*2, padx=5, pady=5, sticky="e")
        
        if "Fecha" in text:  # Usar DateEntry solo para fechas
            entry = create_date_entry(frame_form)
        else:  # Si no, usar Entry normal
            entry = ttk.Entry(frame_form, width=30)
        
        entry.grid(row=i//2, column=(i%2)*2+1, padx=5, pady=5, sticky="w")
        entries[text] = entry  # Guardamos las entradas en un diccionario
    
    

    # Frame para los botones
    frame_buttons = ttk.Frame(ventana_clientes)
    frame_buttons.grid(row=2, column=0, columnspan=4, pady=10)

    # Botones Crear, Modificar, Inhabilitar
    btn_crear = ttk.Button(frame_buttons, text="Crear", command=lambda: print("Función Crear"))
    btn_crear.grid(row=0, column=0, padx=10)

    btn_modificar = ttk.Button(frame_buttons, text="Modificar", command=lambda: print("Función Modificar"))
    btn_modificar.grid(row=0, column=1, padx=10)

    btn_inhabilitar = ttk.Button(frame_buttons, text="Inhabilitar", command=lambda: print("Función Inhabilitar"))
    btn_inhabilitar.grid(row=0, column=2, padx=10)

    # Expansión de filas y columnas
    ventana_clientes.columnconfigure(0, weight=1)
    ventana_clientes.rowconfigure(0, weight=1)

    return ventana_clientes  # Si quieres capturar la ventana creada

def cargar_nequi_opciones():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()

        # Obtener las columnas 'Entidad' y 'Titular' de la tabla 'Cuentas'
        cursor.execute("SELECT Entidad, Titular FROM cuentas")
        rows = cursor.fetchall()

        # Crear la lista con la concatenación 'Entidad - Titular'
        nequi_opciones = [f"{row[0]} {row[1]}" for row in rows]

        # Cerrar la conexión
        conn.close()

        return nequi_opciones

    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return []

def convertir_fecha(fecha_str):
    """Convierte una fecha de formato dd-mm-yyyy a yyyy-mm-dd."""
    try:
        return datetime.strptime(fecha_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Error", "Formato de fecha incorrecto. Use dd-mm-yyyy.")
        return None

def agregar_registro(tree, entry_hoy, entry_cedula, entry_nombre, entry_placa, entry_monto, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada):
    # Obtener los valores de los entry y combo directamente
    cedula = entry_cedula.get().strip()
    nombre = entry_nombre.get().strip()
    placa = entry_placa.get().strip()
    valor = entry_monto.get().strip()
    referencia = entry_referencia.get().strip()
    fecha_hoy = entry_hoy.get().strip()
    fecha = entry_fecha.get().strip()
    tipo = combo_tipo.get().strip()
    nequi = combo_nequi.get().strip()
    verificada = combo_verificada.get().strip()

    # Validar que la combinación de cédula, nombre y placa exista y sea única en la tabla clientes
    try:
        with sqlite3.connect("diccionarios/base_dat.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE Cedula = ? AND Nombre = ? AND Placa = ?", (cedula, nombre, placa))
            count = cursor.fetchone()[0]

            if count != 1:
                messagebox.showerror("Error", "La combinación de cédula, nombre y placa no es única o no existe.")
                return

            # Validar que el monto sea numérico
            try:
                valor = float(valor)
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un valor numérico.")
                return

            # Validar referencia y nequi dependiendo del tipo de pago
            if tipo.lower() != "efectivo":
                if not referencia or not nequi:
                    messagebox.showerror("Error", "Referencia y Nequi deben ser proporcionados si el tipo de pago no es 'Efectivo'.")
                    return

            # Validar la fecha_hoy
            fecha_hoy_bd = convertir_fecha(fecha_hoy)
            if fecha_hoy_bd is None:
                return  # Salir si hubo error en la conversión

            # Convertir la fecha al formato correcto antes de guardar en la BD
            fecha_bd = convertir_fecha(fecha)
            if fecha_bd is None:
                return  # Salir si hubo error en la conversión

            # Insertar en la base de datos
            cursor.execute("""
                INSERT INTO registros (Fecha_sistema, Fecha_registro, Cedula, Nombre, Placa, Valor, Tipo, Nombre_cuenta, Referencia, Verificada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_hoy_bd, fecha_bd, cedula, nombre, placa, valor, tipo, nequi, referencia, verificada))
            conn.commit()

            messagebox.showinfo("Éxito", "Registro agregado correctamente.")

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al guardar en la base de datos: {e}")





