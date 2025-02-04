import pandas as pd
import sqlite3

# Cargar el archivo Excel
df = pd.read_excel('diccionarios/registros_motos.xlsx')

# Convertir las columnas de fecha a formato string 'YYYY-MM-DD' si es necesario
df['Fecha_sistema'] = df['Fecha_sistema'].dt.strftime('%Y-%m-%d')
df['Fecha_registro'] = df['Fecha_registro'].dt.strftime('%Y-%m-%d')

# Conectar a la base de datos SQLite
conn = sqlite3.connect('diccionarios/base_dat.db')
cursor = conn.cursor()

# Crear una lista de tuplas con los datos del DataFrame (excluyendo la columna autoincremental)
data = df[['Fecha_sistema', 'Fecha_registro', 'Cedula', 'Nombre', 'Placa', 'Valor', 'Tipo', 'Nombre_cuenta', 'Referencia', 'Verificada']].values.tolist()

# Insertar los datos en la tabla 'registros'
cursor.executemany('''
    INSERT INTO registros (Fecha_sistema, Fecha_registro, Cedula, Nombre, Placa, Valor, Tipo, Nombre_cuenta, Referencia, Verificada)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', data)

# Confirmar la transacción
conn.commit()

# Cerrar la conexión
conn.close()

print("Los registros han sido cargados exitosamente.")




