# image_editor.py
import tkinter as tk
from tkinter import Label, Text, Scrollbar
from PIL import Image, ImageTk, ImageGrab, ImageEnhance
import pyperclip
import pytesseract
import os

# Configura la ruta de Tesseract (si es necesario)
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Ruta donde se encuentra tesseract.exe
tesseract_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tesseract.exe')

# Configurar Tesseract con la ruta correcta
pytesseract.pytesseract.tesseract_cmd = tesseract_path



class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pegar Imagen y Filtrar")

        # Crear área para mostrar imagen
        self.label = Label(root, text="Presiona Ctrl+V para pegar una imagen")
        self.label.pack(pady=10)

        # Botón para aplicar filtro
        self.filter_button = tk.Button(root, text="Aplicar filtro", command=self.apply_filter, state=tk.DISABLED)
        self.filter_button.pack(pady=5)

        # Botón para extraer texto con OCR
        self.ocr_button = tk.Button(root, text="Extraer Texto", command=self.extract_text, state=tk.DISABLED)
        self.ocr_button.pack(pady=5)

        # Área de texto para mostrar OCR
        self.text_area = Text(root, height=10, width=50, wrap="word")
        self.text_area.pack(pady=10)
        
        # Agregar Scrollbar
        scrollbar = Scrollbar(root, command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)

        # Capturar evento de Ctrl + V
        root.bind("<Control-v>", self.paste_image)

        self.image = None  # Almacenar imagen pegada

    def paste_image(self, event=None):
        """Pega la imagen del portapapeles en la UI"""
        img = ImageGrab.grabclipboard()  # Obtener imagen del portapapeles

        if img:
            self.image = img.convert("RGB")  # Convertir imagen a RGB
            self.display_image(self.image)
            self.filter_button.config(state=tk.NORMAL)  # Habilitar botón de filtro
        else:
            self.label.config(text="No hay imagen en el portapapeles")

    def display_image(self, img):
        """Muestra la imagen en el Label"""
        img.thumbnail((400, 400))  # Ajustar tamaño
        self.tk_image = ImageTk.PhotoImage(img)
        self.label.config(image=self.tk_image, text="")  # Mostrar imagen
        self.ocr_button.config(state=tk.NORMAL)  # Habilitar OCR cuando hay imagen

    def apply_filter(self):
        """Aplica un filtro para eliminar colores claros"""
        if self.image:
            enhancer = ImageEnhance.Contrast(self.image)
            self.image = enhancer.enhance(2)  # Aumentar contraste
            self.display_image(self.image)

    def extract_text(self):
        """Ejecuta OCR en la imagen y muestra el texto extraído"""
        if self.image:
            text = pytesseract.image_to_string(self.image, lang="spa")  # Detectar texto en español
            self.text_area.delete("1.0", tk.END)  # Limpiar el área de texto
            self.text_area.insert(tk.END, text)  # Mostrar texto extraído

# Esta es la función que se llama desde main_app.py
def open_image_editor():
    editor_window = tk.Toplevel()  # Crea una nueva ventana
    app = ImageEditorApp(editor_window)
    editor_window.mainloop()


