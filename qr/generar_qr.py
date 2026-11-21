"""Genera el código QR que lleva a la web de Ari (para ponerlo en el CV).

Uso:
    python generar_qr.py                      -> usa la URL por defecto
    python generar_qr.py https://otra-url.com -> usa la URL que le pases

Crea qr-web-ari.svg (vectorial, el mejor para el CV) y, si tienes Pillow
instalado, también qr-web-ari.png. No necesita ninguna librería de QR:
el codificador (modo byte, corrección de errores nivel Q) está aquí mismo.
"""
import os
import sys

URL_POR_DEFECTO = "https://diegofdzortega.github.io/Web_marketing/"

# Tablas del estándar QR (índice = versión). Orden de niveles: L, M, Q, H
ECC_POR_BLOQUE = [
    [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18],
    [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26],
    [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24],
    [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28],
]
NUM_BLOQUES = [
    [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4],
    [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5],
    [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8],
    [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8],
]
BITS_FORMATO = [1, 0, 3, 2]  # L, M, Q, H
NIVEL = 2  # Q: aguanta ~25 % del código dañado (bien para papel impreso)


def modulos_datos(v):
    r = (16 * v + 128) * v + 64
    if v >= 2:
        n = v // 7 + 2
        r -= (25 * n - 10) * n - 55
        if v >= 7:
            r -= 36
    return r


def codewords_datos(v, e):
    return modulos_datos(v) // 8 - ECC_POR_BLOQUE[e][v] * NUM_BLOQUES[e][v]


# Reed-Solomon sobre GF(256)
def rs_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def rs_divisor(grado):
    r = [0] * (grado - 1) + [1]
    raiz = 1
    for _ in range(grado):
        for j in range(len(r)):
            r[j] = rs_mul(r[j], raiz)
            if j + 1 < len(r):
                r[j] ^= r[j + 1]
        raiz = rs_mul(raiz, 0x02)
    return r


def rs_resto(datos, divisor):
    r = [0] * len(divisor)
    for b in datos:
        f = b ^ r.pop(0)
        r.append(0)
        for i, c in enumerate(divisor):
            r[i] ^= rs_mul(c, f)
    return r


def posiciones_alineacion(v):
    if v == 1:
        return []
    n = v // 7 + 2
    paso = (v * 8 + n * 3 + 5) // (n * 4 - 4) * 2
    r = [v * 4 + 10 - i * paso for i in range(n - 1)] + [6]
    return list(reversed(r))


