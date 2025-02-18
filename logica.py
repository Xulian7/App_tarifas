import pandas as pd
import tkinter as tk
import tkinter.font as tkFont
from tkinter import font
from tkinter import filedialog, messagebox, ttk
import sqlite3
import os
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import locale


# Establecer configuraciones locales - español
locale.setlocale(locale.LC_ALL, 'es_CO.utf8')
ventana_clientes = None  # Variable global dentro del módulo

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

        # Construir la consulta SQL con filtros y JOIN para agregar el Color
        query = """
            SELECT r.id, r.Fecha_sistema, r.Fecha_registro, r.Cedula, r.Nombre, 
                r.Placa, p.Color, r.Valor, r.Saldos, r.Tipo, r.Nombre_cuenta, 
                r.Referencia, r.Verificada
            FROM registros r
            LEFT JOIN propietario p ON r.Placa = p.Placa
            WHERE 1=1
        """

        params = []

        if cedula:
            query += " AND r.Cedula = ?"
            params.append(cedula)
        if nombre:
            query += " AND r.Nombre LIKE ?"
            params.append(f"%{nombre}%")
        if placa:
            query += " AND r.Placa LIKE ?"
            params.append(f"%{placa}%")
        if referencia:
            query += " AND r.Referencia LIKE ?"
            params.append(f"%{referencia}%")
        if fecha:
            query += " AND r.Fecha_registro = ?"
            params.append(fecha)
        if tipo:
            query += " AND r.Tipo = ?"
            params.append(tipo)
        if nequi:
            query += " AND r.Nombre_cuenta = ?"
            params.append(nequi)
        if verificada:
            query += " AND r.Verificada = ?"
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
            tags = ("sombreado",) if row[12] == "No" else ()
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

def limpiar_formulario(entry_cedula, entry_nombre, entry_placa, entry_monto, entry_saldos, entry_referencia, entry_fecha,
combo_tipo, combo_nequi, combo_verificada, listbox_sugerencias, tree):
    # Limpiar campos de texto (Entry)
    entry_cedula.focus_set()
    entry_cedula.delete(0, tk.END)
    entry_nombre.delete(0, tk.END)
    entry_placa.delete(0, tk.END)
    entry_monto.delete(0, tk.END)
    entry_saldos.delete(0, tk.END)
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

def cargar_nequi_opciones():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()

        # Obtener las columnas 'Entidad' y 'Titular' de la tabla 'Cuentas'
        cursor.execute("SELECT Nombre_cuenta FROM cuentas")
        rows = cursor.fetchall()

        # Crear la lista con la concatenación 'Entidad - Titular'
        nequi_opciones = [row[0] for row in rows]


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

def obtener_datos_clientes():
    """Obtiene los datos de la tabla clientes desde la base de datos y formatea Capital y Fecha_inicio."""
    conexion = sqlite3.connect("diccionarios/base_dat.db")  # Cambia el nombre si es diferente
    cursor = conexion.cursor()
    
    # Consulta SQL
    query = """
        SELECT 
            c.Cedula, c.Nombre, c.Nacionalidad, c.Telefono, c.Direccion, 
            c.Placa, p.Modelo, p.Tarjeta_propiedad, 
            c.Fecha_inicio, c.Fecha_final, c.Tipo_contrato, c.Valor_cuota, c.Estado 
        FROM clientes c 
        LEFT JOIN propietario p ON c.Placa = p.Placa;
    """

    cursor.execute(query)
    datos = cursor.fetchall()
    
    conexion.close()

    # Formatear los datos
    datos_formateados = []
    for fila in datos:
        cedula, nombre, nacionalidad, telefono, direccion, placa, modelo, Tarjeta , fecha_inicio, fecha_final, tipo_contrato, valor_cuota, estado = fila
        
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
        
        
        
        datos_formateados.append((cedula, nombre, nacionalidad, telefono, direccion, placa, modelo, Tarjeta , fecha_inicio, fecha_final, tipo_contrato, valor_cuota, estado))

    return datos_formateados

