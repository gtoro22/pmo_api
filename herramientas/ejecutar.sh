#!/usr/bin/env bash
# Envoltorio para ejecutar el invocador desde cron.
#
# Resuelve los problemas tipicos del entorno de cron:
#   - se situa en la raiz del proyecto (el .env, output/ y logs/ son relativos)
#   - fija el locale, para que los acentos no rompan la salida por consola
#   - evita que dos ejecuciones se solapen (flock)
#   - deja traza del inicio, el fin y el codigo de salida
#   - purga los Excel y los logs mas viejos que RETENCION_DIAS
#
# Uso:
#     bash herramientas/ejecutar.sh --todas-las-paginas
#
# En crontab (todos los dias a las 6:00):
#     0 6 * * * /home/usuario/pmo_api/herramientas/ejecutar.sh --todas-las-paginas
#
# Variables opcionales:
#     PYTHON_BIN       interprete a usar          (por defecto /usr/bin/python3)
#     RETENCION_DIAS   dias que se conservan      (por defecto 90; 0 = no purgar)

set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

export LANG="${LANG:-C.UTF-8}"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
RETENCION_DIAS="${RETENCION_DIAS:-90}"

mkdir -p logs output
BITACORA="logs/cron.log"

registrar() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$BITACORA"
}

# Un solo proceso a la vez: si el anterior sigue corriendo, esta ejecucion
# se salta en lugar de acumularse.
exec 9>"logs/.ejecutar.lock"
if ! flock -n 9; then
    registrar "OMITIDA: ya hay una ejecucion en curso."
    exit 0
fi

registrar "===== INICIO ($*) ====="
"$PYTHON_BIN" main.py "$@" >> "$BITACORA" 2>&1
CODIGO=$?

if [ "$CODIGO" -eq 0 ]; then
    registrar "===== FIN OK ====="
else
    registrar "===== FIN CON ERRORES (codigo $CODIGO) ====="
fi

# Purga de archivos antiguos
if [ "$RETENCION_DIAS" -gt 0 ]; then
    find output -maxdepth 1 -name '*.xlsx' -type f -mtime "+$RETENCION_DIAS" -delete 2>/dev/null
    find logs -maxdepth 1 -name 'tracking-goals-invoker_*.log' -type f \
        -mtime "+$RETENCION_DIAS" -delete 2>/dev/null
fi

exit "$CODIGO"
