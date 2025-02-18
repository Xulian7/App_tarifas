import os
import json
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

imagenes = {} 
db_path = "diccionarios/base_dat.db"
users_path = "diccionarios/usuarios.json"
excel_path = "diccionarios/baseExcel.xlsx"

def create_database():
    try:
        # Verificar si la base de datos ya existe antes de crear la conexión
        db_exists = os.path.exists(db_path)

        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Habilitar claves foráneas
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Si la base de datos no existía, mostrar mensaje
        if not db_exists:
            messagebox.showinfo("Éxito", "Base de datos creada correctamente.")

        # Diccionario con las tablas a crear
        tables = {
            "propietario": """
                CREATE TABLE IF NOT EXISTS propietario (
                    Placa TEXT PRIMARY KEY,
                    Modelo TEXT,
                    Color TEXT,
                    Tarjeta_propiedad TEXT
                )
            """,
            "clientes": """
                CREATE TABLE IF NOT EXISTS clientes (
                    Cedula TEXT PRIMARY KEY,
                    Nombre TEXT NOT NULL,
                    Nacionalidad TEXT,
                    Telefono TEXT,
                    Direccion TEXT,
                    Placa TEXT,
                    Fecha_inicio TEXT NOT NULL,
                    Fecha_final TEXT NOT NULL,
                    Tipo_contrato TEXT NOT NULL,
                    Valor_cuota REAL CHECK(Valor_cuota >= 0),
                    Estado TEXT,
                    FOREIGN KEY (Placa) REFERENCES propietario(Placa) ON DELETE SET NULL
                )
            """,
            "registros": """
                CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Fecha_sistema TEXT NOT NULL,
                    Fecha_registro TEXT NOT NULL,
                    Cedula TEXT NOT NULL,
                    Nombre TEXT NOT NULL,
                    Placa TEXT,
                    Valor REAL CHECK(Valor >= 0),
                    Saldos REAL CHECK(Valor >= 0),
                    Tipo TEXT NOT NULL,
                    Nombre_cuenta TEXT,
                    Referencia TEXT,
                    Verificada TEXT,
                    FOREIGN KEY (Cedula) REFERENCES clientes(Cedula) ON DELETE CASCADE,
                    FOREIGN KEY (Placa) REFERENCES propietario(Placa) ON DELETE SET NULL
                )
            """,
            "cuentas": """
                CREATE TABLE IF NOT EXISTS cuentas (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre_cuenta TEXT,
                    Llave Text
                )
            """
        }

        # Ejecutar la creación de las tablas
        for query in tables.values():
            cursor.execute(query)

        # Confirmar cambios
        conn.commit()
        conn.close()

        # Mensaje de éxito
        messagebox.showinfo("Éxito", "Tablas creadas correctamente.")

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error al crear la base de datos: {e}")

def migrar_clientes():
    try:
        if not os.path.exists(excel_path):
            messagebox.showerror("Error", "El archivo de Excel no existe.")
            return

        # Leer el archivo de Excel
        df = pd.read_excel(excel_path, sheet_name="clientes", dtype=str)

        # Definir las columnas esperadas en la base de datos
        columnas_db = [
            "Cedula", "Nombre", "Nacionalidad", "Telefono", "Direccion", "Placa", "Fecha_inicio", "Fecha_final", "Tipo_contrato", "Valor_cuota", "Estado"
        ]

        # Validar que las columnas en Excel coincidan con las esperadas
        if not all(col in df.columns for col in columnas_db):
            messagebox.showerror("Error", "Las columnas del archivo Excel no coinciden con la base de datos.")
            return

        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insertar cada fila en la base de datos
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO clientes (Cedula, Nombre, Nacionalidad, Telefono, Direccion, Placa, Fecha_inicio, Fecha_final, Tipo_contrato, Valor_cuota, Estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, tuple(row[column] for column in columnas_db))
            except sqlite3.IntegrityError as e:
                messagebox.showwarning("Advertencia", f"No se pudo insertar el cliente {row['Cedula']} (Duplicado o error en datos): {e}")

        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "Clientes migrados correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al migrar clientes: {e}")

