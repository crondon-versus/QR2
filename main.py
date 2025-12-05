# main.py

import os
import argparse

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image

from config import (
    FORM_URL,
    OUTPUT_DIR,
    BOX_SIZE,
    BORDER,
    DEFAULT_OUTPUT_FORMAT,
)


def ensure_output_dir(path: str) -> None:
    """Crea la carpeta de salida si no existe."""
    os.makedirs(path, exist_ok=True)


def generate_qr_base(data: str) -> Image.Image:
    """
    Genera la imagen del código QR (sin logo) como un objeto PIL.Image (RGB).
    """
    # Mantenemos ERROR_CORRECT_H para que el QR sea muy resistente a daños,
    # aunque sin logo se podría usar 'M' o 'L'.
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=BOX_SIZE,
        border=BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img


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
        description="Generador de código QR para formulario de Google (Sin Logo)."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=FORM_URL,
        help="URL a codificar en el QR (por defecto el formulario de Google).",
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
        default="qr_formulario_sin_logo",
        help="Nombre base del archivo de salida (sin extensión).",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=DEFAULT_OUTPUT_FORMAT,
        choices=["jpg", "pdf"],
        help="Formato de salida: jpg o pdf.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    ensure_output_dir(args.out_dir)

    print("Generando código QR limpio (sin logo)...")
    qr_img = generate_qr_base(args.url)

    output_path = os.path.join(args.out_dir, args.name)
    print(f"Guardando archivo en formato {args.format.upper()}...")
    
    save_qr_image(qr_img, output_path, args.format)

    final_path = (
        output_path + (".jpg" if args.format.lower() == "jpg" else ".pdf")
    )
    print(f"QR generado correctamente en: {final_path}")


if __name__ == "__main__":
    main()