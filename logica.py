import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import os
from datetime import datetime
import pandas as pd

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
        query = "SELECT Fecha_sistema, Fecha_registro, Cedula, Nombre, Placa, Valor, Tipo, Nombre_cuenta, Referencia, Verificada FROM registros WHERE 1=1"

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
        rows.sort(key=lambda x: str(x[2]))  # Ordena por el valor de la columna Cedula (índice 2)

        # Insertar las filas en el Treeview
        for row in rows:
            # Formatear las fechas correctamente
            fecha_sistema = pd.to_datetime(row[0]).strftime('%d-%m-%Y')
            fecha_registro = pd.to_datetime(row[1]).strftime('%d-%m-%Y')

            # Crear una lista con los valores modificados
            values = list(row)
            values[0] = fecha_sistema
            values[1] = fecha_registro

            # Aplicar sombreado si "Verificada" es "No"
            tags = ("sombreado",) if row[9] == "No" else ()
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
    # Crear una nueva ventana para la gestión de Cuentas
    ventana_cuentas = tk.Toplevel()
    ventana_cuentas.title("Gestión de Cuentas")
    ventana_cuentas.geometry("600x400")
    icono_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'inicio.ico')

    # Crear el Treeview
    tree = ttk.Treeview(ventana_cuentas, columns=("ID","Titular", "Entidad"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Titular", text="Titular")
    tree.heading("Entidad", text="Entidad")
    tree.pack(fill=tk.BOTH, expand=True)
    # Configurar el encabezado de las columnas para centrarlas
    tree.heading("ID", text="ID", anchor="center")
    tree.heading("Titular", text="Titular", anchor="center")
    tree.heading("Entidad", text="Entidad", anchor="center")
    # Configurar las celdas de los datos para centrarlas
    tree.column("ID", anchor="center")
    tree.column("Titular", anchor="center")
    tree.column("Entidad", anchor="center")

    # Crear los campos de entrada para Titular y Entidad
    label_titular = tk.Label(ventana_cuentas, text="Titular:")
    label_titular.pack()

    entry_titular = tk.Entry(ventana_cuentas)
    entry_titular.pack()

    label_entidad = tk.Label(ventana_cuentas, text="Entidad:")
    label_entidad.pack()

    entry_entidad = tk.Entry(ventana_cuentas)
    entry_entidad.pack()

    # Función para crear una nueva cuenta
    def crear_cuenta():
        # Obtener los valores de los campos de entrada
        titular_valor = entry_titular.get()
        entidad_valor = entry_entidad.get()

        # Validar que los campos no estén vacíos
        if not titular_valor or not entidad_valor:
            messagebox.showwarning("Advertencia", "Todos los campos deben ser completados")
            return  # No continuar si algún campo está vacío

        # Insertar el nuevo registro en el Treeview
        tree.insert("", "end", values=(titular_valor, entidad_valor))

        # Limpiar los campos de entrada después de crear la cuenta
        entry_titular.delete(0, tk.END)
        entry_entidad.delete(0, tk.END)

        # Guardar el nuevo registro en la base de datos
        try:
            conn = sqlite3.connect('diccionarios/base_dat.db')
            cursor = conn.cursor()
            
            # Insertar en la base de datos (no es necesario el campo ID ya que es autoincrementable)
            cursor.execute("INSERT INTO cuentas (Titular, Entidad) VALUES (?, ?)", 
                        (titular_valor, entidad_valor))
            conn.commit()  # Confirmar la inserción
            conn.close()

            messagebox.showinfo("Éxito", "Cuenta creada exitosamente")
            
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la cuenta en la base de datos: {e}")

    # Botón de Crear
    btn_crear = tk.Button(ventana_cuentas, text="Crear", command=crear_cuenta)
    btn_crear.pack(side=tk.LEFT, padx=10, pady=10)

    # Botón de Eliminar
    def eliminar_cuenta():
        # Obtener el item seleccionado en el Treeview
        selected_item = tree.selection()

        if not selected_item:
            messagebox.showwarning("Seleccionar registro", "Por favor, seleccione un registro para eliminar.")
            return
        
        # Obtener el ID del registro seleccionado
        item_values = tree.item(selected_item)["values"]
        id_cuenta = item_values[0]# El primer valor es el ID
        titular_c = item_values[1]

        # Confirmar la eliminación
        confirmacion = messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de eliminar el registro con ID: {id_cuenta} {titular_c}?")

        if confirmacion:
            try:
                conn = sqlite3.connect('diccionarios/base_dat.db')
                cursor = conn.cursor()

                # Eliminar el registro de la base de datos
                cursor.execute("DELETE FROM cuentas WHERE ID = ?", (id_cuenta,))
                conn.commit()

                # Cerrar la conexión
                conn.close()

                # Eliminar el registro del Treeview
                tree.delete(selected_item)

                # Mensaje de éxito
                messagebox.showinfo("Éxito", f"El registro con ID {id_cuenta} ha sido eliminado.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")

    btn_eliminar = tk.Button(ventana_cuentas, text="Eliminar", command=eliminar_cuenta)
    btn_eliminar.pack(side=tk.LEFT, padx=10, pady=10)

    try:
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()

        # Verificar si la tabla 'cuentas' existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cuentas';")
        if cursor.fetchone() is None:
            messagebox.showerror("Error", "La tabla 'Cuentas' no existe.")
            return

        # Obtener todos los registros de la tabla 'cuentas'
        cursor.execute("SELECT ID, Titular, Entidad FROM cuentas")
        rows = cursor.fetchall()

        if not rows:  # Si no hay registros en la tabla
            messagebox.showinfo("Información", "La tabla 'Cuentas' está vacía.")
        else:
            # Insertar los registros en el Treeview
            for row in rows:
                tree.insert("", "end", values=row)

        # Cerrar la conexión
        conn.close()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar los datos de la tabla 'Cuentas': {e}")


def obtener_datos_clientes():
    """Obtiene los datos de la tabla clientes desde la base de datos y formatea Capital y Fecha_inicio."""
    conexion = sqlite3.connect("diccionarios/base_dat.db")  # Cambia el nombre si es diferente
    cursor = conexion.cursor()
    
    query = "SELECT Cedula, Nombre, Telefono, Direccion, Placa, Fecha_inicio, Tipo_contrato, Capital, Valor_cuota FROM clientes"
    cursor.execute(query)
    datos = cursor.fetchall()
    
    conexion.close()

    # Formatear los datos
    datos_formateados = []
    for fila in datos:
        cedula, nombre, telefono, direccion, placa, fecha_inicio, tipo_contrato, capital, valor_cuota = fila
        
        # Formatear la fecha si existe
        if fecha_inicio:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                fecha_inicio = "Formato Inválido"  # En caso de error con la fecha
        
        # Formatear capital sin decimales
        capital = int(capital) if capital is not None else 0
        
        datos_formateados.append((cedula, nombre, telefono, direccion, placa, fecha_inicio, tipo_contrato, capital, valor_cuota))

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
    frame_tree.grid(row=0, column=0, columnspan=6, sticky="nsew", padx=10, pady=10)

    # Crear el Treeview dentro del Frame
    columnas = ("Cedula", "Nombre", "Telefono", "Direccion", 
                "Placa", "Fecha_inicio", "Tipo_contrato", 
                "Capital", "Valor_cuota")

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

    # Labels y Entries para la información del cliente
    labels_texts = ["Cédula:", "Nombre:", "Teléfono:", "Dirección:", 
                    "Placa:", "Fecha Inicio:", "Tipo Contrato:", 
                    "Capital:", "Valor Cuota:"]
    
    entries = {}
    for i, text in enumerate(labels_texts):
        lbl = ttk.Label(ventana_clientes, text=text)
        lbl.grid(row=i+1, column=0, padx=5, pady=5, sticky="e")
        
        entry = ttk.Entry(ventana_clientes)
        entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="w")
        
        entries[text] = entry  # Guardamos las entradas en un diccionario

    # Botón para cerrar la ventana
    btn_cerrar = ttk.Button(ventana_clientes, text="Cerrar", command=ventana_clientes.destroy)
    btn_cerrar.grid(row=len(labels_texts)+1, column=0, columnspan=2, pady=10)

    # Expansión de filas y columnas
    ventana_clientes.columnconfigure(1, weight=1)
    ventana_clientes.rowconfigure(0, weight=1)

    return ventana_clientes  # Si quieres capturar la ventana creada

# Código para probar la ventana de clientes de forma independiente
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ocultamos la ventana principal
    abrir_ventana_clientes()
    root.mainloop()




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
        
    
    
