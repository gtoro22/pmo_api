"""Fixtures compartidas: respuesta de ejemplo del documento tecnico."""

from __future__ import annotations

import os

import pytest

from tracking_goals.infrastructure.config.settings import Settings

PREFIJOS_CONFIGURACION = ("AMAGI_", "ENVIO_")
VARIABLES_CONFIGURACION = ("LOG_LEVEL", "LOG_DIR", "OUTPUT_DIR")


@pytest.fixture(autouse=True)
def entorno_limpio():
    """Aisla cada prueba de la configuracion que dejaron las anteriores.

    `load_dotenv` escribe en `os.environ` y esos valores sobreviven a la prueba
    que cargo el archivo, porque no los puso `monkeypatch`. Sin esta limpieza,
    una prueba podia heredar el ENVIO_HOST de otra e intentar una conexion real.
    """
    previo = dict(os.environ)
    _borrar_configuracion()
    yield
    os.environ.clear()
    os.environ.update(previo)


def _borrar_configuracion() -> None:
    for clave in list(os.environ):
        if clave.startswith(PREFIJOS_CONFIGURACION) or clave in VARIABLES_CONFIGURACION:
            del os.environ[clave]


@pytest.fixture
def respuesta_documentacion() -> dict:
    """Ejemplo de la seccion 7 del documento tecnico."""
    return {
        "results": [
            {
                "id": 13,
                "identificacion": "5555553333",
                "nombres": "Usuario",
                "apellidos": "Prueba",
                "evaluaciones": [
                    {
                        "id": 127,
                        "proyecto": "2026",
                        "nombre": "Q4 2026 CO",
                        "total_perspectivas": 1,
                        "total_objetivos": 4,
                        "perspectivas": [
                            {
                                "id": 7,
                                "nombre": "Procesos Internos",
                                "objetivos": [
                                    {
                                        "id": 15,
                                        "objetivo": "Aplicar la metodologia de gestion\nde proyectos",
                                        "meta": 100.0,
                                        "unidad_medida": "Porcentaje",
                                        "tipo_calculo": "Ultimo dato",
                                        "tipo_indicador": "Creciente",
                                        "indicador": "VENEZUELA",
                                        "resultado": None,
                                        "cumplimiento": None,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "meta": {
            "page": 1,
            "per_page": 50,
            "total_users": 1,
            "total_pages": 1,
            "updated_since": None,
            "server_time": "2026-07-29T10:38:00-05:00",
            "next_updated_since": "2026-07-29T10:38:00-05:00",
        },
        "status": "ok",
    }


@pytest.fixture
def respuesta_servicio() -> dict:
    """Respuesta real del servicio (24/08/2026), con los datos personales enmascarados.

    Incluye los campos que el servicio entrega y que NO figuran en el documento
    tecnico v1.0, y omite `indicador`, que el documento describe pero el
    servicio ya no envia.
    """
    return {
        "results": [
            {
                "id": 2,
                "identificacion": "6XXXXX7",
                "nombres": "NOMBRE",
                "apellidos": "APELLIDO EJEMPLO",
                "cargo": "Especialista de Administracion de Contratos",
                "nivel_cargo": "Operativo",
                "area": "Gestion Corporativa y Control de Gestion",
                "grupo": "Soporte",
                "localizacion": "Venezuela",
                "unidad_negocio": "Amagi Group",
                "evaluaciones": [
                    {
                        "id": 85,
                        "proyecto": "2026",
                        "nombre": "Q4 2026 CO",
                        "inicio": "2026-04-01",
                        "fin": "2026-08-31",
                        "evaluador": "Apellido1 Apellido2 Nombre1 Nombre2",
                        "estado_evaluacion": "Evaluacion Finalizada",
                        "total_perspectivas": 1,
                        "total_objetivos": 1,
                        "perspectivas": [
                            {
                                "id": 24,
                                "nombre": "Clientes",
                                "peso": 100.0,
                                "cumplimiento": 78.38,
                                "objetivos": [
                                    {
                                        "id": 98,
                                        "objetivo": "Calidad de la Data\nConsistencia de los numeros",
                                        "objetivo_estrategico": "VENEZUELA",
                                        "indicador_medicion": "• Mantenimiento del Dashboard Comercial",
                                        "peso": 35.0,
                                        "meta": 100.0,
                                        "minimo": None,
                                        "sobresaliente": None,
                                        "unidad_medida": "Porcentaje",
                                        "tipo_calculo": "Ultimo dato",
                                        "tipo_indicador": "Creciente",
                                        "periodo": "Q4 2026",
                                        "resultado": 90.0,
                                        "cumplimiento": 90.0,
                                        "fecha_limite": "2026-08-31",
                                        "estado_seguimientos": "Seguimiento Aprobado",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "meta": {
            "page": 1,
            "per_page": 50,
            "total_users": 143,
            "total_pages": 3,
            "updated_since": None,
            "server_time": "2026-08-24T15:55:17-05:00",
            "next_updated_since": "2026-08-24T15:55:17-05:00",
        },
        "status": "ok",
    }


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        api_base_url="https://amagi.elearning.co",
        api_token="token-de-pruebas",
        api_timeout=5,
        api_max_reintentos=1,
        api_backoff=0,
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "output",
    )