def codificar(texto):
    datos = texto.encode("utf-8")
    for v in range(1, 7):  # hasta v6 (sin bloque de versión)
        cap = codewords_datos(v, NIVEL) * 8
        cuenta = 8 if v < 10 else 16
        if 4 + cuenta + len(datos) * 8 <= cap:
            break
    else:
        raise ValueError("URL demasiado larga para este generador")

    bits = []
    def poner(val, n):
        bits.extend((val >> i) & 1 for i in range(n - 1, -1, -1))
    poner(0b0100, 4)
    poner(len(datos), cuenta)
    for b in datos:
        poner(b, 8)
    poner(0, min(4, cap - len(bits)))
    poner(0, (8 - len(bits) % 8) % 8)
    relleno = 0xEC
    while len(bits) < cap:
        poner(relleno, 8)
        relleno ^= 0xEC ^ 0x11
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]

    # Bloques + ECC, intercalados
    nb = NUM_BLOQUES[NIVEL][v]
    ecc_len = ECC_POR_BLOQUE[NIVEL][v]
    total = modulos_datos(v) // 8
    cortos = nb - total % nb
    largo_corto = total // nb
    div = rs_divisor(ecc_len)
    bloques, k = [], 0
    for i in range(nb):
        d = cw[k:k + largo_corto - ecc_len + (0 if i < cortos else 1)]
        k += len(d)
        e = rs_resto(d, div)
        if i < cortos:
            d = d + [None]
        bloques.append(d + e)
    final = []
    for i in range(len(bloques[0])):
        for j, b in enumerate(bloques):
            if i != largo_corto - ecc_len or j >= cortos:
                final.append(b[i])

    size = v * 4 + 17
    m = [[False] * size for _ in range(size)]
    fijo = [[False] * size for _ in range(size)]

    def set_f(x, y, val):
        m[y][x] = val
        fijo[y][x] = True

    for i in range(size):
        set_f(6, i, i % 2 == 0)
        set_f(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    set_f(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    al = posiciones_alineacion(v)
    for i, a in enumerate(al):
        for j, b in enumerate(al):
            if (i == 0 and j == 0) or (i == 0 and j == len(al) - 1) or (i == len(al) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    set_f(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)

    def poner_formato(mask):
        d = BITS_FORMATO[NIVEL] << 3 | mask
        r = d
        for _ in range(10):
            r = (r << 1) ^ ((r >> 9) * 0x537)
        b = (d << 10 | r) ^ 0x5412
        bit = lambda i: (b >> i) & 1 == 1
        for i in range(6):
            set_f(8, i, bit(i))
        set_f(8, 7, bit(6))
        set_f(8, 8, bit(7))
        set_f(7, 8, bit(8))
        for i in range(9, 15):
            set_f(14 - i, 8, bit(i))
        for i in range(8):
            set_f(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            set_f(8, size - 15 + i, bit(i))
        set_f(8, size - 8, True)

    poner_formato(0)  # reserva las zonas de formato

    # Colocar datos en zigzag
    todos = []
    for b in final:
        todos.extend((b >> i) & 1 for i in range(7, -1, -1))
    i = 0
    derecha = size - 1
    while derecha >= 1:
        if derecha == 6:
            derecha = 5
        for vert in range(size):
            for j in range(2):
                x = derecha - j
                sube = ((derecha + 1) & 2) == 0
                y = size - 1 - vert if sube else vert
                if not fijo[y][x] and i < len(todos):
                    m[y][x] = todos[i] == 1
                    i += 1
        derecha -= 2

    mascaras = [
        lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0,
        lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
        lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
        lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
    ]

    def aplicar(k):
        for y in range(size):
            for x in range(size):
                if not fijo[y][x] and mascaras[k](x, y):
                    m[y][x] = not m[y][x]

    def penalizacion():
        p = 0
        for filas in (m, [list(c) for c in zip(*m)]):
            for fila in filas:
                n = 1
                for a, b in zip(fila, fila[1:]):
                    if a == b:
                        n += 1
                    else:
                        if n >= 5:
                            p += n - 2
                        n = 1
                if n >= 5:
                    p += n - 2
                s = "".join("1" if c else "0" for c in fila)
                p += 40 * (s.count("10111010000") + s.count("00001011101"))
        for y in range(size - 1):
            for x in range(size - 1):
                if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    p += 3
        oscuros = sum(sum(f) for f in m)
        p += (abs(oscuros * 20 - size * size * 10) // (size * size)) * 10
        return p

    mejor, mejor_p = 0, None
    for k in range(8):
        aplicar(k)
        poner_formato(k)
        p = penalizacion()
        if mejor_p is None or p < mejor_p:
            mejor, mejor_p = k, p
        aplicar(k)
    aplicar(mejor)
    poner_formato(mejor)
    return m


def guardar(m, carpeta):
    n = len(m)
    borde = 4
    lado = n + borde * 2
    trazos = "".join(
        f"M{x + borde},{y + borde}h1v1h-1z" for y in range(n) for x in range(n) if m[y][x]
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}" '
        f'shape-rendering="crispEdges"><rect width="{lado}" height="{lado}" fill="#fff"/>'
        f'<path d="{trazos}" fill="#000"/></svg>\n'
    )
    ruta_svg = os.path.join(carpeta, "qr-web-ari.svg")
    with open(ruta_svg, "w", encoding="utf-8") as f:
        f.write(svg)
    print("Creado", ruta_svg)
    try:
        from PIL import Image
    except ImportError:
        print("(Pillow no está instalado: solo se ha creado el SVG)")
        return
    escala = 24
    img = Image.new("L", (lado * escala, lado * escala), 255)
    px = img.load()
    for y in range(n):
        for x in range(n):
            if m[y][x]:
                for dy in range(escala):
                    for dx in range(escala):
                        px[(x + borde) * escala + dx, (y + borde) * escala + dy] = 0
    ruta_png = os.path.join(carpeta, "qr-web-ari.png")
    img.save(ruta_png)
    print("Creado", ruta_png)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else URL_POR_DEFECTO
    print("URL:", url)
    guardar(codificar(url), os.path.dirname(os.path.abspath(__file__)))