def migrar_registros():
    try:
        # Verificar si el archivo existe
        if not os.path.exists(excel_path):
            messagebox.showerror("Error", f"El archivo {excel_path} no existe.")
            return
        
        # Cargar el Excel y la hoja "registros"
        df = pd.read_excel(excel_path, sheet_name="registros", dtype=str)
        
        # Definir las columnas requeridas
        columnas_requeridas = [
            "Fecha_sistema", "Fecha_registro", "Cedula", "Nombre", "Placa", 
            "Valor", "Saldos", "Tipo", "Nombre_cuenta", "Referencia", "Verificada"
        ]
        
        # Validar que las columnas del Excel coincidan
        if list(df.columns) != columnas_requeridas:
            messagebox.showerror("Error", "Las columnas del Excel no coinciden con las requeridas.")
            return
        
        # Validar que las columnas obligatorias (excepto 'Referencia' y 'Nombre_cuenta') no tengan valores vacíos
        obligatorias = [col for col in columnas_requeridas if col not in ["Referencia", "Nombre_cuenta"]]
        if df[obligatorias].isnull().any().any():
            messagebox.showerror("Error", "Hay campos obligatorios vacíos en el archivo de Excel.")
            return
        
    
        # Reemplazar valores NaN en 'Referencia' y 'Nombre_cuenta' con None (para SQLite)
        df["Referencia"] = df["Referencia"].where(pd.notna(df["Referencia"]), None)
        df["Nombre_cuenta"] = df["Nombre_cuenta"].where(pd.notna(df["Nombre_cuenta"]), None)

        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insertar los datos en la tabla 'registros'
        query = """
        INSERT INTO registros (
            Fecha_sistema, Fecha_registro, Cedula, Nombre, Placa, 
            Valor, Saldos, Tipo, Nombre_cuenta, Referencia, Verificada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.executemany(query, df.values.tolist())
        
        # Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Los registros han sido migrados correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema durante la migración: {e}")

def migrar_cuentas():
    try:
        # Verificar si el archivo existe
        if not os.path.exists(excel_path):
            messagebox.showerror("Error", f"El archivo {excel_path} no existe.")
            return
        
        # Cargar el Excel y la hoja "cuentas"
        df = pd.read_excel(excel_path, sheet_name="cuentas", dtype=str)
        
        # Definir las columnas requeridas
        columnas_requeridas = ["Nombre cuenta", "Llave"]
        
        # Validar que las columnas del Excel coincidan
        if list(df.columns) != columnas_requeridas:
            messagebox.showerror("Error", "Las columnas del Excel no coinciden con las requeridas.")
            return
        
        # Validar que las columnas no tengan valores vacíos
        if df.isnull().any().any():
            messagebox.showerror("Error", "Existen campos vacíos en el archivo de Excel.")
            return
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insertar los datos en la tabla 'cuentas'
        query = """
        INSERT INTO cuentas (Nombre_cuenta, Llave) VALUES (?, ?)
        """
        cursor.executemany(query, df.values.tolist())
        
        # Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Las cuentas han sido migradas correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema durante la migración: {e}")
        
def migrar_propietarios():
    try:
        # Verificar si el archivo existe
        if not os.path.exists(excel_path):
            messagebox.showerror("Error", f"El archivo {excel_path} no existe.")
            return
        
        # Cargar el Excel y la hoja "cuentas"
        df = pd.read_excel(excel_path, sheet_name="propietario", dtype=str)
        
        # Definir las columnas requeridas
        columnas_requeridas = ["Placa", "Modelo","Color", "Tarjeta_propiedad"]
        
        # Validar que las columnas del Excel coincidan
        if list(df.columns) != columnas_requeridas:
            messagebox.showerror("Error", "Las columnas del Excel no coinciden con las requeridas.")
            return
        
        # Validar que las columnas no tengan valores vacíos
        if df.isnull().any().any():
            messagebox.showerror("Error", "Existen campos vacíos en el archivo de Excel.")
            return
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insertar los datos en la tabla 'cuentas'
        query = """
        INSERT INTO propietario (Placa, Modelo, Color, Tarjeta_propiedad) VALUES (?, ?, ?, ?)
        """
        cursor.executemany(query, df.values.tolist())
        
        # Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Las cuentas han sido migradas correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema durante la migración: {e}")    

def cargar_imagen(nombre):
        imagen = Image.open(f"img/{nombre}.png")
        imagen = imagen.resize((48, 48), Image.Resampling.LANCZOS)
        imagen_tk = ImageTk.PhotoImage(imagen)
        imagenes[nombre] = imagen_tk
        return imagen_tk
    
def on_enter(event):
    """Cambia el color del botón al pasar el mouse."""
    event.widget.config(bg="#004080")

def on_leave(event):
    """Restaura el color original al salir el mouse."""
    event.widget.config(bg="#0056b3")

# Inicializar ventana
root = tk.Tk()
root.title("Gestión de Base de Datos")
root.geometry("750x550")
root.configure(bg="#f0f0f0")

# Configurar el grid de la ventana principal
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Frame contenedor para centrar botones
frame_botones = tk.Frame(root, bg="#f0f0f0", bd=2, relief="solid")
frame_botones.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
frame_botones.pack_propagate(False)  # Evita que el frame cambie de tamaño por su contenido


# Estilo de los botones
btn_style = {
    "font": ("Arial", 14, "bold"),
    #"width": 28,  # Ajuste de ancho del botón
    #"height": 10,  # Ajuste de altura del botón
    "bg": "#0056b3",
    "fg": "white",
    "bd": 2,
    "compound": "left",  # Imagen a la izquierda del texto
    "anchor": "w",  # Alinear el texto a la izquierda
    "padx": 10,  # Espacio entre imagen y texto
    "pady": 10  # Espaciado interno
}

# Crear botones uno por uno

btn_db = tk.Button(frame_botones, text="  Crear Base de Datos", image=cargar_imagen("database"), command=create_database, **btn_style)
btn_db.grid(row=0, column=0, padx=30, pady=10, sticky="ew")
btn_db.bind("<Enter>", on_enter)
btn_db.bind("<Leave>", on_leave)

btn_clientes = tk.Button(frame_botones, text="  Migrar Clientes", image=cargar_imagen("clients"), command=migrar_clientes, **btn_style)
btn_clientes.grid(row=1, column=0, padx=30, pady=10, sticky="ew")
btn_clientes.bind("<Enter>", on_enter)
btn_clientes.bind("<Leave>", on_leave)

btn_registros = tk.Button(frame_botones, text="  Migrar Registros", image=cargar_imagen("records"), command=migrar_registros, **btn_style)
btn_registros.grid(row=2, column=0, padx=30, pady=10, sticky="ew")
btn_registros.bind("<Enter>", on_enter)
btn_registros.bind("<Leave>", on_leave)


btn_cuentas = tk.Button(frame_botones, text="  Migrar Cuentas", image=cargar_imagen("accounts"), command=migrar_cuentas, **btn_style)
btn_cuentas.grid(row=3, column=0, padx=30, pady=10, sticky="ew")
btn_cuentas.bind("<Enter>", on_enter)
btn_cuentas.bind("<Leave>", on_leave)

btn_asociados = tk.Button(frame_botones, text="  Migrar Asociados", image=cargar_imagen("associates"), command=migrar_propietarios, **btn_style)
btn_asociados.grid(row=4, column=0, padx=30, pady=10, sticky="ew")
btn_asociados.bind("<Enter>", on_enter)
btn_asociados.bind("<Leave>", on_leave)


root.mainloop()


