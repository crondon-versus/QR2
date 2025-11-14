# main.py

import os
import argparse

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image

from config import (
    FORM_URL,
    DEFAULT_LOGO_PATH,
    OUTPUT_DIR,
    BOX_SIZE,
    BORDER,
    LOGO_SCALE,
    DEFAULT_OUTPUT_FORMAT,
)


def ensure_output_dir(path: str) -> None:
    """Crea la carpeta de salida si no existe."""
    os.makedirs(path, exist_ok=True)


def generate_qr_base(data: str) -> Image.Image:
    """
    Genera la imagen base del código QR (sin logo) como un objeto PIL.Image (RGB).
    """
    qr = qrcode.QRCode(
        version=None,  # deja que la librería elija el tamaño mínimo suficiente
        error_correction=ERROR_CORRECT_H,  # alto nivel de corrección (para aguantar el logo)
        box_size=BOX_SIZE,
        border=BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img


def add_logo_to_qr(qr_img: Image.Image, logo_path: str, logo_scale: float) -> Image.Image:
    """
    Inserta un logo en el centro del QR. logo_scale es el porcentaje del ancho del QR.
    """
    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"No se encuentra la imagen de logo: {logo_path}")

    logo = Image.open(logo_path).convert("RGBA")

    qr_width, qr_height = qr_img.size

    # Nuevo tamaño del logo (proporcional)
    logo_target_width = int(qr_width * logo_scale)
    # Mantener proporción original del logo
    aspect_ratio = logo.height / logo.width
    logo_target_height = int(logo_target_width * aspect_ratio)

    logo = logo.resize((logo_target_width, logo_target_height), Image.LANCZOS)

    # Posición centrada
    pos_x = (qr_width - logo_target_width) // 2
    pos_y = (qr_height - logo_target_height) // 2

    # Trabajamos sobre una copia del QR para no modificar el original
    qr_with_logo = qr_img.copy()
    qr_with_logo.paste(logo, (pos_x, pos_y), logo)

    return qr_with_logo


def save_qr_image(img: Image.Image, output_path: str, output_format: str) -> None:
    """
    Guarda la imagen del QR en el formato deseado.
    - output_format: 'jpg' o 'pdf'
    """
    output_format = output_format.lower()

    if output_format == "jpg" or output_format == "jpeg":
        # Aseguramos RGB y guardamos como JPEG
        rgb_img = img.convert("RGB")
        # Forzamos extensión .jpg por coherencia
        if not output_path.lower().endswith(".jpg"):
            output_path += ".jpg"
        rgb_img.save(output_path, "JPEG", quality=95)

    elif output_format == "pdf":
        # Pillow permite guardar directamente como PDF
        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"
        # Convertimos a RGB por si acaso
        rgb_img = img.convert("RGB")
        rgb_img.save(output_path, "PDF")

    else:
        raise ValueError(f"Formato de salida no soportado: {output_format}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generador de código QR para formulario de Google con logo central."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=FORM_URL,
        help="URL a codificar en el QR (por defecto el formulario de Google).",
    )
    parser.add_argument(
        "--logo",
        type=str,
        default=DEFAULT_LOGO_PATH,
        help="Ruta al archivo de logo en PNG (por defecto assets/logo.png).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=OUTPUT_DIR,
        help="Carpeta de salida para el archivo generado.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="qr_formulario",
        help="Nombre base del archivo de salida (sin extensión).",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=DEFAULT_OUTPUT_FORMAT,
        choices=["jpg", "pdf"],
        help="Formato de salida: jpg o pdf.",
    )
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=LOGO_SCALE,
        help="Proporción del ancho del QR que ocupará el logo (ejemplo: 0.22).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    ensure_output_dir(args.out_dir)

    print("Generando código QR...")
    qr_base = generate_qr_base(args.url)

    print("Insertando logo en el centro...")
    qr_with_logo = add_logo_to_qr(qr_base, args.logo, args.logo_scale)

    output_path = os.path.join(args.out_dir, args.name)
    print(f"Guardando archivo en formato {args.format.upper()}...")
    save_qr_image(qr_with_logo, output_path, args.format)

    final_path = (
        output_path + (".jpg" if args.format.lower() == "jpg" else ".pdf")
    )
    print(f"QR generado correctamente en: {final_path}")


if __name__ == "__main__":
    main()
