"""Descarga la portada de cada vídeo de Instagram a img/portadas/<id>.jpg

Uso (desde la carpeta Web_Ari):
    python descargar_portadas.py

Solo usa la librería estándar de Python. Lee los ids de los vídeos del
propio index.html, así que si añades vídeos nuevos basta con volver a
ejecutarlo (las portadas que ya existen no se vuelven a descargar;
usa --todas para forzarlo).
"""
import html
import os
import re
import sys
import time
import urllib.request

CARPETA = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(CARPETA, "img", "portadas")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")


def pedir(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,image/avif,image/webp,image/*,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.headers.get("Content-Type", ""), r.read()


def portada(tipo, vid):
    # 1) Miniatura vertical de 320 px (ligera, unos 20 KB)
    try:
        ctype, datos = pedir(f"https://www.instagram.com/p/{vid}/media/?size=m")
        if ctype.startswith("image/") and len(datos) > 2000:
            return datos
    except Exception:
        pass
    # 2) Plan B: la imagen que muestra el reproductor incrustado
    _, pagina = pedir(f"https://www.instagram.com/{tipo}/{vid}/embed/")
    m = re.search(r'class="EmbeddedMediaImage"[^>]*src="([^"]+)"', pagina.decode("utf-8", "ignore"))
    if not m:
        raise RuntimeError("no se encontró la imagen")
    ctype, datos = pedir(html.unescape(m.group(1)))
    if not ctype.startswith("image/"):
        raise RuntimeError("la respuesta no es una imagen")
    return datos


def main():
    todas = "--todas" in sys.argv
    with open(os.path.join(CARPETA, "index.html"), encoding="utf-8") as f:
        codigo = f.read()
    bloque = codigo[codigo.index("var VIDEOS"):]
    bloque = bloque[:bloque.index("];")]
    videos = []
    for linea in re.findall(r"\{[^{}]*\}", bloque):
        vid = re.search(r'id:"([^"]+)"', linea)
        tipo = re.search(r'tipo:"([^"]+)"', linea)
        if vid:
            videos.append((tipo.group(1) if tipo else "reel", vid.group(1)))
    os.makedirs(DESTINO, exist_ok=True)
    ok = fallos = 0
    for tipo, vid in videos:
        ruta = os.path.join(DESTINO, vid + ".jpg")
        if os.path.exists(ruta) and not todas:
            print("  ya existe ", vid)
            ok += 1
            continue
        try:
            datos = portada(tipo, vid)
            with open(ruta, "wb") as f:
                f.write(datos)
            print(f"  descargada {vid}  ({len(datos) // 1024} KB)")
            ok += 1
        except Exception as e:
            print(f"  ERROR      {vid}: {e}")
            fallos += 1
        time.sleep(0.6)
    print(f"\n{ok} portadas listas en img/portadas/, {fallos} errores.")
    if fallos:
        print("Vuelve a ejecutarlo en unos minutos: Instagram a veces limita las descargas seguidas.")


if __name__ == "__main__":
    main()
