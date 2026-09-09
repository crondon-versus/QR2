# main.py

import os
import glob
import argparse

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw

from config import (
    FORM_URL,
    OUTPUT_DIR,
    BOX_SIZE,
    BORDER,
    DEFAULT_OUTPUT_FORMAT,
    LOGO_PATH,
)

IMAGE_EXTS = ("png", "jpg", "jpeg", "webp", "gif", "bmp")


def ensure_output_dir(path: str) -> None:
    """Crea la carpeta de salida si no existe."""
    os.makedirs(path, exist_ok=True)


def available_logos() -> str:
    """Lista las imágenes que hay en assets/, para que el error sea útil."""
    found = []
    for ext in IMAGE_EXTS:
        found.extend(glob.glob(os.path.join("assets", "*." + ext)))
    if not found:
        return "No hay ninguna imagen en la carpeta assets/."
    return "Imágenes disponibles en assets/:\n" + "\n".join("  --logo \"%s\"" % f for f in sorted(found))


def open_logo(path: str) -> Image.Image:
    """Abre el logo o falla con un mensaje claro. Nunca devuelve None en silencio."""
    if not os.path.exists(path):
        raise SystemExit(
            "ERROR: no encuentro el logo en \"%s\".\n%s" % (path, available_logos())
        )
    try:
        logo = Image.open(path)
        logo.load()
    except Exception as exc:
        raise SystemExit(
            "ERROR: \"%s\" no se puede abrir como imagen (%s)." % (path, exc)
        )

    if logo.mode == "CMYK":
        print(
            "AVISO: \"%s\" está en CMYK. Al pasarlo a RGB los colores de marca "
            "pueden desplazarse un poco." % path
        )
    # Convertir ANTES de redimensionar: en modo P o 1, Pillow fuerza NEAREST y el
    # logo saldría con los bordes en dientes de sierra.
    if logo.mode != "RGBA":
        logo = logo.convert("RGBA")
    return logo


