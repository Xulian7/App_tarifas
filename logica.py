import pandas as pd
import tkinter as tk
import tkinter.font as tkFont
from tkinter import font
from tkinter import filedialog, messagebox
from tkinter import ttk
import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd
from tkcalendar import DateEntry
import locale

# Establecer configuraciones locales - español
locale.setlocale(locale.LC_ALL, 'es_CO.utf8')

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

def agregar_registro(tree, entry_hoy, entry_cedula, entry_nombre, entry_placa, entry_monto, entry_referencia, entry_fecha, combo_tipo, combo_nequi, combo_verificada):
    # Obtener valores de los widgets
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

    # Lista de campos obligatorios
    campos_faltantes = []
    
    if not cedula:
        campos_faltantes.append("Cédula")
    if not nombre:
        campos_faltantes.append("Nombre")
    if not placa:
        campos_faltantes.append("Placa")
    if not valor:
        campos_faltantes.append("Valor")
    if not fecha_hoy:
        campos_faltantes.append("Fecha de hoy")
    if not fecha:
        campos_faltantes.append("Fecha de registro")
    if not tipo:
        campos_faltantes.append("Tipo")
    if not verificada:
        campos_faltantes.append("Verificada")

    # Validación extra para consignación
    if tipo.lower() == "consignación":
        if not referencia:
            campos_faltantes.append("Referencia")
        if not nequi:
            campos_faltantes.append("Nequi")

    # Si hay campos faltantes, mostrar mensaje y cancelar la operación
    if campos_faltantes:
        mensaje_error = "Faltan valores obligatorios:\n- " + "\n- ".join(campos_faltantes)
        messagebox.showerror("Error", mensaje_error)
        return

    try:
        with sqlite3.connect("diccionarios/base_dat.db") as conn:
            cursor = conn.cursor()

            # Validar si la referencia ya existe
            if referencia:
                cursor.execute("SELECT Referencia, Cedula, Nombre FROM registros WHERE Referencia = ?", (referencia,))
                registro_existente = cursor.fetchone()
                if registro_existente:
                    ref, ced, nom = registro_existente
                    messagebox.showwarning("Referencia duplicada", 
                        f"El registro con referencia '{ref}' ya existe.\n"
                        f"Cédula: {ced}\nNombre: {nom}\n\n"
                        "No se guardará el nuevo registro.")
                    return  # Cancelar la grabación

            # Validar que la combinación de cédula, nombre y placa exista y sea única en clientes
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE Cedula = ? AND Nombre = ? AND Placa = ?", (cedula, nombre, placa))
            count = cursor.fetchone()[0]
            if count != 1:
                messagebox.showerror("Error", "La combinación de cédula, nombre y placa no es única o no existe en la base de datos.")
                return

            # Validar que el monto sea numérico
            try:
                valor = float(valor)
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un valor numérico.")
                return

            # Convertir las fechas al formato correcto antes de guardar en la BD
            fecha_hoy_bd = convertir_fecha(fecha_hoy)
            fecha_bd = convertir_fecha(fecha)
            if fecha_hoy_bd is None or fecha_bd is None:
                return  # Si hubo error en la conversión, cancelar

            # Insertar en la base de datos
            cursor.execute("""
                INSERT INTO registros (Fecha_sistema, Fecha_registro, Cedula, Nombre, Placa, Valor, Tipo, Nombre_cuenta, Referencia, Verificada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_hoy_bd, fecha_bd, cedula, nombre, placa, valor, tipo, nequi, referencia, verificada))
            conn.commit()

            messagebox.showinfo("Éxito", "Registro agregado correctamente.")

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error al guardar en la base de datos: {e}")

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

def obtener_datos_clientes():
    """Obtiene los datos de la tabla clientes desde la base de datos y formatea Capital y Fecha_inicio."""
    conexion = sqlite3.connect("diccionarios/base_dat.db")  # Cambia el nombre si es diferente
    cursor = conexion.cursor()
    
    query = "SELECT Cedula, Nombre, Telefono, Direccion, Placa, Tarjeta_propiedad, Fecha_inicio, Fecha_final, Tipo_contrato, Valor_cuota FROM clientes"
    cursor.execute(query)
    datos = cursor.fetchall()
    
    conexion.close()

    # Formatear los datos
    datos_formateados = []
    for fila in datos:
        cedula, nombre, telefono, direccion, placa, Tarjeta , fecha_inicio, fecha_final, tipo_contrato, valor_cuota = fila
        
        # Formatear la fecha si existe
        if fecha_inicio:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                fecha_inicio = "Formato Inválido"  # En caso de error con la fecha
                
        if fecha_final:
            try:
                fecha_final = datetime.strptime(fecha_final, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                fecha_final = "Formato Inválido"  # En caso de error con la fecha
        
        
        
        datos_formateados.append((cedula, nombre, telefono, direccion, placa, Tarjeta , fecha_inicio, fecha_final, tipo_contrato, valor_cuota))

    return datos_formateados

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
    icono_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'inicio.ico')
    if os.path.exists(icono_path):
        ventana_clientes.iconbitmap(icono_path)
    else:
        print("No se encontró el icono en la ruta especificada")

    # Crear un Frame para contener el Treeview y la Scrollbar
    frame_tree = ttk.Frame(ventana_clientes)
    frame_tree.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

    # Crear el Treeview dentro del Frame
    columnas = ("Cédula", "Nombre", "Teléfono", "Dirección", 
                "Placa","Tarjeta_propiedad", "Fecha Inicio", "Fecha Final", "Tipo Contrato", "Valor Cuota")

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

    # Llenar el Treeview con datos de la base de datos
    for fila in obtener_datos_clientes():
        tree.insert("", "end", values=fila)
    # Ajustar automáticamente el ancho de las columnas después de insertar los datos
    ajustar_columnas(tree)
    
    datos_originales = [tree.item(item)["values"] for item in tree.get_children()]


    # Función para configurar correctamente los DateEntry
    def create_date_entry(parent):
        return DateEntry(parent, width=27, background='darkblue', 
                        foreground='white', borderwidth=2, 
                        date_pattern='dd-MM-yyyy',  # Establecer el formato Día-Mes-Año
                        locale='es_ES')

        # Frame para los Labels y Entries
    frame_form = ttk.LabelFrame(ventana_clientes, text="Información del Cliente")
    frame_form.grid(row=1, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")

    # Diccionario para almacenar las entradas
    entries = {}
    
    cedula_var = tk.StringVar()
    # Función para validar que solo sean números (Si son letras las borra)
    def validar_cedula(*args):
        valor = cedula_var.get()
        if not valor.isdigit():
            cedula_var.set("".join(filter(str.isdigit, valor)))  # Elimina caracteres no numéricos

    # Agregando manualmente cada etiqueta y entrada en un diseño de 3 columnas
    cedula_var.trace_add("write", validar_cedula)
    lbl_cedula = ttk.Label(frame_form, text="Cédula:")
    lbl_cedula.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entries["Cédula"] = ttk.Entry(frame_form, textvariable=cedula_var, width=30)
    entries["Cédula"].grid(row=0, column=1, padx=5, pady=5, sticky="w")

    nombre_var = tk.StringVar()
    nombre_var.trace_add("write", lambda *args: nombre_var.set(nombre_var.get().title()))
    nombre_var.trace_add("write", lambda *args: filtrar_treeview(tree, nombre_var))
    lbl_nombre = ttk.Label(frame_form, text="Nombre:")
    lbl_nombre.grid(row=0, column=2, padx=5, pady=5, sticky="w")

    def filtrar_treeview(tree, nombre_var):
        filtro = nombre_var.get().strip().lower()
        items = tree.get_children()

        if not filtro:
            tree.delete(*items)
            for fila in datos_originales:
                tree.insert("", "end", values=fila)
            return

        tree.delete(*items)
        for fila in datos_originales:
            if filtro in fila[1].lower():
                tree.insert("", "end", values=fila)

    entries["Nombre"] = ttk.Entry(frame_form, textvariable=nombre_var, width=30)
    entries["Nombre"].grid(row=0, column=3, padx=5, pady=5, sticky="w")

    lbl_telefono = ttk.Label(frame_form, text="Teléfono:")
    lbl_telefono.grid(row=0, column=4, padx=5, pady=5, sticky="w")
    entries["Teléfono"] = ttk.Entry(frame_form, width=30)
    entries["Teléfono"].grid(row=0, column=5, padx=5, pady=5, sticky="w")

    lbl_direccion = ttk.Label(frame_form, text="Dirección:")
    lbl_direccion.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entries["Dirección"] = ttk.Entry(frame_form, width=30)
    entries["Dirección"].grid(row=1, column=1, padx=5, pady=5, sticky="w")

    placa_var = tk.StringVar()
    placa_var.trace_add("write", lambda *args: placa_var.set(placa_var.get().upper()))
    placa_var.trace_add("write", lambda *args: consultar_tarjeta_propiedad(placa_var.get()))
    lbl_placa = ttk.Label(frame_form, text="Placa:")
    lbl_placa.grid(row=1, column=2, padx=5, pady=5, sticky="w")
    entries["Placa"] = ttk.Entry(frame_form, textvariable=placa_var, width=30)
    entries["Placa"].grid(row=1, column=3, padx=5, pady=5, sticky="w")

    lbl_tarjeta_propiedad = ttk.Label(frame_form, text="Tarjeta Propiedad:")
    lbl_tarjeta_propiedad.grid(row=1, column=4, padx=5, pady=5, sticky="w")
    entries["Tarjeta_propiedad"] = ttk.Entry(frame_form, width=30, state="readonly")
    entries["Tarjeta_propiedad"].grid(row=1, column=5, padx=5, pady=5, sticky="w")

    def consultar_tarjeta_propiedad(placa):
        import sqlite3
        conn = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conn.cursor()
        cursor.execute("SELECT Tarjeta_propiedad FROM propietario WHERE Placa = ?", (placa,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            entries["Tarjeta_propiedad"].config(state="normal")
            entries["Tarjeta_propiedad"].delete(0, tk.END)
            entries["Tarjeta_propiedad"].insert(0, resultado[0])
            entries["Tarjeta_propiedad"].config(state="readonly")

    lbl_fecha_inicio = ttk.Label(frame_form, text="Fecha Inicio:")
    lbl_fecha_inicio.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    entries["Fecha Inicio"] = create_date_entry(frame_form)
    entries["Fecha Inicio"].grid(row=2, column=1, padx=5, pady=5, sticky="w")

    lbl_fecha_final = ttk.Label(frame_form, text="Fecha Final:")
    lbl_fecha_final.grid(row=2, column=2, padx=5, pady=5, sticky="w")
    entries["Fecha Final"] = create_date_entry(frame_form)
    entries["Fecha Final"].grid(row=2, column=3, padx=5, pady=5, sticky="w")

    lbl_tipo_contrato = ttk.Label(frame_form, text="Tipo Contrato:")
    lbl_tipo_contrato.grid(row=2, column=4, padx=5, pady=5, sticky="w")
    tipos_opciones = ["Alquiler", "Opcion de compra", "Empeño"]
    entries["Tipo Contrato"] = ttk.Combobox(frame_form, values=tipos_opciones, state="readonly", width=30)
    entries["Tipo Contrato"].grid(row=2, column=5, padx=5, pady=5, sticky="w")


    lbl_valor_cuota = ttk.Label(frame_form, text="Valor Cuota:")
    lbl_valor_cuota.grid(row=3, column=4, padx=5, pady=5, sticky="w")
    entries["Valor Cuota"] = ttk.Entry(frame_form, width=30)
    entries["Valor Cuota"].grid(row=3, column=5, padx=5, pady=5, sticky="w")
    
    def limpiar_formulario():
        """Limpia todos los campos de entrada en el formulario."""
        for entry in entries.values():
                entry.delete(0, "end")
                entries["Tipo Contrato"].set("")  # Resetear el Combobox
                entries["Tarjeta_propiedad"].config(state="normal")
                entries["Tarjeta_propiedad"].delete(0, tk.END)
                entries["Tarjeta_propiedad"].config(state="readonly")
    
    def registrar_cliente():
        pass
    
    def cargar_datos_desde_treeview():
        # Carga los datos seleccionados del Treeview en los campos del formulario.
        seleccion = tree.selection()
        
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un cliente en la tabla.")
            return

        # Obtiene los valores de la fila seleccionada
        valores = tree.item(seleccion[0], "values")

        if not valores:
            messagebox.showwarning("Advertencia", "No hay datos en la selección.")
            return
        
        #print(valores)
        # Asignación de valores a cada campo del formulario
        entries["Cédula"].delete(0, tk.END)
        entries["Cédula"].insert(0, valores[0])
        entries["Nombre"].delete(0, tk.END)
        entries["Nombre"].insert(0, valores[1])
        entries["Teléfono"].delete(0, tk.END)
        entries["Teléfono"].insert(0, valores[2])
        entries["Dirección"].delete(0, tk.END)
        entries["Dirección"].insert(0, valores[3])
        entries["Placa"].delete(0, tk.END)
        entries["Placa"].insert(0, valores[4])
        entries["Fecha Inicio"].set_date(valores[6])  # Para DateEntry
        entries["Fecha Final"].set_date(valores[7])  # Para DateEntry

        # Manejo del Combobox de "Tipo Contrato"
        opciones_tipo_contrato = entries["Tipo Contrato"]["values"]
        if valores[8] in opciones_tipo_contrato:
            entries["Tipo Contrato"].set(valores[8])
        else:
            print(f"El valor '{valores[8]}' no está en las opciones del Combobox")


        entries["Valor Cuota"].delete(0, tk.END)
        entries["Valor Cuota"].insert(0, valores[11])

        # Consultar la base de datos para obtener la Tarjeta de Propiedad
        conn = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conn.cursor()
        cursor.execute("SELECT Tarjeta_propiedad FROM propietario WHERE Placa = ?", (valores[4],))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            entries["Tarjeta_propiedad"].config(state="normal")
            entries["Tarjeta_propiedad"].delete(0, tk.END)
            entries["Tarjeta_propiedad"].insert(0, resultado[0])
            entries["Tarjeta_propiedad"].config(state="readonly")

        
    # Frame para los botones
    frame_buttons = ttk.Frame(ventana_clientes)
    frame_buttons.grid(row=2, column=0, columnspan=4, pady=10)

    # Botones Crear, Modificar, Inhabilitar
    btn_crear = ttk.Button(frame_buttons, text="Crear", command=registrar_cliente)
    btn_crear.grid(row=0, column=0, padx=10)

    btn_modificar = ttk.Button(frame_buttons, text="Modificar")
    btn_modificar.grid(row=0, column=1, padx=10)
    
    btn_limpiar = ttk.Button(frame_buttons, text="Limpiar", command=limpiar_formulario)
    btn_limpiar.grid(row=0, column=2, padx=10)
    
    btn_inhabilitar = ttk.Button(frame_buttons, text="Inhabilitar", command=lambda: print("Función Inhabilitar"))
    btn_inhabilitar.grid(row=0, column=3, padx=10)
    
    tree.bind("<Double-1>", lambda event: cargar_datos_desde_treeview())

    # Expansión de filas y columnas
    ventana_clientes.columnconfigure(0, weight=1)
    ventana_clientes.rowconfigure(0, weight=1)
    
    return ventana_clientes  # Si quieres capturar la ventana creada

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

def mostrar_registros(entry_nombre, entry_fecha):
    nombre = entry_nombre.get().strip()
    fecha_texto = entry_fecha.get().strip()

    # Validar que al menos el nombre esté presente
    if not nombre:
        messagebox.showerror("Error", "Debe ingresar un nombre.")
        return
    
    # Inicializar variables de fecha
    mes, anio, nombre_mes = None, None, "Totales"  # "Totales" por defecto si no hay fecha

    if fecha_texto:
        try:
            fecha_obj = datetime.strptime(fecha_texto, "%d-%m-%Y")
            mes = fecha_obj.month
            anio = fecha_obj.year
            nombre_mes = fecha_obj.strftime("%B").capitalize()  # Obtener mes en español
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-YYYY.")
            return

    # Conectar a la base de datos y obtener datos
    try:
        with sqlite3.connect("diccionarios/base_dat.db") as conn:
            cursor = conn.cursor()

            # Obtener la Cédula, Nombre y Placa de la primera coincidencia
            cursor.execute("SELECT Cedula, Nombre, Placa FROM Registros WHERE Nombre = ? LIMIT 1", (nombre,))
            info_cliente = cursor.fetchone()
            # Obtener valores de pagos, cuotas y plazos
            cursor.execute("SELECT Fecha_inicio, Fecha_final, Valor_cuota FROM clientes WHERE Nombre = ?", (nombre,))
            balance = cursor.fetchone()
            # Buscar la suma de abonos en la tabla 'registros'
            cursor.execute("SELECT COALESCE(SUM(Valor), 0) FROM registros WHERE Nombre = ?", (nombre,))
            total_abonos = cursor.fetchone()[0]
            
            
            if not info_cliente:
                messagebox.showinfo("Sin resultados", "No se encontraron registros para el nombre dado.")
                return

            cedula, nombre, placa = info_cliente
            fecha_inicio_str, Fecha_final_str, valor_cuota = balance
                    
            # Calcular C_vencidas (días transcurridos desde Fecha_inicio hasta hoy)
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            C_totales = (fecha_inicio - datetime.strptime(Fecha_final_str, "%Y-%m-%d")).days
            c_vencidas = (datetime.today() - fecha_inicio).days + 1
            c_saldas = total_abonos / valor_cuota if valor_cuota else 0

            # Definir consulta SQL a todos los registros
            cursor.execute("""
                SELECT Fecha_registro, Valor, Tipo, Referencia, Verificada 
                FROM Registros 
                WHERE Nombre = ? 
                ORDER BY Fecha_registro ASC
            """, (nombre,))
        
            registros = cursor.fetchall()
            
            al_dia = round((c_vencidas-c_saldas)*valor_cuota, 2)
            al_dia_formateado = locale.currency(al_dia, grouping=True)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Ocurrió un error con la base de datos: {e}")
        return
    

    # Crear una nueva ventana para mostrar los datos
    ventana = tk.Toplevel()
    ventana.title("Historial de pagos")

    # Definir el título con "Totales" si no hay fecha
    titulo_texto = f"Extracto pagos {nombre_mes} - Leo Motos"
    lbl_titulo = tk.Label(ventana, text=titulo_texto, font=("Arial", 14, "bold"), fg="blue")
    lbl_titulo.pack(pady=10)

    # Zona superior con Cedula, Nombre y Placa
    frame_info = tk.Frame(ventana)
    frame_info.pack(pady=10, padx=10)
    
    # Fuente en negrita para etiquetas / normal variables
    bold_font = font.Font(family="Arial", size=10, weight="bold")
    normal_font = font.Font(family="Arial", size=10, weight="normal")
    
    def create_label(frame, label_text, variable_text, row, col):
        tk.Label(frame, text=label_text, font=bold_font).grid(row=row, column=col, padx=3, pady=3, sticky="w")
        tk.Label(frame, text=variable_text, font=normal_font).grid(row=row, column=col+1, padx=3, pady=3, sticky="w")
        
    create_label(frame_info, "Cédula:", cedula, 0, 0)
    create_label(frame_info, "Nombre:", nombre, 1, 0)
    create_label(frame_info, "Placa:", placa, 2, 0)
    create_label(frame_info, "Cuotas vencidas:", c_vencidas, 0, 4)
    create_label(frame_info, "Cuotas pagas:", round(c_saldas, 2), 1, 4)
    create_label(frame_info, "Cuotas pendientes:", round(c_vencidas-c_saldas, 2), 2, 4)
    create_label(frame_info, "$ al dia:", al_dia_formateado, 3, 2)
    
    # Crear Treeview para mostrar los registros
    frame_tree = tk.Frame(ventana)
    frame_tree.pack(pady=10, padx=10, fill="both", expand=True)
    columnas = ("Calendario", "Fecha_registro", "Valor", "Tipo", "Referencia" ,"Verificada")
    tree = ttk.Treeview(frame_tree, columns=columnas, show="headings", selectmode="browse")

    # Definir encabezados
    tree.heading("Calendario", text="Calendario")
    tree.heading("Fecha_registro", text="Fecha Registro")
    tree.heading("Valor", text="Valor")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Referencia", text="Referencia")
    tree.heading("Verificada", text="Verificada")

    # Ajustar ancho de columnas
    for col in columnas:
        tree.column(col, anchor="center", width=120)

    # Definir un estilo para los registros con deuda
    tree.tag_configure("deuda", foreground="red")
    
    # Inicializar variables para la fecha esperada
    fecha_esperada = fecha_inicio
    saldo_pendiente = valor_cuota  # Inicia con la cuota completa esperando ser cubierta
        
    # Insertar los datos en el treeview con la fecha en formato DD-MM-YYYY
    for registro in registros:
        fecha_formateada = datetime.strptime(registro[0], "%Y-%m-%d").strftime("%d-%m-%Y")
        valor_registro = registro[1]  # El valor del pago en la fila
        fecha_pago = datetime.strptime(registro[0], "%Y-%m-%d")  # Fecha real del pago
        valor_pago = registro[1]  # Monto del abono
        
        # Si el pago cubre la cuota esperada, actualizar fecha esperada
        saldo_pendiente -= valor_pago
        while saldo_pendiente < 0:  # Si cubrió al menos una cuota, avanzar fecha
            saldo_pendiente += valor_cuota  # Se "renueva" la deuda de la nueva fecha esperada
            fecha_esperada += timedelta(days=1)
            
            
        # Si el valor es menor a la cuota, marcarlo en rojo
        tag = "deuda" if valor_registro < valor_cuota else ""
        # Insertar en el Treeview
        fecha_formateada = fecha_pago.strftime("%d-%m-%Y")
        fecha_esperada_formateada = fecha_esperada.strftime("%d-%m-%Y")
        tree.insert("", "end", values=(fecha_esperada_formateada, fecha_formateada, *registro[1:]), tags=(tag,))

    tree.pack(fill="both", expand=True)


def join_and_export():
    # Abrir el diálogo para seleccionar la carpeta de destino
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal de Tkinter
    folder_selected = filedialog.askdirectory(title="Selecciona una carpeta para guardar el archivo")

    if not folder_selected:  # Si el usuario cancela, salir de la función
        messagebox.showwarning("Operación cancelada", "No se guardó ningún archivo.")
        return

    output_path = os.path.join(folder_selected, "resultado.xlsx")

    # Conectar a la base de datos
    conn = sqlite3.connect('diccionarios/base_dat.db')

    # Definir la consulta SQL con el JOIN usando 'placa' como clave
    query = """
    SELECT r.*, p.*
    FROM registros r
    LEFT JOIN propietario p ON r.placa = p.placa
    """

    # Ejecutar la consulta y cargar los datos en un DataFrame
    merged_df = pd.read_sql_query(query, conn)

    # Cerrar la conexión
    conn.close()

    # Exportar a Excel en la carpeta seleccionada
    merged_df.to_excel(output_path, index=False)

    # Mostrar mensaje con la ruta del archivo guardado
    messagebox.showinfo("Exportación exitosa", f"El archivo .xlsx se guardó en:\n{output_path}")






