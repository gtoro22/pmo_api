"""Pruebas de la interfaz de linea de comandos."""

from __future__ import annotations

from pathlib import Path

import pytest
import responses

from tracking_goals.interfaces.cli.argumentos import construir_parser, construir_solicitud
from tracking_goals.interfaces.cli.main import CODIGO_ERROR, CODIGO_OK, main

URL = "https://amagi.elearning.co/api/v1/tracking_goals"


def _escribir_env(tmp_path: Path) -> Path:
    ruta = tmp_path / ".env"
    ruta.write_text(
        "AMAGI_API_BASE_URL=https://amagi.elearning.co\n"
        "AMAGI_API_TOKEN=token-de-pruebas\n"
        "AMAGI_API_MAX_REINTENTOS=1\n"
        f"LOG_DIR={tmp_path / 'logs'}\n"
        f"OUTPUT_DIR={tmp_path / 'output'}\n",
        encoding="utf-8",
    )
    return ruta


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for variable in (
        "AMAGI_API_BASE_URL",
        "AMAGI_API_TOKEN",
        "AMAGI_API_MAX_REINTENTOS",
        "AMAGI_PROYECTO_DEFECTO",
        "AMAGI_PER_PAGE_DEFECTO",
        "LOG_DIR",
        "OUTPUT_DIR",
    ):
        monkeypatch.delenv(variable, raising=False)


def test_solicitud_usa_valores_por_defecto_del_env(settings):
    from dataclasses import replace

    settings = replace(settings, proyecto_defecto="2026", per_page_defecto=25)
    argumentos = construir_parser().parse_args([])
    solicitud = construir_solicitud(argumentos, settings)

    assert solicitud.criterio.project == "2026"
    assert solicitud.criterio.per_page == 25
    assert solicitud.destino.parent == settings.output_dir
    assert solicitud.destino.suffix == ".xlsx"


def test_argumentos_del_cli_tienen_prioridad(settings):
    from dataclasses import replace

    settings = replace(settings, proyecto_defecto="2026", per_page_defecto=25)
    argumentos = construir_parser().parse_args(
        ["--project", "2027", "--per-page", "100", "--todas-las-paginas"]
    )
    solicitud = construir_solicitud(argumentos, settings)

    assert solicitud.criterio.project == "2027"
    assert solicitud.criterio.per_page == 100
    assert solicitud.todas_las_paginas is True


@responses.activate
def test_ejecucion_completa_genera_excel_y_log(tmp_path, respuesta_documentacion):
    responses.add(responses.GET, URL, json=respuesta_documentacion, status=200)
    env = _escribir_env(tmp_path)
    salida = tmp_path / "reporte.xlsx"

    codigo = main(
        [
            "--env-file",
            str(env),
            "--project",
            "2026",
            "--identity",
            "5555553333",
            "--salida",
            str(salida),
        ]
    )

    assert codigo == CODIGO_OK
    assert salida.exists()
    logs = list((tmp_path / "logs").glob("*.log"))
    assert len(logs) == 1
    contenido = logs[0].read_text(encoding="utf-8")
    assert "INICIO DEL PROCESO" in contenido
    assert "FINALIZADO CORRECTAMENTE" in contenido
    assert "token-de-pruebas" not in contenido


@responses.activate
def test_error_del_servicio_devuelve_codigo_de_error(tmp_path):
    responses.add(responses.GET, URL, json={"error": "unauthorized"}, status=401)
    env = _escribir_env(tmp_path)

    codigo = main(["--env-file", str(env), "--salida", str(tmp_path / "x.xlsx")])

    assert codigo == CODIGO_ERROR
    assert not (tmp_path / "x.xlsx").exists()


def test_falta_de_configuracion_devuelve_error(tmp_path, capsys):
    vacio = tmp_path / "vacio.env"
    vacio.write_text("", encoding="utf-8")

    codigo = main(["--env-file", str(vacio)])

    assert codigo == CODIGO_ERROR
    assert "AMAGI_API_BASE_URL" in capsys.readouterr().err
