"""Puerto de salida: exportador de registros planos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from tracking_goals.domain.model.registro_plano import RegistroPlano


class ExportadorRegistros(ABC):
    """Contrato de escritura del reporte generado por el invocador."""

    @abstractmethod
    def exportar(self, registros: Sequence[RegistroPlano], destino: Path) -> Path:
        """Escribe los registros en `destino` y devuelve la ruta final.

        Raises:
            ErrorDeExportacion: si no es posible generar el archivo.
        """
        raise NotImplementedError
