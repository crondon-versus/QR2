# config.py

# URL del formulario de Google
FORM_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSdxLgFfT6kwZvuuK_OE32iLuyvyOodeUQI5Bvu2-60YlGWRrA/viewform"
)

# Ruta por defecto del logo
DEFAULT_LOGO_PATH = "assets/logo.jpg"

# Carpeta de salida
OUTPUT_DIR = "output"

# Tamaño del QR (cada "box" es un píxel de módulo)
BOX_SIZE = 10
BORDER = 4

# Proporción del logo respecto al ancho del QR (0.2 = 20%)
LOGO_SCALE = 0.22

# Formato de salida por defecto: "jpg" o "pdf"
DEFAULT_OUTPUT_FORMAT = "jpg"
