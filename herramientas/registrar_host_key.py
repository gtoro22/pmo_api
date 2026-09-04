#!/usr/bin/env python3
"""Registra la llave del servidor SFTP en un archivo `known_hosts`.

Con la verificacion de host key activada (el valor por defecto), el invocador
solo conecta si la llave del servidor ya esta registrada. Este script la obtiene
y la guarda, incluyendo el puerto cuando no es el 22.

Equivale a `ssh-keyscan -p <puerto> <host>`, pero usa paramiko, asi que funciona
aunque el servidor no tenga instalado el cliente de OpenSSH.

Uso:
    python3 herramientas/registrar_host_key.py

    Sin argumentos toma ENVIO_HOST, ENVIO_PUERTO y ENVIO_KNOWN_HOSTS del .env.
    Si ENVIO_KNOWN_HOSTS esta vacio, escribe en ~/.ssh/known_hosts.

    python3 herramientas/registrar_host_key.py --host 172.20.1.65 --puerto 4422
    python3 herramientas/registrar_host_key.py --salida .ssh/known_hosts

IMPORTANTE: este script confia en la llave que le entregue el servidor la
primera vez. Compare la huella que imprime contra la que le haya dado el
administrador del servidor antes de darla por buena.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

PUERTO_SSH_ESTANDAR = 22


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Registra la llave del servidor SFTP en un known_hosts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", help="Servidor. Por defecto ENVIO_HOST del .env.")
    parser.add_argument(
        "--puerto", type=int, help="Puerto. Por defecto ENVIO_PUERTO del .env."
    )
    parser.add_argument(
        "--salida",
        type=Path,
        help="Archivo known_hosts a escribir. Por defecto ENVIO_KNOWN_HOSTS "
        "del .env, o ~/.ssh/known_hosts.",
    )
    parser.add_argument("--env-file", type=Path, help="Ruta alternativa del .env.")
    parser.add_argument(
        "--timeout", type=int, default=15, help="Segundos de espera (por defecto 15)."
    )
    return parser


def huella_sha256(llave) -> str:
    """Huella en el mismo formato que muestra el cliente de OpenSSH."""
    digest = hashlib.sha256(llave.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode().rstrip("=")


def main(argv: list[str] | None = None) -> int:
    argumentos = construir_parser().parse_args(argv)

    try:
        import paramiko
    except ImportError:
        print(
            "[ERROR] Falta la libreria `paramiko`. Instalela con "
            "`pip install -r requirements.txt` o `apt install python3-paramiko`.",
            file=sys.stderr,
        )
        return 1

    host, puerto, salida = _resolver_parametros(argumentos)
    if not host:
        print(
            "[ERROR] No hay servidor: indique --host o defina ENVIO_HOST en el .env.",
            file=sys.stderr,
        )
        return 1

    print(f"Consultando la llave de {host}:{puerto} ...")
    transporte = paramiko.Transport((host, puerto))
    try:
        transporte.start_client(timeout=argumentos.timeout)
        llave = transporte.get_remote_server_key()
    except Exception as error:
        print(f"[ERROR] No fue posible obtener la llave: {error}", file=sys.stderr)
        return 1
    finally:
        transporte.close()

    # OpenSSH identifica los servidores en puertos no estandar como [host]:puerto
    nombre = host if puerto == PUERTO_SSH_ESTANDAR else f"[{host}]:{puerto}"

    llaves = paramiko.HostKeys()
    if salida.is_file():
        llaves.load(str(salida))
    llaves.add(nombre, llave.get_name(), llave)

    salida.parent.mkdir(parents=True, exist_ok=True)
    llaves.save(str(salida))
    salida.chmod(0o600)

    print(f"  Tipo de llave : {llave.get_name()}")
    print(f"  Huella        : {huella_sha256(llave)}")
    print(f"  Registrada en : {salida.resolve()}  (como {nombre})")
    print()
    print("Verifique la huella con el administrador del servidor antes de confiar en ella.")
    if not _esta_en_el_env(salida, argumentos):
        print(f"Agregue al .env:  ENVIO_KNOWN_HOSTS={salida.resolve()}")
    return 0


def _resolver_parametros(argumentos) -> tuple[str, int, Path]:
    """Combina los argumentos del CLI con lo definido en el .env."""
    host, puerto, salida = argumentos.host, argumentos.puerto, argumentos.salida

    if host is None or puerto is None or salida is None:
        try:
            from tracking_goals.infrastructure.config.settings import cargar_settings

            envio = cargar_settings(argumentos.env_file).envio
            host = host or envio.host
            puerto = puerto or envio.puerto
            salida = salida or envio.known_hosts
        except Exception as error:
            print(f"[AVISO] No se pudo leer el .env ({error}).", file=sys.stderr)

    return host or "", puerto or PUERTO_SSH_ESTANDAR, salida or _known_hosts_por_defecto()


def _known_hosts_por_defecto() -> Path:
    return Path.home() / ".ssh" / "known_hosts"


def _esta_en_el_env(salida: Path, argumentos) -> bool:
    try:
        from tracking_goals.infrastructure.config.settings import cargar_settings

        configurado = cargar_settings(argumentos.env_file).envio.known_hosts
        return configurado is not None and configurado.resolve() == salida.resolve()
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
