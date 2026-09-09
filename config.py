# config.py

# URL del formulario/destino
FORM_URL = (
    "https://guardiacivil.academiaprefortia.com/conoce-la-oposicion-a-guardia-civil/"
)

# Carpeta de salida
OUTPUT_DIR = "output"

# Tamaño del QR (cada "box" es un píxel de módulo)
BOX_SIZE = 10
BORDER = 4

# Formato de salida por defecto: "jpg" o "pdf"
DEFAULT_OUTPUT_FORMAT = "jpg"

# Logo por defecto: ninguno, a proposito.
#
# Antes esto apuntaba a assets/logo.webp, un archivo que no existe, y main.py se
# lo tragaba en silencio: imprimia "Generando codigo QR con logo..." y producia un
# codigo sin logo, sin un solo aviso. Y como el grupo tiene seis academias, poner
# una de ellas por defecto arriesga mandar a imprenta el logo equivocado.
#
# Ahora el logo se indica en cada ejecucion con --logo, y si falta, main.py se
# para y lista las imagenes que hay en assets/.
LOGO_PATH = None