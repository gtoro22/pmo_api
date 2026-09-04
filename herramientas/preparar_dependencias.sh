#!/usr/bin/env bash
# Descarga las dependencias como wheels de Linux y las descomprime en `libs/`,
# para servidores sin pip, sin venv y sin salida a PyPI.
#
# Se ejecuta en una maquina CON internet (puede ser Windows con Git Bash, o
# cualquier equipo con pip). Luego se copia la carpeta `libs/` al servidor y
# el invocador se ejecuta asi:
#
#     PYTHONPATH=libs python3 main.py --todas-las-paginas
#
# Uso:
#     bash herramientas/preparar_dependencias.sh
#     bash herramientas/preparar_dependencias.sh 3.11     # otra version de Python

set -euo pipefail

VERSION_PYTHON="${1:-3.11}"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHEELS="$RAIZ/wheels"
LIBS="$RAIZ/libs"

echo "==> Descargando wheels de Linux para Python $VERSION_PYTHON"
rm -rf "$WHEELS" "$LIBS"
mkdir -p "$WHEELS" "$LIBS"

python -m pip download \
    -r "$RAIZ/requirements.txt" \
    -d "$WHEELS" \
    --only-binary=:all: \
    --python-version "$VERSION_PYTHON" \
    --platform manylinux_2_17_x86_64 \
    --platform manylinux_2_28_x86_64 \
    --platform manylinux_2_34_x86_64

echo "==> Descomprimiendo en libs/"
for rueda in "$WHEELS"/*.whl; do
    python -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
        "$rueda" "$LIBS"
done

# Los metadatos y scripts no hacen falta para importar
rm -rf "$LIBS"/*.dist-info "$LIBS"/*.data 2>/dev/null || true

echo
echo "Listo. Copie la carpeta libs/ al servidor junto al proyecto y ejecute:"
echo "    PYTHONPATH=libs python3 main.py --todas-las-paginas"
echo
du -sh "$LIBS"
