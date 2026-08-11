"""Definicion y parseo de los argumentos de linea de comandos."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from tracking_goals.application.dto.solicitud_exportacion import SolicitudExportacion
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta
from tracking_goals.infrastructure.config.settings import Settings

DESCRIPCION = (
    "Invocador del servicio web de evaluaciones y objetivos de Amagi. "
    "Consulta el endpoint tracking_goals y exporta los resultados a Excel."
)

EPILOGO = """Ejemplos:
  tracking-goals --project 2026 --identity 5555553333
  tracking-goals --project 2026 --per-page 100 --todas-las-paginas
  tracking-goals --updated-since 2026-07-29T10:38:00-05:00 --salida reporte.xlsx
"""


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tracking-goals",
        description=DESCRIPCION,
        epilog=EPILOGO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    filtros = parser.add_argument_group("Filtros de consulta")
    filtros.add_argument(
        "--project",
        "-p",
        help="Codigo o nombre del proyecto (ej. 2026). Por defecto usa AMAGI_PROYECTO_DEFECTO.",
    )
    filtros.add_argument(
        "--identity",
        "-i",
        help="Numero de identificacion del usuario a consultar.",
    )
    filtros.add_argument(
        "--updated-since",
        help="Marca temporal ISO 8601 para sincronizacion incremental.",
    )

    paginacion = parser.add_argument_group("Paginacion")
    paginacion.add_argument("--page", type=int, default=1, help="Pagina inicial (por defecto 1).")
    paginacion.add_argument(
        "--per-page",
        type=int,
        help="Usuarios por pagina. Por defecto usa AMAGI_PER_PAGE_DEFECTO.",
    )
    paginacion.add_argument(
        "--todas-las-paginas",
        "--all-pages",
        action="store_true",
        dest="todas_las_paginas",
        help="Recorre todas las paginas hasta total_pages y consolida los resultados.",
    )

    salida = parser.add_argument_group("Salida")
    salida.add_argument(
        "--salida",
        "-o",
        type=Path,
        help="Ruta del archivo Excel a generar. Por defecto OUTPUT_DIR/tracking_goals_<fecha>.xlsx.",
    )
    salida.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nivel de detalle del log. Por defecto usa LOG_LEVEL.",
    )
    salida.add_argument(
        "--env-file",
        type=Path,
        help="Ruta alternativa del archivo .env.",
    )
    return parser


def construir_solicitud(
    argumentos: argparse.Namespace, settings: Settings
) -> SolicitudExportacion:
    """Combina los argumentos del CLI con los valores por defecto del `.env`."""
    criterio = CriterioConsulta(
        project=argumentos.project or settings.proyecto_defecto,
        identity=argumentos.identity,
        page=argumentos.page,
        per_page=argumentos.per_page or settings.per_page_defecto,
        updated_since=argumentos.updated_since,
    )
    return SolicitudExportacion(
        criterio=criterio,
        destino=argumentos.salida or _destino_por_defecto(settings),
        todas_las_paginas=argumentos.todas_las_paginas,
    )


def _destino_por_defecto(settings: Settings) -> Path:
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    return settings.output_dir / f"tracking_goals_{marca}.xlsx"