def generate_qr_with_logo(
    data: str,
    logo_path: str = None,
    logo_pct: float = 25.0,
    plate: bool = True,
):
    """
    Genera el código QR con un logo opcional en el centro.
    Devuelve (imagen, numero_de_casillas_por_lado).

    logo_pct se mide sobre el SÍMBOLO, no sobre la imagen con su margen blanco.
    Medirlo sobre la imagen completa (como se hacía antes) infla la oclusión real
    hasta el 34% en enlaces cortos, que es donde menos margen hay.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=BOX_SIZE,
        border=BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)
    modules = qr.modules_count

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if not logo_path:
        return img, modules

    logo = open_logo(logo_path)

    symbol_px = modules * BOX_SIZE
    plate_px = int(round(symbol_px * logo_pct / 100.0))
    plate_px = max(BOX_SIZE, min(plate_px, (modules - 16) * BOX_SIZE))

    # El símbolo está centrado en la imagen, así que el centro de la imagen sirve.
    off = (img.size[0] - plate_px) // 2

    if plate:
        draw = ImageDraw.Draw(img)
        box = [off, off, off + plate_px - 1, off + plate_px - 1]
        try:
            draw.rounded_rectangle(box, radius=max(1, min(BOX_SIZE, plate_px // 8)), fill="white")
        except AttributeError:      # Pillow anterior a 8.2
            draw.rectangle(box, fill="white")
        pad = BOX_SIZE
    else:
        pad = 0

    # Encajar en una caja CUADRADA limitando ambas dimensiones. Escalar solo por
    # anchura dejaba un logo vertical pegado en coordenada negativa, y Pillow lo
    # recortaba en silencio destrozando el código.
    inner = max(1, plate_px - 2 * pad)
    scale = min(inner / float(logo.width), inner / float(logo.height))
    new_w = max(1, int(round(logo.width * scale)))
    new_h = max(1, int(round(logo.height * scale)))

    resample_filter = getattr(Image, "Resampling", Image).LANCZOS
    logo = logo.resize((new_w, new_h), resample_filter)

    pos = (off + (plate_px - new_w) // 2, off + (plate_px - new_h) // 2)
    img.paste(logo, pos, mask=logo)

    return img, modules


def save_qr_image(img: Image.Image, output_path: str, output_format: str) -> str:
    """
    Guarda la imagen y devuelve la ruta final real, extensión incluida.
    Devolverla evita que el mensaje de éxito anuncie un archivo que no existe.
    """
    output_format = output_format.lower()
    rgb_img = img.convert("RGB")

    if output_format in ("jpg", "jpeg"):
        if not output_path.lower().endswith(".jpg"):
            output_path += ".jpg"
        # subsampling=0 fuerza 4:4:4. Sin él, libjpeg usa 4:2:0 y aparecen flecos
        # de color alrededor de un logo de color.
        rgb_img.save(output_path, "JPEG", quality=95, subsampling=0, dpi=(300, 300))

    elif output_format == "png":
        if not output_path.lower().endswith(".png"):
            output_path += ".png"
        rgb_img.save(output_path, "PNG", optimize=True, dpi=(300, 300))

    elif output_format == "pdf":
        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"
        # Sin resolution, Pillow escribe 72 ppp y sale una página de 20 cm.
        rgb_img.save(output_path, "PDF", resolution=300.0)

    else:
        raise ValueError("Formato de salida no soportado: %s" % output_format)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generador de código QR con logo opcional en el centro."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=FORM_URL,
        help="URL a codificar en el QR.",
    )
    parser.add_argument(
        "--logo",
        type=str,
        default=None,
        help="Ruta de la imagen del logo. Obligatorio salvo que uses --no-logo.",
    )
    parser.add_argument(
        "--logo-size",
        type=float,
        default=25.0,
        help="Tamaño del logo como %% del ancho del código (10-45). Por defecto 25.",
    )
    parser.add_argument(
        "--no-plate",
        action="store_true",
        help="No dibujar el recuadro blanco detrás del logo.",
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
        default="qr_con_logo",
        help="Nombre base del archivo de salida (sin extensión).",
    )
    parser.add_argument(
        "--format",
        type=str,
        default=DEFAULT_OUTPUT_FORMAT,
        choices=["png", "jpg", "pdf"],
        help="Formato de salida: png, jpg o pdf.",
    )
    parser.add_argument(
        "--no-logo",
        action="store_true",
        help="Generar el código QR sin el logo en el centro.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    url = (args.url or "").strip()
    if not url:
        raise SystemExit("ERROR: --url está vacío. Un QR sin destino no sirve de nada.")

    if not 10.0 <= args.logo_size <= 45.0:
        raise SystemExit(
            "ERROR: --logo-size debe estar entre 10 y 45 (has puesto %s)." % args.logo_size
        )

    if args.no_logo:
        logo_path = None
    else:
        logo_path = args.logo or LOGO_PATH
        if not logo_path:
            raise SystemExit(
                "ERROR: no has indicado ningún logo.\n"
                "Usa --logo RUTA, o --no-logo si lo quieres sin logo.\n"
                + available_logos()
            )

    try:
        ensure_output_dir(args.out_dir)
    except OSError as exc:
        raise SystemExit(
            "ERROR: no se pudo crear la carpeta \"%s\" (%s)." % (args.out_dir, exc)
        )

    print("Generando código QR %s logo..." % ("sin" if logo_path is None else "con"))
    qr_img, modules = generate_qr_with_logo(
        url,
        logo_path=logo_path,
        logo_pct=args.logo_size,
        plate=not args.no_plate,
    )

    version = (modules - 17) // 4
    if logo_path and version <= 2:
        print(
            "AVISO: tu enlace es cortísimo, así que el código sale en versión %d "
            "(%dx%d casillas) y aguanta muy poco logo. Si puedes usar el enlace "
            "largo en vez del acortado, sale bastante más robusto. También puedes "
            "bajarlo con --logo-size 15." % (version, modules, modules)
        )
    elif logo_path and version == 3:
        print(
            "AVISO: enlace corto (versión %d). Mantén el logo pequeño; "
            "--logo-size 20 va más seguro." % version
        )

    output_path = os.path.join(args.out_dir, args.name)
    print("Guardando archivo en formato %s..." % args.format.upper())

    try:
        final_path = save_qr_image(qr_img, output_path, args.format)
    except OSError as exc:
        raise SystemExit(
            "ERROR: no se pudo escribir el archivo en \"%s\" (%s)." % (output_path, exc)
        )

    mm_per_module = 0.6 if logo_path else 0.5
    print_cm = (modules + 2 * BORDER) * mm_per_module / 10.0

    print("QR generado correctamente en: %s" % final_path)
    print("Imprímelo a %.1f cm de lado o más, y escanéalo con el móvil antes de mandarlo."
          % print_cm)


if __name__ == "__main__":
    main()
