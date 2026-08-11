"""Fixtures compartidas: respuesta de ejemplo del documento tecnico."""

from __future__ import annotations

import pytest

from tracking_goals.infrastructure.config.settings import Settings


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
