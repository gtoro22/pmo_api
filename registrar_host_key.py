#!/usr/bin/env python
"""Registra la llave de un servidor SFTP en known_hosts.

Ejecutable directamente, sin instalar el proyecto ni crear entorno virtual:

    python3 registrar_host_key.py

Agrega `src/` al path de importacion y delega en la capa de interfaces.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from tracking_goals.interfaces.cli.registrar_host_key import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
