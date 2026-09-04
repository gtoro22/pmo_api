"""Interfaz de linea de comandos del invocador."""

from tracking_goals.interfaces.cli.main import main
from tracking_goals.interfaces.cli.registrar_host_key import main as registrar_host_key

__all__ = ["main", "registrar_host_key"]
