import json

# Diccionario con las credenciales
usuarios = {
    "Admin": "1234",
    "Dev": "1234",
    "Oper": "1234"
}

# Guardar en un archivo JSON
with open("usuarios.json", "w") as file:
    json.dump(usuarios, file, indent=4)

print("Archivo 'usuarios.json' creado correctamente.")