def abrir_ventana_clientes():
    
    global ventana_clientes

    if ventana_clientes and ventana_clientes.winfo_exists():
        ventana_clientes.lift()  # Trae la ventana al frente si ya existe
        return
    
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
    columnas = ("Cédula", "Nombre","Nacionalidad", "Teléfono", "Dirección", 
                "Placa","Modelo","Tarjeta propiedad", "Fecha Inicio", "Fecha Final", "Tipo Contrato", "Valor Cuota", "Estado")

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
    
    global datos_originales
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
    
    nacion_var = tk.StringVar()
    nacion_var.trace_add("write", lambda *args: nacion_var.set(nacion_var.get().title()))
    lbl_nacion = ttk.Label(frame_form, text="Nacionalidad:")
    lbl_nacion.grid(row=0, column=4, padx=4, pady=5, sticky="w")
    entries["Nacionalidad"] = ttk.Entry(frame_form, textvariable=nacion_var, width=30)
    entries["Nacionalidad"].grid(row=0, column=5, padx=5, pady=5, sticky="w")
    
    lbl_telefono = ttk.Label(frame_form, text="Teléfono:")
    lbl_telefono.grid(row=1, column=0, padx=0, pady=5, sticky="w")
    entries["Teléfono"] = ttk.Entry(frame_form, width=30)
    entries["Teléfono"].grid(row=1, column=1, padx=5, pady=5, sticky="w")

    lbl_direccion = ttk.Label(frame_form, text="Dirección:")
    lbl_direccion.grid(row=1, column=2, padx=5, pady=5, sticky="w")
    entries["Dirección"] = ttk.Entry(frame_form, width=30)
    entries["Dirección"].grid(row=1, column=3, padx=5, pady=5, sticky="w")

    placa_var = tk.StringVar()
    placa_var.trace_add("write", lambda *args: placa_var.set(placa_var.get().upper()))
    placa_var.trace_add("write", lambda *args: consultar_tarjeta_propiedad(placa_var.get()))
    placa_var.trace_add("write", lambda *args: consultar_modelo(placa_var.get()))
    lbl_placa = ttk.Label(frame_form, text="Placa:")
    lbl_placa.grid(row=1, column=4, padx=5, pady=5, sticky="w")
    entries["Placa"] = ttk.Entry(frame_form, textvariable=placa_var, width=30)
    entries["Placa"].grid(row=1, column=5, padx=5, pady=5, sticky="w")
    
    lbl_modelo = ttk.Label(frame_form, text="Modelo:")
    lbl_modelo.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    entries["Modelo"] = ttk.Entry(frame_form, width=30, state="readonly")
    entries["Modelo"].grid(row=2, column=1, padx=5, pady=5, sticky="w")

    lbl_tarjeta_propiedad = ttk.Label(frame_form, text="Tarjeta Propiedad:")
    lbl_tarjeta_propiedad.grid(row=2, column=2, padx=5, pady=5, sticky="w")
    entries["Tarjeta_propiedad"] = ttk.Entry(frame_form, width=30, state="readonly")
    entries["Tarjeta_propiedad"].grid(row=2, column=3, padx=5, pady=5, sticky="w")
    
    def consultar_modelo(placa):
        import sqlite3
        conn = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conn.cursor()
        cursor.execute("SELECT Modelo FROM propietario WHERE Placa = ?", (placa,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            entries["Modelo"].config(state="normal")
            entries["Modelo"].delete(0, tk.END)
            entries["Modelo"].insert(0, resultado[0])
            entries["Modelo"].config(state="readonly")
    
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
    lbl_fecha_inicio.grid(row=2, column=4, padx=5, pady=5, sticky="w")
    entries["Fecha Inicio"] = create_date_entry(frame_form)
    entries["Fecha Inicio"].grid(row=2, column=5, padx=5, pady=5, sticky="w")

    lbl_fecha_final = ttk.Label(frame_form, text="Fecha Final:")
    lbl_fecha_final.grid(row=3, column=0, padx=5, pady=5, sticky="w")
    entries["Fecha Final"] = create_date_entry(frame_form)
    entries["Fecha Final"].grid(row=3, column=1, padx=5, pady=5, sticky="w")

    lbl_tipo_contrato = ttk.Label(frame_form, text="Tipo Contrato:")
    lbl_tipo_contrato.grid(row=3, column=2, padx=5, pady=5, sticky="w")
    tipos_opciones = ["Alquiler", "Opcion de compra", "Empeño"]
    entries["Tipo Contrato"] = ttk.Combobox(frame_form, values=tipos_opciones, state="readonly", width=30)
    entries["Tipo Contrato"].grid(row=3, column=3, padx=5, pady=5, sticky="w")

    lbl_valor_cuota = ttk.Label(frame_form, text="Valor Cuota:")
    lbl_valor_cuota.grid(row=3, column=4, padx=5, pady=5, sticky="w")
    entries["Valor Cuota"] = ttk.Entry(frame_form, width=30)
    entries["Valor Cuota"].grid(row=3, column=5, padx=5, pady=5, sticky="w")
    
    lbl_estado = ttk.Label(frame_form, text="Estado:")
    lbl_estado.grid(row=3, column=6, padx=5, pady=5, sticky="w")
    estado_opciones = ["","activo", "inactivo"]
    combo_estado = ttk.Combobox(frame_form, values=estado_opciones, width=30)
    combo_estado.grid(row=3, column=7, padx=5, pady=5, sticky="w")
    
    def limpiar_formulario():
        """Limpia todos los campos de entrada en el formulario."""
        for entry in entries.values():
                entry.delete(0, "end")
        
        entries["Tipo Contrato"].set("")  # Resetear el Combobox
        entries["Tarjeta_propiedad"].config(state="normal")
        entries["Tarjeta_propiedad"].delete(0, tk.END)
        entries["Tarjeta_propiedad"].config(state="readonly")
        combo_estado.set("")
        
    def convertir_fecha_formato_sqlite(fecha_ui):
        """Convierte una fecha de formato dd-mm-yyyy a yyyy-mm-dd"""
        try:
            dia, mes, año = fecha_ui.split('-')
            return f"{año}-{mes}-{dia}"
        except ValueError:
            messagebox.showerror("Error", f"Formato de fecha inválido: {fecha_ui}")
            return None

    def registrar_cliente():
        # Obtener valores de los campos
        valores = [
            entries["Cédula"].get().strip(),
            entries["Nombre"].get().strip(),
            entries["Nacionalidad"].get().strip(),
            entries["Teléfono"].get().strip(),
            entries["Dirección"].get().strip(),
            entries["Placa"].get().strip(),
            convertir_fecha_formato_sqlite(entries["Fecha Inicio"].get().strip()),
            convertir_fecha_formato_sqlite(entries["Fecha Final"].get().strip()),
            entries["Tipo Contrato"].get().strip(),
            entries["Valor Cuota"].get().strip(),
            combo_estado.get().strip()
        ]

        # Verificar si hay campos vacíos
        if None in valores or "" in valores:
            messagebox.showerror("Error", "Todos los campos deben estar llenos y las fechas deben tener el formato correcto.")
            ventana_clientes.focus_force()
            return

        # Conectar a la base de datos
        conexion = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conexion.cursor()

        # Validaciones
        cursor.execute("SELECT Placa FROM propietario WHERE Placa = ?", (valores[5],))
        if not cursor.fetchone():
            messagebox.showwarning("Advertencia", f"La Placa {valores[5]} no está registrada en la base de datos de propietarios.")
            conexion.close()
            return  

        cursor.execute("SELECT Cedula, Placa FROM clientes WHERE Cedula = ? OR Placa = ?", (valores[0], valores[5]))
        resultado = cursor.fetchone()

        if resultado:
            mensaje = "No se puede registrar el cliente porque:\n"
            if resultado[0] == valores[0]:
                mensaje += f"- La Cédula {resultado[0]} ya está registrada.\n"
            if resultado[1] == valores[5]:
                mensaje += f"- La Placa {resultado[1]} ya está asignada a otro cliente.\n"
            messagebox.showwarning("Advertencia", mensaje)
        else:
            try:
                cursor.execute("""
                    INSERT INTO clientes (Cedula, Nombre, Nacionalidad, Telefono, Direccion, Placa, Fecha_inicio, Fecha_final, Tipo_contrato, Valor_cuota, Estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, valores)
                conexion.commit()
                ventana_clientes.focus_force()
                messagebox.showinfo("Éxito", "Cliente guardado correctamente.")
                    
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo guardar el cliente.\n{e}")
                ventana_clientes.focus_force()

        conexion.close()
        
        # 🔹 ACTUALIZAR EL TREEVIEW
        tree.delete(*tree.get_children())  # Limpiar datos actuales en el Treeview
        for fila in obtener_datos_clientes():  # Obtener datos actualizados de la BD
            tree.insert("", "end", values=fila)
        ajustar_columnas(tree)  # Ajustar ancho de columnas automáticamente

        # 🔹 ACTUALIZAR datos_originales
        global datos_originales  # Asegurar que se modifique la variable global
        datos_originales = [tree.item(item)["values"] for item in tree.get_children()]
        ventana_clientes.focus_force()

    def actualizar_cliente():
        # Obtener valores de los campos
        valores = {
            "Cedula": entries["Cédula"].get().strip(),
            "Nombre": entries["Nombre"].get().strip(),
            "Nacionalidad": entries["Nacionalidad"].get().strip(),
            "Telefono": entries["Teléfono"].get().strip(),
            "Direccion": entries["Dirección"].get().strip(),
            "Placa": entries["Placa"].get().strip(),
            "Fecha_inicio": convertir_fecha_formato_sqlite(entries["Fecha Inicio"].get().strip()),
            "Fecha_final": convertir_fecha_formato_sqlite(entries["Fecha Final"].get().strip()),
            "Tipo_contrato": entries["Tipo Contrato"].get().strip(),
            "Valor_cuota": entries["Valor Cuota"].get().strip(),
            "Estado": combo_estado.get().strip()
        }

        # Verificar si hay campos vacíos
        if None in valores.values() or "" in valores.values():
            messagebox.showerror("Error", "Todos los campos deben estar llenos y las fechas deben tener el formato correcto.")
            ventana_clientes.focus_force()
            return

        # Conectar a la base de datos
        conexion = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conexion.cursor()

        # Validaciones
        cursor.execute("SELECT Placa FROM clientes WHERE Cedula = ?", (valores["Cedula"],))
        resultado_cliente = cursor.fetchone()

        if not resultado_cliente:
            messagebox.showerror("Error", f"No existe un cliente con la Cédula {valores['Cedula']}.")
            conexion.close()
            return

        cursor.execute("SELECT Placa FROM propietario WHERE Placa = ?", (valores["Placa"],))
        if not cursor.fetchone():
            messagebox.showwarning("Advertencia", f"La Placa {valores['Placa']} no está registrada en la base de datos de propietarios.")
            conexion.close()
            ventana_clientes.focus_force()
            return  

        cursor.execute("SELECT Cedula FROM clientes WHERE Placa = ? AND Cedula != ?", (valores["Placa"], valores["Cedula"]))
        if cursor.fetchone():
            messagebox.showwarning("Advertencia", f"La Placa {valores['Placa']} ya está asignada a otro cliente.")
            conexion.close()
            ventana_clientes.focus_force()
            return

        try:
            cursor.execute("""
                UPDATE clientes
                SET Nombre = ?, Nacionalidad = ?, Telefono = ?, Direccion = ?, Placa = ?, 
                    Fecha_inicio = ?, Fecha_final = ?, Tipo_contrato = ?, Valor_cuota = ?, Estado = ?
                WHERE Cedula = ?
            """, (
                valores["Nombre"], valores["Nacionalidad"], valores["Telefono"], valores["Direccion"],
                valores["Placa"], valores["Fecha_inicio"], valores["Fecha_final"], valores["Tipo_contrato"],
                valores["Valor_cuota"], valores["Estado"], valores["Cedula"]
            ))
            conexion.commit()
            messagebox.showinfo("Éxito", "Cliente actualizado correctamente.")
            ventana_clientes.focus_force()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"No se pudo actualizar el cliente.\n{e}")
            ventana_clientes.focus_force()
        conexion.close()
        
        # 🔹 ACTUALIZAR EL TREEVIEW
        tree.delete(*tree.get_children())  # Limpiar datos actuales en el Treeview
        for fila in obtener_datos_clientes():  # Obtener datos actualizados de la BD
            tree.insert("", "end", values=fila)
        ajustar_columnas(tree)  # Ajustar ancho de columnas automáticamente

        # 🔹 ACTUALIZAR datos_originales
        global datos_originales  # Asegurar que se modifique la variable global
        datos_originales = [tree.item(item)["values"] for item in tree.get_children()]
        ventana_clientes.focus_force()

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
        entries["Nacionalidad"].delete(0, tk.END)
        entries["Nacionalidad"].insert(0, valores[2])
        entries["Teléfono"].delete(0, tk.END)
        entries["Teléfono"].insert(0, valores[3])
        entries["Dirección"].delete(0, tk.END)
        entries["Dirección"].insert(0, valores[4])
        entries["Placa"].delete(0, tk.END)
        entries["Placa"].insert(0, valores[5])
        entries["Fecha Inicio"].set_date(valores[8])  # Para DateEntry
        entries["Fecha Final"].set_date(valores[9])  # Para DateEntry

        # Manejo del Combobox de "Tipo Contrato"
        opciones_tipo_contrato = entries["Tipo Contrato"]["values"]
        if valores[10] in opciones_tipo_contrato:
            entries["Tipo Contrato"].set(valores[10])
        else:
            print(f"El valor '{valores[8]}' no está en las opciones del Combobox")

        entries["Valor Cuota"].delete(0, tk.END)
        entries["Valor Cuota"].insert(0, valores[11])
        combo_estado.set(valores[12])

                
    # Configurar estilo de los botones
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12, "bold"), padding=6, width=12)
    style.configure("BotonCrear.TButton", background="#4CAF50", foreground="black")
    style.configure("BotonModificar.TButton", background="#FFC107", foreground="black")
    style.configure("BotonLimpiar.TButton", background="#F44336", foreground="black")

    # Configurar el frame con un borde
    frame_buttons = ttk.Frame(ventana_clientes, relief="ridge", borderwidth=3)
    frame_buttons.grid(row=2, column=0, columnspan=4, pady=10, padx=10, sticky="ew")

    # Botones Crear, Modificar, Limpiar con estilos personalizados
    btn_crear = ttk.Button(frame_buttons, text="Crear", command=registrar_cliente, style="BotonCrear.TButton")
    btn_crear.grid(row=0, column=0, padx=10, pady=5)

    btn_modificar = ttk.Button(frame_buttons, text="Modificar", command=actualizar_cliente, style="BotonModificar.TButton")
    btn_modificar.grid(row=0, column=1, padx=10, pady=5)

    btn_limpiar = ttk.Button(frame_buttons, text="Limpiar", command=limpiar_formulario, style="BotonLimpiar.TButton")
    btn_limpiar.grid(row=0, column=2, padx=10, pady=5)
    

        
    tree.bind("<Double-1>", lambda event: cargar_datos_desde_treeview())

    # Expansión de filas y columnas
    ventana_clientes.columnconfigure(0, weight=1)
    ventana_clientes.rowconfigure(0, weight=1)
    
    ventana_clientes.protocol("WM_DELETE_WINDOW", cerrar_ventana_clientes)
    return ventana_clientes  # Si quieres capturar la ventana creada

def cerrar_ventana_clientes():
    global ventana_clientes
    ventana_clientes.destroy()
    ventana_clientes = None  # Resetea la variable

def abrir_ventana_cuentas():
    # Crear ventana
    ventana_cuentas = tk.Toplevel()
    ventana_cuentas.title("Gestión de Cuentas")
    ventana_cuentas.geometry("600x400")
    ventana_cuentas.rowconfigure(0, weight=1)
    ventana_cuentas.columnconfigure(0, weight=1)

    # Establecer un icono (si existe)
    icono_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'inicio.ico')
    if os.path.exists(icono_path):
        ventana_cuentas.iconbitmap(icono_path)


    # Frame superior para la tabla
    frame_tabla = ttk.Frame(ventana_cuentas)
    frame_tabla.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    # Permitir expansión dentro del frame
    frame_tabla.rowconfigure(0, weight=1)
    frame_tabla.columnconfigure(0, weight=1)

    # Crear Treeview con scrollbar
    columnas = ("ID", "Nombre cuenta", "Llave")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

    # Scrollbar vertical
    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)

    # Configuración de columnas
    for col in columnas:
        tree.heading(col, text=col, anchor="center")
        tree.column(col, anchor="center", width=150, stretch=True)

    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Función para cargar datos desde la base de datos
    def cargar_datos():
        try:
            # Limpiar el Treeview antes de recargar los datos
            for item in tree.get_children():
                tree.delete(item)

            conn = sqlite3.connect('diccionarios/base_dat.db')
            cursor = conn.cursor()
            cursor.execute("SELECT ID, Nombre_cuenta, Llave FROM cuentas")
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar los datos: {e}")
            ventana_cuentas.focus_force()
    
    # Función para crear una nueva cuenta
    def crear_cuenta():
        titular_valor = entry_titular.get().strip()
        llave_valor = entry_llave.get().strip()

        if not titular_valor  or not llave_valor:
            messagebox.showwarning("Advertencia", "Todos los campos deben ser completados")
            ventana_cuentas.focus_force()
            return

        try:
            conn = sqlite3.connect('diccionarios/base_dat.db')
            cursor = conn.cursor()

            # Verificar si la combinación Entidad - Llave ya existe
            cursor.execute("SELECT COUNT(*) FROM cuentas WHERE Nombre_cuenta = ? AND Llave = ?", (titular_valor, llave_valor))
            if cursor.fetchone()[0] > 0:
                messagebox.showwarning("Advertencia", "La combinación Titular - Llave ya existe en la base de datos.")
                entry_llave.focus_force()
                return

            # Insertar la nueva cuenta
            cursor.execute("INSERT INTO cuentas (Nombre_cuenta, Llave) VALUES (?, ?)", 
                        (titular_valor, llave_valor))
            conn.commit()

            # Insertar en Treeview y limpiar entradas
            tree.insert("", "end", values=(cursor.lastrowid, titular_valor, llave_valor))
            entry_titular.delete(0, tk.END)
            entry_llave.delete(0, tk.END)

            messagebox.showinfo("Éxito", "Cuenta creada exitosamente")
            ventana_cuentas.focus_force()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la cuenta: {e}")

        finally:
            conn.close()

    # Función para eliminar una cuenta
    def eliminar_cuenta():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione un registro para eliminar.")
            ventana_cuentas.focus_force()
            return

        item_values = tree.item(selected_item)["values"]
        
        if not item_values:  # Evitar errores si no hay valores
            messagebox.showerror("Error", "No se pudo obtener la información del registro seleccionado.")
            return
        
        id_cuenta = item_values[0]  # Se asume que el ID está en la primera columna

        confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar cuenta ID {id_cuenta}?")
        ventana_cuentas.focus_force()
        if confirmacion:
            try:
                conn = sqlite3.connect('diccionarios/base_dat.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cuentas WHERE ID = ?", (id_cuenta,))
                conn.commit()
                
                tree.delete(selected_item)
                messagebox.showinfo("Éxito", f"Cuenta ID {id_cuenta} eliminada.")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")  
            
            finally:
                conn.close()
            
            ventana_cuentas.focus_force()

    # Cargar datos al inicio
    cargar_datos()

    # Frame medio para formularios
    frame_formulario = ttk.Frame(ventana_cuentas, padding=10)
    frame_formulario.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew")

    label_titular = ttk.Label(frame_formulario, text="Entidad Titular:")
    label_titular.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    titular_var = tk.StringVar()
    titular_var.trace_add("write", lambda *args: titular_var.set(titular_var.get().title()))
    entry_titular = ttk.Entry(frame_formulario, textvariable = titular_var, width=30)
    entry_titular.grid(row=0, column=1, padx=5, pady=5)
    
    label_llave = ttk.Label(frame_formulario, text="Llave:")
    label_llave.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    entry_llave = ttk.Entry(frame_formulario, width=30)
    entry_llave.grid(row=1, column=1, padx=5, pady=5)
    
    # Configurar estilo de los botones
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12, "bold"), padding=6, width=12)
    style.configure("BotonCrear.TButton", background="#4CAF50", foreground="black")
    style.configure("BotonLimpiar.TButton", background="#F44336", foreground="black")

    # Configurar el frame con un borde
    frame_botones = ttk.Frame(ventana_cuentas, relief="ridge", borderwidth=3)
    frame_botones.grid(row=2, column=0, columnspan=4, pady=10, padx=10, sticky="ew")

    btn_crear = ttk.Button(frame_botones, text="Crear", command= crear_cuenta, style="BotonCrear.TButton")
    btn_crear.grid(row=0, column=0, padx=10, pady=5)

    btn_eliminar = ttk.Button(frame_botones, text="Eliminar", command= eliminar_cuenta, style="BotonLimpiar.TButton")
    btn_eliminar.grid(row=0, column=1, padx=10, pady=5)


    # Expandir columnas
    ventana_cuentas.columnconfigure(0, weight=1)
    ventana_cuentas.rowconfigure(0, weight=1)

def mostrar_registros(entry_nombre, entry_fecha):
    nombre = entry_nombre.get().strip()
    #fecha_texto = entry_fecha.get().strip()

    # Validar que al menos el nombre esté presente
    if not nombre:
        messagebox.showerror("Error", "Debe ingresar un nombre.")
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
            cursor.execute("SELECT COALESCE(SUM(Saldos), 0) FROM registros WHERE Nombre = ?", (nombre,))
            saldos_ = cursor.fetchone()[0]
            
            
            
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

    # Definir el título sin incluir el mes
    titulo_texto = "Extracto pagos - Leo Motos"
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
    create_label(frame_info, "Cuotas en mora:", round(c_vencidas-c_saldas, 2), 2, 4)
    create_label(frame_info, "Pago ($) al dia:", al_dia_formateado, 3, 0)
    create_label(frame_info, "Total Otros:", saldos_, 3, 4)
    

    # Crear Treeview para mostrar los registros
    frame_tree = tk.Frame(ventana)
    frame_tree.pack(pady=10, padx=10, fill="both", expand=True)

    columnas = ("Mes", "Calendario", "Fecha_registro", "Valor", "Tipo", "Referencia", "Verificada")
    tree = ttk.Treeview(frame_tree, columns=columnas, show="headings", selectmode="browse")

    # Scrollbar vertical
    scroll_y = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)

    # Ubicar scrollbar y treeview
    scroll_y.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Definir encabezados
    for col in columnas:
        tree.heading(col, text=col)
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
        # Obtener el mes en formato corto (Ej: Diciembre -> Dic)
        mes_abreviado = fecha_pago.strftime("%b").capitalize()
        
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
        #tree.insert("", "end", values=(fecha_esperada_formateada, fecha_formateada, *registro[1:]), tags=(tag,))
        tree.insert("", "end", values=(mes_abreviado, fecha_esperada_formateada, fecha_formateada, *registro[1:]), tags=(tag,))

def ventana_propietario():
    # Crear ventana secundaria
    ventana_propietario = tk.Toplevel()
    ventana_propietario.title("Gestión de Propietarios")
    ventana_propietario.geometry("700x400")

    # Configurar el grid en la ventana principal
    ventana_propietario.columnconfigure(0, weight=1)
    ventana_propietario.rowconfigure(0, weight=1)
    ventana_propietario.rowconfigure(1, weight=0)
    ventana_propietario.rowconfigure(2, weight=0)
    
    def seleccionar_fila(event):
        # Obtener la fila seleccionada
        item = tree.selection()
        
        if item:
            valores = tree.item(item, "values")  # Obtener valores de la fila
            
            # Asignar los valores a las variables del formulario
            placa_var.set(valores[0])  # Placa
            modelo_var.set(valores[1])  # Modelo
            color_var.set(valores[2])
            tarjeta_var.set(valores[3])  # Tarjeta Propiedad

    def cargar_propietarios():
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()
        cursor.execute("SELECT Placa, Modelo, Color, Tarjeta_propiedad FROM propietario")
        registros = cursor.fetchall()

        tree.delete(*tree.get_children())  # Limpiar registros previos

        for registro in registros:
            tree.insert("", tk.END, values=registro)

        conn.close()
    
    def limpiar_campos():
        placa_var.set("")
        modelo_var.set("")
        color_var.set("")
        tarjeta_var.set("")

    def agregar_propietario():
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()
        
        placa = placa_var.get().strip()
        modelo = modelo_var.get().strip()
        color = color_var.get().strip()
        tarjeta = tarjeta_var.get().strip()

        # Verificar que todos los campos estén llenos
        if not placa or not modelo or not tarjeta:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            ventana_propietario.focus_force()
            return  # Salir de la función sin continuar

        # Verificar si la placa ya existe
        cursor.execute("SELECT COUNT(*) FROM propietario WHERE Placa = ?", (placa,))
        existe = cursor.fetchone()[0]

        if existe:
            messagebox.showerror("Error", f"La placa {placa} ya está registrada.")
            ventana_propietario.focus_force()
        else:
            cursor.execute("INSERT INTO propietario (Placa, Modelo, Color, Tarjeta_propiedad) VALUES (?, ?, ?, ?)",
                        (placa, modelo, color, tarjeta))
            conn.commit()
            messagebox.showinfo("Éxito", "Propietario agregado correctamente.")

        conn.close()
        cargar_propietarios()  # Refrescar la tabla
        limpiar_campos()

    def modificar_propietario():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione un propietario para modificar.")
            ventana_propietario.focus_force()
            return

        placa_nueva = placa_var.get().strip().upper()
        modelo_nuevo = modelo_var.get().strip().title()
        color_nuevo = color_var.get().strip().title()
        tarjeta_nueva = tarjeta_var.get().strip().title()

        if not placa_nueva or not modelo_nuevo or not tarjeta_nueva:
            messagebox.showwarning("Campos vacíos", "Todos los campos deben estar llenos.")
            ventana_propietario.focus_force()
            return

        item = tree.item(selected_item)
        placa_original = item["values"][0]  # Placa original del registro seleccionado

        try:
            conn = sqlite3.connect('diccionarios/base_dat.db')
            cursor = conn.cursor()

            # Verificar si la nueva placa ya existe en la base de datos y no es la original
            cursor.execute("SELECT COUNT(*) FROM propietario WHERE Placa=? AND Placa<>?", (placa_nueva, placa_original))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Error de duplicación", f"La placa '{placa_nueva}' ya existe en otro registro.")
                ventana_propietario.focus_force()
                return

            # Actualizar el registro
            cursor.execute("""
                UPDATE propietario 
                SET Placa=?, Modelo=?, Color=?, Tarjeta_propiedad=? 
                WHERE Placa=?
            """, (placa_nueva, modelo_nuevo, color_nuevo, tarjeta_nueva, placa_original))

            if cursor.rowcount == 0:
                messagebox.showerror("Error", "No se pudo actualizar el propietario. Verifique los datos.")
                ventana_propietario.focus_force()
            else:
                conn.commit()
                messagebox.showinfo("Éxito", "El propietario ha sido modificado correctamente.")
                ventana_propietario.focus_force()

                # Actualizar la vista en el Treeview
                tree.item(selected_item, values=(placa_nueva, modelo_nuevo, tarjeta_nueva))

        except sqlite3.Error as e:
            messagebox.showerror("Error de base de datos", f"Ocurrió un error: {e}")
            ventana_propietario.focus_force()

        finally:
            conn.close()

        cargar_propietarios()  # Refrescar la tabla
        limpiar_campos()

    # 🌟 FRAME PARA EL TREEVIEW
    frame_tree = ttk.Frame(ventana_propietario, padding=10)
    frame_tree.grid(row=0, column=0, sticky="nsew")

    columnas = ("Placa", "Modelo", "Color",  "Tarjeta Propiedad")
    tree = ttk.Treeview(frame_tree, columns=columnas, show="headings", height=8)

    # Encabezados del Treeview
    for col in columnas:
        tree.heading(col, text=col, anchor="center")
        tree.column(col, width=180, anchor="center")

    tree.grid(row=0, column=0, sticky="nsew")
    tree.bind("<Double-1>", seleccionar_fila)

    # Expandir el TreeView dentro del frame
    frame_tree.columnconfigure(0, weight=1)
    frame_tree.rowconfigure(0, weight=1)

    # 🌟 FRAME PARA FORMULARIO
    frame_form = ttk.Frame(ventana_propietario, padding=10, borderwidth=2, relief="solid")
    frame_form.grid(row=1, column=0, sticky="ew")

    # Crear campos del formulario en línea horizontal
    placa_var = tk.StringVar()
    placa_var.trace_add("write", lambda *args: placa_var.set(placa_var.get().upper()))
    ttk.Label(frame_form, text="Placa:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_placa = ttk.Entry(frame_form, textvariable=placa_var, width=15)
    entry_placa.grid(row=0, column=1, padx=5, pady=5)

    modelo_var = tk.StringVar()
    modelo_var.trace_add("write", lambda *args: modelo_var.set(modelo_var.get().title()))
    ttk.Label(frame_form, text="Modelo:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    entry_modelo = ttk.Entry(frame_form, textvariable=modelo_var, width=30)
    entry_modelo.grid(row=0, column=3, padx=5, pady=5)
    
    color_var = tk.StringVar()
    color_var.trace_add("write", lambda *args: color_var.set(color_var.get().title()))
    ttk.Label(frame_form, text="Color:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_color = ttk.Entry(frame_form, textvariable=color_var, width=15)
    entry_color.grid(row=1, column=1, padx=5, pady=5)
    

    tarjeta_var = tk.StringVar()
    tarjeta_var.trace_add("write", lambda *args: tarjeta_var.set(tarjeta_var.get().title()))
    ttk.Label(frame_form, text="Tarjeta Propiedad:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    entry_tarjeta = ttk.Entry(frame_form, textvariable=tarjeta_var, width=30)
    entry_tarjeta.grid(row=1, column=3, padx=5, pady=5)

    # 🌟 FRAME PARA BOTONES
    
    # Configurar el frame con un borde
    frame_buttons = ttk.Frame(ventana_propietario, relief="ridge", borderwidth=3)
    frame_buttons.grid(row=2, column=0, columnspan=4, pady=10, padx=10, sticky="ew")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12, "bold"), padding=6, width=12)
    style.configure("BotonCrear.TButton", background="#4CAF50", foreground="black")
    style.configure("BotonModificar.TButton", background="#FFC107", foreground="black")
    style.configure("BotonLimpiar.TButton", background="#F44336", foreground="black")

    # Botones con funcionalidades
    btn_crear = ttk.Button(frame_buttons, text="Crear", command= agregar_propietario, style="BotonCrear.TButton")
    btn_crear.grid(row=0, column=0, padx=10, pady=5)

    btn_modificar = ttk.Button(frame_buttons, text="Modificar", command= modificar_propietario, style="BotonModificar.TButton")
    btn_modificar.grid(row=0, column=1, padx=10, pady=5)

    btn_limpiar = ttk.Button(frame_buttons, text="Limpiar", command= limpiar_campos, style="BotonLimpiar.TButton")
    btn_limpiar.grid(row=0, column=2, padx=10, pady=5)

    # Expandir columnas en el frame de botones
    frame_buttons.columnconfigure((0, 1, 2), weight=1)
    
    cargar_propietarios()
    
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

def arqueo():

    # Función para obtener los datos y llenar el treeview
    def generar_reporte():
        fecha_seleccionada = entry_fecha.get()
        
        if not fecha_seleccionada:
            return
        
        # Limpiar treeview antes de insertar nuevos datos
        for item in tree.get_children():
            tree.delete(item)

        conexion = sqlite3.connect("diccionarios/base_dat.db")
        cursor = conexion.cursor()

        # Obtener todos los valores de Nombre_cuenta en la tabla cuentas
        cursor.execute("SELECT DISTINCT Nombre_cuenta FROM cuentas")
        cuentas = cursor.fetchall()

        total_dia = 0  # Variable para calcular la sumatoria total

        for cuenta in cuentas:
            nombre_cuenta = cuenta[0]

            # Sumar el campo Valor de la tabla registros para la fecha seleccionada y la cuenta actual
            cursor.execute("""
                SELECT SUM(Valor) FROM registros
                WHERE Fecha_sistema = ? AND Nombre_cuenta = ?
            """, (fecha_seleccionada, nombre_cuenta))
            
            sumatoria = cursor.fetchone()[0]
            sumatoria = sumatoria if sumatoria else 0  # Si no hay registros, poner 0

            total_dia += sumatoria  # Sumar al total del día

            # Insertar en el treeview
            tree.insert("", "end", values=(fecha_seleccionada, nombre_cuenta, sumatoria))

        # Obtener la sumatoria total de los registros donde Tipo = 'Efectivo' para la fecha seleccionada
        cursor.execute("""
            SELECT SUM(Valor) FROM registros
            WHERE Fecha_sistema = ? AND Tipo = 'Efectivo'
        """, (fecha_seleccionada,))
        
        total_efectivo = cursor.fetchone()[0]
        total_efectivo = total_efectivo if total_efectivo else 0

        # Insertar dos filas en blanco
        tree.insert("", "end", values=("", "", ""))
        tree.insert("", "end", values=("", "", ""))

        # Insertar la fila Total Efectivo con estilo resaltado
        tree.insert("", "end", values=(fecha_seleccionada, "TOTAL EFECTIVO", total_efectivo), tags=("total",))

        # Insertar la fila TOTAL DÍA con estilo resaltado
        tree.insert("", "end", values=(fecha_seleccionada, "TOTAL DÍA", total_dia), tags=("total",))

        conexion.close()

    # Crear ventana principal
    root = tk.Toplevel()
    root.title("Reporte de Valores")
    root.geometry("600x400")

    # Frame para el selector de fecha y botón
    frame_superior = tk.Frame(root)
    frame_superior.pack(pady=10)

    # Entry para ingresar la fecha
    tk.Label(frame_superior, text="Fecha:").pack(side=tk.LEFT, padx=5)
    entry_fecha = tk.Entry(frame_superior, width=15)
    entry_fecha.pack(side=tk.LEFT, padx=5)

    # Botón para generar el reporte
    btn_reporte = tk.Button(frame_superior, text="Reporte de valores", command=generar_reporte)
    btn_reporte.pack(side=tk.LEFT, padx=5)

    # Treeview para mostrar los datos
    tree = ttk.Treeview(root, columns=("Fecha", "Cuenta", "Sumatoria"), show="headings")
    tree.heading("Fecha", text="Fecha")
    tree.heading("Cuenta", text="Cuenta")
    tree.heading("Sumatoria", text="Sumatoria")

    # Configurar ancho y alineación de columnas (centrado)
    tree.column("Fecha", width=100, anchor="center")
    tree.column("Cuenta", width=250, anchor="center")
    tree.column("Sumatoria", width=100, anchor="center")

    # Agregar scrollbar
    scroll_y = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    # Estilos para resaltar la última fila (TOTAL EFECTIVO y TOTAL DÍA)
    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 10))  # Fuente normal
    style.configure("Total.Treeview", font=("Arial", 10, "bold"), background="#d9d9d9")  # Resaltar filas finales

    # Aplicar el estilo a las filas de TOTAL EFECTIVO y TOTAL DÍA
    tree.tag_configure("total", font=("Arial", 10, "bold"), background="#d9d9d9")

def ui_atrasos():

    # Conexión a la base de datos
    def conectar_db():
        conn = sqlite3.connect('diccionarios/base_dat.db')
        return conn

    # Cargar datos de la tabla 'registros' y 'clientes'
    def cargar_datos():
        conn = conectar_db()
        registros = pd.read_sql_query("SELECT * FROM registros", conn)
        clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
        conn.close()
        return registros, clientes

    # Cálculo de atraso por placa
    def calcular_atraso(registros, clientes):
        # Obtenemos la fecha actual
        fecha_actual = datetime.now()

        # Crear un diccionario para almacenar el atraso por placa
        atraso_por_placa = []

        # Iteramos por cada cliente
        for _, cliente in clientes.iterrows():
            # Datos del cliente
            cedula = cliente['Cedula']
            nombre = cliente['Nombre']  # Nombre del cliente
            fecha_inicio = datetime.strptime(cliente['Fecha_inicio'], '%Y-%m-%d')
            valor_cuota = cliente['Valor_cuota']

            # Calculamos los días transcurridos
            dias_transcurridos = (fecha_actual - fecha_inicio).days

            # Total de lo que debería haberse pagado hasta la fecha
            monto_adeudado = dias_transcurridos * valor_cuota

            # Filtramos los registros de pagos para este cliente (por cédula)
            pagos_cliente = registros[registros['Cedula'] == cedula]

            # Sumamos los pagos realizados
            total_pagado = pagos_cliente['Valor'].sum()

            # Calculamos los días cubiertos por los pagos
            dias_cubiertos = total_pagado / valor_cuota

            # Calculamos los días de atraso (restando los días cubiertos)
            dias_atraso = dias_transcurridos - dias_cubiertos

            # Calculamos el atraso
            atraso = monto_adeudado - total_pagado

            # Si hay atraso, lo registramos
            if atraso > 0 and dias_atraso > 0:  # Solo si hay atraso y días de atraso positivos
                placa = pagos_cliente.iloc[0]['Placa']  # Usamos la placa del primer registro de pago
                atraso_por_placa.append((placa, nombre, round(dias_transcurridos, 1), round(dias_atraso, 1), round(atraso, 2)))

        # Ordenamos los datos por "Días de Atraso" de mayor a menor
        atraso_por_placa.sort(key=lambda x: x[3], reverse=True)

        return atraso_por_placa

    # Crear la interfaz gráfica para mostrar los datos

    registros, clientes = cargar_datos()
    atraso_por_placa = calcular_atraso(registros, clientes)

    # Crear la ventana principal
    root = tk.Toplevel()
    root.title("Reporte de Atrasos de Pagos")

    # Configurar el redimensionamiento de la ventana
    root.grid_rowconfigure(0, weight=1)  # La fila 0 (donde está el Treeview) se redimensionará
    root.grid_columnconfigure(0, weight=1)  # La columna 0 (donde está el Treeview) se redimensionará

    # Crear un Treeview para mostrar los datos
    tree = ttk.Treeview(root, columns=("Placa", "Nombre", "Días Transcurridos", "Días de Atraso", "Valor Atraso"), show="headings")
    tree.heading("Placa", text="Placa")
    tree.heading("Nombre", text="Nombre")
    tree.heading("Días Transcurridos", text="Días Transcurridos")
    tree.heading("Días de Atraso", text="Días de Atraso")
    tree.heading("Valor Atraso", text="Valor Atraso")

    # Centrar el texto en todas las columnas
    tree.column("Placa", anchor="center")
    tree.column("Nombre", anchor="center")
    tree.column("Días Transcurridos", anchor="center")
    tree.column("Días de Atraso", anchor="center")
    tree.column("Valor Atraso", anchor="center")

    for atraso in atraso_por_placa:
        # Formateamos el monto con COP y los días con un solo decimal
        monto_formateado = f"{atraso[4]:,.2f} COP"
        tree.insert("", "end", values=(atraso[0], atraso[1], atraso[2], atraso[3], monto_formateado))

    # Colocar el Treeview en la ventana usando grid
    tree.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")


