"""Puerto de salida: entrega del reporte a un destino remoto.

El dominio y los casos de uso no saben si la entrega ocurre por SFTP, FTP o si
esta deshabilitada: solo conocen este contrato.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResultadoEnvio:
    """Desenlace de la entrega del archivo."""

    enviado: bool
    protocolo: str | None = None
    destino: str | None = None
    motivo: str | None = None

    @classmethod
    def deshabilitado(cls, motivo: str = "Envio remoto deshabilitado") -> "ResultadoEnvio":
        return cls(enviado=False, motivo=motivo)

    def describir(self) -> str:
        if self.enviado:
            return f"{self.protocolo} -> {self.destino}"
        return self.motivo or "no enviado"


class TransportadorArchivos(ABC):
    """Contrato de entrega de un archivo generado."""

    @abstractmethod
    def enviar(self, archivo: Path) -> ResultadoEnvio:
        """Entrega `archivo` en el destino remoto configurado.

        Raises:
            ErrorDeEnvio: si la conexion, la autenticacion o la transferencia fallan.
        """
        raise NotImplementedError
