#!/usr/bin/env python
"""Punto de entrada ejecutable del invocador.

Permite correr el CLI directamente, sin instalar el proyecto como paquete
ni crear un entorno virtual:

    python main.py --project 2026 --identity 5555553333

Solo agrega `src/` al path de importacion y delega en la capa de interfaces.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from tracking_goals.interfaces.cli.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
