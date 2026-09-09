# web/build.py
"""
Genera docs/index.html, la version autonoma y desplegable, a partir de
web/index.html, que es la fuente unica.

Por que hace falta este paso
----------------------------
web/index.html esta escrito como fuente de artifact: a proposito NO lleva
<!DOCTYPE>, <html>, <head>, <meta charset> ni <meta viewport>, porque el visor de
artifacts los anade al publicar. Servido tal cual en un hosting estatico eso se
rompe, y de la peor manera: sin la etiqueta de viewport el movil usa su ventana de
reserva de ~980 px, con lo que la media query de escritorio se activa y la pagina
se reduce a un ~40% (letra de 6 px, controles inarrastrables). Sin charset, los
acentos salen mal en cualquier servidor que no mande la cabecera correcta.

Este script envuelve la fuente en el esqueleto que falta. Nada se duplica: si
cambia web/index.html, se vuelve a ejecutar y ya esta.

Uso
---
    python web/build.py            genera docs/index.html
    python web/build.py --check    falla si docs/index.html esta desactualizado

Desplegar en GitHub Pages: Settings > Pages > Deploy from a branch > main /docs.
"""

import argparse
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(HERE, "index.html")
OUT_DIR = os.path.join(ROOT, "docs")
OUT = os.path.join(OUT_DIR, "index.html")

# Elementos que pertenecen a <head>. Se consumen desde el principio del archivo
# mientras aparezcan; el resto es el cuerpo.
HEAD_PATTERNS = [
    re.compile(r"\s+"),
    re.compile(r"<!--.*?-->", re.S),
    re.compile(r"<title\b[^>]*>.*?</title>", re.S | re.I),
    re.compile(r"<style\b[^>]*>.*?</style>", re.S | re.I),
    re.compile(r"<link\b[^>]*?/?>", re.I),
    re.compile(r"<meta\b[^>]*?/?>", re.I),
]

# Lo que el visor de artifacts pone en su <head> y aqui hay que reponer.
# El resto del reset (margin 0, img max-width, [hidden]) ya lo declara la propia
# hoja de estilos de la pagina, asi que no se repite.
SKELETON_HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>:root { color-scheme: light dark; }</style>"""


def split_head_body(src: str):
    """Separa el prefijo de <head> del cuerpo, sin depender del marcado concreto."""
    pos = 0
    head_parts = []
    while pos < len(src):
        for pattern in HEAD_PATTERNS:
            m = pattern.match(src, pos)
            if m:
                chunk = m.group(0)
                if chunk.strip():
                    head_parts.append(chunk)
                pos = m.end()
                break
        else:
            break
    return "\n".join(head_parts), src[pos:].strip()


def render(src: str) -> str:
    head, body = split_head_body(src)
    if not head:
        raise SystemExit(
            "ERROR: no encontre nada para el <head> en web/index.html. "
            "Se esperaba que empezara por <title>, <link> o <style>."
        )
    if "<style" not in head.lower():
        raise SystemExit(
            "ERROR: el <head> extraido no contiene ningun <style>. "
            "Algo cambio en la estructura de web/index.html; revisa este script."
        )
    if "canvas" not in body.lower():
        raise SystemExit(
            "ERROR: el cuerpo extraido no contiene el <canvas> del codigo QR. "
            "El reparto entre <head> y <body> ha salido mal."
        )

    digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:12]
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n'
        "<head>\n"
        "<!-- GENERADO AUTOMATICAMENTE. No editar este archivo.\n"
        "     Fuente: web/index.html (sha256:%s)\n"
        "     Regenerar con: python web/build.py -->\n"
        "%s\n"
        "%s\n"
        "</head>\n"
        "<body>\n"
        "%s\n"
        "</body>\n"
        "</html>\n"
    ) % (digest, SKELETON_HEAD, head, body)


def main():
    parser = argparse.ArgumentParser(
        description="Genera la version autonoma desplegable a partir de web/index.html."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="No escribe nada; falla si docs/index.html no coincide con la fuente.",
    )
    args = parser.parse_args()

    if not os.path.exists(SOURCE):
        raise SystemExit("ERROR: no encuentro %s" % SOURCE)

    with open(SOURCE, encoding="utf-8") as fh:
        src = fh.read()

    rendered = render(src)

    if args.check:
        if not os.path.exists(OUT):
            raise SystemExit(
                "ERROR: falta docs/index.html. Ejecuta: python web/build.py"
            )
        with open(OUT, encoding="utf-8") as fh:
            current = fh.read()
        if current != rendered:
            raise SystemExit(
                "ERROR: docs/index.html esta desactualizado respecto a web/index.html.\n"
                "Ejecuta: python web/build.py"
            )
        print("docs/index.html esta al dia.")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(rendered)

    # Evita que Jekyll se entrometa en GitHub Pages.
    nojekyll = os.path.join(OUT_DIR, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()

    print("Generado docs/index.html (%d KB) desde web/index.html"
          % (len(rendered.encode("utf-8")) // 1024))
    print("Para publicarlo: Settings > Pages > Deploy from a branch > main /docs")


if __name__ == "__main__":
    main()
