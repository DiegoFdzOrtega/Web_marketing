# Web de Ari

Portfolio de vídeos (edición + guiones) de Ari. Un solo `index.html`, sin dependencias.

## Editar
- **Contacto y CV:** al principio del `<script>` de `index.html`, objeto `CONTACTO`. Lo que quede vacío no se muestra.
- **Vídeos:** array `VIDEOS` justo debajo. Para añadir uno, copia una línea y cambia `t` (título), `f` (formato) e `id` (lo que va después de `/reel/` en el enlace).

## Publicar en GitHub Pages
1. Crea el repo `Web_Ari` en GitHub y sube esta carpeta.
2. Settings → Pages → Branch `main`, carpeta `/ (root)`.
3. La web queda en `https://diegofdzortega.github.io/Web_Ari/`.

## Código QR para el CV
`qr/qr-web-ari.svg` (vectorial, mejor para el CV) y `qr/qr-web-ari.png` apuntan a la URL de arriba.
Si la web acaba en otra dirección: `python qr/generar_qr.py https://nueva-url/`
