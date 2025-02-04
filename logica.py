import pandas as pd
import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox
from tkinter import ttk
import sqlite3




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
    

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

def abrir_ventana_cuentas():
    # Crear una nueva ventana para la gestión de Cuentas
    ventana_cuentas = tk.Toplevel()
    ventana_cuentas.title("Gestión de Cuentas")
    ventana_cuentas.geometry("600x400")

    # Crear el Treeview
    tree = ttk.Treeview(ventana_cuentas, columns=("Titular", "Entidad"), show="headings")
    tree.heading("Titular", text="Titular")
    tree.heading("Entidad", text="Entidad")
    tree.pack(fill=tk.BOTH, expand=True)
    # Configurar el encabezado de las columnas para centrarlas
    tree.heading("Titular", text="Titular", anchor="center")
    tree.heading("Entidad", text="Entidad", anchor="center")
    # Configurar las celdas de los datos para centrarlas
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
            cursor.execute("INSERT INTO Cuentas (Titular, Entidad) VALUES (?, ?)", 
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
        id_cuenta = item_values[0]  # El primer valor es el ID

        # Confirmar la eliminación
        confirmacion = messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de eliminar el registro con ID: {id_cuenta}?")

        if confirmacion:
            try:
                conn = sqlite3.connect('diccionarios/base_dat.db')
                cursor = conn.cursor()

                # Eliminar el registro de la base de datos
                cursor.execute("DELETE FROM Cuentas WHERE ID = ?", (id_cuenta,))
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

    # Cargar los datos de la tabla 'Cuentas' en el Treeview
    try:
        conn = sqlite3.connect('diccionarios/base_dat.db')
        cursor = conn.cursor()

        # Obtener todos los registros de la tabla Cuentas
        cursor.execute("SELECT Titular, Entidad FROM Cuentas")
        rows = cursor.fetchall()

        # Insertar los registros en el Treeview
        for row in rows:
            tree.insert("", "end", values=row)

        # Cerrar la conexión
        conn.close()

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar los datos de la tabla 'Cuentas': {e}")


        
    
    
