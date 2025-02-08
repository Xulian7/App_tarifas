import os
import json
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import messagebox

db_path = "diccionarios/base_dat.db"
users_path = "diccionarios/usuarios.json"
excel_path = "diccionarios/baseExcel.xlsx"

# Ventana de autenticación
def pedir_contraseña():
    auth_window = tk.Tk()  # Crear la ventana principal para la autenticación
    auth_window.title("Autenticación")
    auth_window.geometry("400x200")
    auth_window.resizable(False, False)

    tk.Label(auth_window, text="Ingrese la contraseña de Dev:", font=("Arial", 12)).pack(pady=10)

    entrada = tk.Entry(auth_window, show="*", font=("Arial", 14), width=25)
    entrada.pack(pady=5)

    resultado = tk.StringVar()

    def confirmar():
        resultado.set(entrada.get())
        auth_window.destroy()

    tk.Button(auth_window, text="Aceptar", font=("Arial", 12), command=confirmar).pack(pady=10)

    auth_window.mainloop()  # Mantener la ventana abierta hasta que se cierre
    
    return resultado.get()

# Función para validar la contraseña
def validar_credenciales():
    if not os.path.exists(users_path):
        messagebox.showerror("Error", "El archivo de usuarios no existe.")
        return False

    with open(users_path, "r") as file:
        usuarios = json.load(file)

    password_correcta = usuarios.get("Dev")

    if not password_correcta:
        messagebox.showerror("Error", "Usuario 'Dev' no encontrado en el archivo.")
        return False

    intentos = 3
    while intentos > 0:
        password_ingresada = pedir_contraseña()
        if password_ingresada == password_correcta:
            return True
        else:
            messagebox.showerror("Error", f"Contraseña incorrecta. Intentos restantes: {intentos - 1}")
            intentos -= 1

    return False

def create_database():
    try:
        db_exists = os.path.exists(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if not db_exists:
            messagebox.showinfo("Éxito", "Base de datos creada correctamente.")

        cursor.execute("PRAGMA foreign_keys = ON;")

        tables = {
            "clientes": """
                CREATE TABLE IF NOT EXISTS clientes (
                    Cedula TEXT PRIMARY KEY,
                    Nombre TEXT,
                    Telefono TEXT,
                    Direccion TEXT,
                    Placa TEXT UNIQUE,
                    Fecha_inicio TEXT,
                    Fecha_final TEXT,
                    Tipo_contrato TEXT,
                    Capital REAL,
                    Valor_cuota REAL
                )
            """,
            "registros": """
                CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Fecha_sistema TEXT,
                    Fecha_registro TEXT,
                    Cedula TEXT,
                    Nombre TEXT,
                    Placa TEXT,
                    Valor REAL,
                    Tipo TEXT,
                    Nombre_cuenta TEXT,
                    Referencia TEXT,
                    Verificada TEXT,
                    FOREIGN KEY (Cedula) REFERENCES clientes(Cedula),
                    FOREIGN KEY (Placa) REFERENCES clientes(Placa)
                )
            """,
            "cuentas": """
                CREATE TABLE IF NOT EXISTS cuentas (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Titular TEXT,
                    Entidad TEXT
                )
            """,
            "asociados": """
                CREATE TABLE IF NOT EXISTS asociados (
                    Cedula_asoc TEXT PRIMARY KEY,
                    Nombre_asoc TEXT,
                    Placa TEXT,
                    FOREIGN KEY (Placa) REFERENCES clientes(Placa)
                )
            """
        }

        for table_name, query in tables.items():
            cursor.execute(query)

        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "Tablas creadas correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")
        
        
def migrar_clientes():
    try:
        if not os.path.exists(excel_path):
            messagebox.showerror("Error", "El archivo de Excel no existe.")
            return

        # Leer el archivo de Excel
        df = pd.read_excel(excel_path, sheet_name="clientes", dtype=str)

        # Definir las columnas esperadas en la base de datos
        columnas_db = [
            "Cedula", "Nombre", "Telefono", "Direccion", "Placa",
            "Fecha_inicio", "Fecha_final", "Tipo_contrato", "Capital", "Valor_cuota"
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
                    INSERT INTO clientes (Cedula, Nombre, Telefono, Direccion, Placa, Fecha_inicio, Fecha_final, Tipo_contrato, Capital, Valor_cuota)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
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
            "Valor", "Tipo", "Nombre_cuenta", "Referencia", "Verificada"
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
            Valor, Tipo, Nombre_cuenta, Referencia, Verificada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        columnas_requeridas = ["Titular", "Entidad"]
        
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
        INSERT INTO cuentas (Titular, Entidad) VALUES (?, ?)
        """
        cursor.executemany(query, df.values.tolist())
        
        # Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Las cuentas han sido migradas correctamente.")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema durante la migración: {e}")
        
        
def migrar_asociados():
    try:
        df = pd.read_excel(excel_path, sheet_name='asociados')
        conn = sqlite3.connect(db_path)
        df.to_sql('asociados', conn, if_exists='append', index=False)
        conn.close()
        messagebox.showinfo("Éxito", "Datos migrados correctamente a la tabla asociados.")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al migrar los datos: {e}")


# Validar credenciales antes de abrir la interfaz
if validar_credenciales():
    root = tk.Tk()
    root.title("Gestión de Base de Datos")
    root.geometry("600x400")
    root.configure(bg="#f0f0f0")  # Fondo gris claro

    # Configuración del grid
    root.columnconfigure(0, weight=1)

    # Estilo de los botones
    btn_style = {"font": ("Arial", 12), "width": 25, "height": 2, "bg": "#007BFF", "fg": "white"}

    # Botones de creación de tablas
    tk.Button(root, text="Crear Base de Datos", command=create_database, **btn_style).grid(row=0, column=0, padx=10, pady=5)

    # Botones de migración de datos
    tk.Button(root, text="Migrar Clientes", command=migrar_clientes, **btn_style).grid(row=1, column=0, padx=10, pady=5)
    tk.Button(root, text="Migrar Registros", command=migrar_registros, **btn_style).grid(row=2, column=0, padx=10, pady=5)
    tk.Button(root, text="Migrar Cuentas", command=migrar_cuentas, **btn_style).grid(row=3, column=0, padx=10, pady=5)
    tk.Button(root, text="Migrar asociados", command=migrar_asociados, **btn_style).grid(row=4, column=0, padx=10, pady=5)

    root.mainloop()
else:
    messagebox.showerror("Error", "Acceso denegado. No se pudo autenticar al usuario.")
