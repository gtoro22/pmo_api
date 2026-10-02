"""Pruebas del registro de host keys: infraestructura y punto de entrada."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.infrastructure.config.settings import ConfiguracionEnvio
from tracking_goals.infrastructure.transferencia.registro_host_keys import (
    RegistradorHostKeys,
    known_hosts_por_defecto,
    nombre_en_known_hosts,
)
from tracking_goals.interfaces.cli.registrar_host_key import (
    CODIGO_ERROR,
    CODIGO_OK,
    construir_parser,
)
from tracking_goals.interfaces.cli.registrar_host_key import main as registrar


@pytest.fixture
def config() -> ConfiguracionEnvio:
    return ConfiguracionEnvio(
        habilitado=True,
        protocolo="sftp",
        host="172.20.1.65",
        puerto=4422,
        usuario="userdocker",
        password="x",
    )


# =============================================================================
# Nombre del servidor en known_hosts
# =============================================================================


@pytest.mark.parametrize(
    "host,puerto,esperado",
    [
        ("172.20.1.65", 22, "172.20.1.65"),
        ("172.20.1.65", 4422, "[172.20.1.65]:4422"),
        ("sftp.miempresa.co", 2222, "[sftp.miempresa.co]:2222"),
    ],
)
def test_el_puerto_no_estandar_va_entre_corchetes(host, puerto, esperado):
    assert nombre_en_known_hosts(host, puerto) == esperado


def test_known_hosts_por_defecto_respeta_el_env(tmp_path, config):
    propio = tmp_path / "kh"
    assert known_hosts_por_defecto(replace(config, known_hosts=propio)) == propio


def test_known_hosts_por_defecto_cae_en_el_del_usuario(config):
    assert known_hosts_por_defecto(config) == Path.home() / ".ssh" / "known_hosts"


# =============================================================================
# Registrador (paramiko simulado)
# =============================================================================


class _LlaveFalsa:
    def __init__(self, cuerpo: bytes = b"llave-de-prueba"):
        self._cuerpo = cuerpo

    def asbytes(self):
        return self._cuerpo

    def get_name(self):
        return "ssh-rsa"

    def get_base64(self):
        import base64

        return base64.b64encode(self._cuerpo).decode()


class _TransporteFalso:
    ultimo: "_TransporteFalso | None" = None

    def __init__(self, direccion):
        self.direccion = direccion
        self.cerrado = False
        self.timeout = None
        _TransporteFalso.ultimo = self

    def start_client(self, timeout=None):
        self.timeout = timeout

    def get_remote_server_key(self):
        return _LlaveFalsa()

    def close(self):
        self.cerrado = True


def _parchear(monkeypatch, transporte=_TransporteFalso, llave_falsa=_LlaveFalsa):
    """Sustituye Transport y HostKeys manteniendo el resto de paramiko real."""
    import paramiko

    monkeypatch.setattr(paramiko, "Transport", transporte)

    class _HostKeys:
        def __init__(self):
            self.entradas: dict[str, tuple[str, object]] = {}
            self.guardado_en: str | None = None

        def load(self, ruta):
            pass

        def check(self, nombre, llave):
            return nombre in self.entradas

        def add(self, nombre, tipo, llave):
            self.entradas[nombre] = (tipo, llave)

        def save(self, ruta):
            self.guardado_en = ruta
            Path(ruta).write_text(
                "\n".join(f"{n} {t} ..." for n, (t, _) in self.entradas.items()),
                encoding="utf-8",
            )

    monkeypatch.setattr(paramiko, "HostKeys", _HostKeys)


def test_registra_la_llave_con_el_puerto_en_el_nombre(monkeypatch, tmp_path, config):
    _parchear(monkeypatch)
    destino = tmp_path / "known_hosts"

    registro = RegistradorHostKeys(config).registrar(destino)

    assert registro.nombre == "[172.20.1.65]:4422"
    assert registro.tipo == "ssh-rsa"
    assert registro.huella.startswith("SHA256:")
    assert registro.archivo == destino
    assert registro.ya_estaba is False
    assert destino.is_file()
    assert "[172.20.1.65]:4422" in destino.read_text(encoding="utf-8")
    assert _TransporteFalso.ultimo.direccion == ("172.20.1.65", 4422)
    assert _TransporteFalso.ultimo.cerrado is True


def test_crea_el_directorio_del_known_hosts(monkeypatch, tmp_path, config):
    _parchear(monkeypatch)
    destino = tmp_path / "sub" / "dir" / "known_hosts"

    RegistradorHostKeys(config).registrar(destino)

    assert destino.is_file()


def test_permisos_restringidos_del_archivo(monkeypatch, tmp_path, config):
    _parchear(monkeypatch)
    destino = tmp_path / "known_hosts"

    RegistradorHostKeys(config).registrar(destino)

    assert oct(destino.stat().st_mode)[-3:] == "600"


def test_sin_host_configurado_falla_con_mensaje_accionable(monkeypatch, tmp_path, config):
    _parchear(monkeypatch)

    with pytest.raises(ErrorDeEnvio, match="ENVIO_HOST"):
        RegistradorHostKeys(replace(config, host="")).registrar(tmp_path / "kh")


def test_servidor_inalcanzable_se_traduce_a_error_de_dominio(monkeypatch, tmp_path, config):
    class _TransporteQueFalla(_TransporteFalso):
        def start_client(self, timeout=None):
            raise OSError("Connection refused")

    _parchear(monkeypatch, transporte=_TransporteQueFalla)

    with pytest.raises(ErrorDeEnvio, match="No fue posible conectar"):
        RegistradorHostKeys(config).registrar(tmp_path / "kh")


def test_saludo_ssh_fallido_se_traduce_a_error_de_dominio(monkeypatch, tmp_path, config):
    import paramiko

    class _TransporteSinSSH(_TransporteFalso):
        def start_client(self, timeout=None):
            raise paramiko.SSHException("Error reading SSH protocol banner")

    _parchear(monkeypatch, transporte=_TransporteSinSSH)

    with pytest.raises(ErrorDeEnvio, match="saludo SSH"):
        RegistradorHostKeys(config).registrar(tmp_path / "kh")


def test_usa_el_timeout_de_la_configuracion(monkeypatch, tmp_path, config):
    _parchear(monkeypatch)

    RegistradorHostKeys(replace(config, timeout=7)).registrar(tmp_path / "kh")
    assert _TransporteFalso.ultimo.timeout == 7

    RegistradorHostKeys(config, timeout=3).registrar(tmp_path / "kh")
    assert _TransporteFalso.ultimo.timeout == 3


# =============================================================================
# Punto de entrada
# =============================================================================


def _env(tmp_path: Path, extra: str = "") -> Path:
    ruta = tmp_path / ".env"
    ruta.write_text(
        "AMAGI_API_BASE_URL=https://amagi.elearning.co\n"
        "AMAGI_API_TOKEN=token\n"
        f"LOG_DIR={tmp_path / 'logs'}\n"
        f"OUTPUT_DIR={tmp_path / 'output'}\n" + extra,
        encoding="utf-8",
    )
    return ruta


def test_los_argumentos_anulan_el_env(monkeypatch, tmp_path):
    _parchear(monkeypatch)
    for clave in ("ENVIO_HABILITADO", "ENVIO_HOST", "ENVIO_PUERTO", "ENVIO_USUARIO",
                  "ENVIO_PASSWORD", "ENVIO_KNOWN_HOSTS"):
        monkeypatch.delenv(clave, raising=False)

    env = _env(
        tmp_path,
        "ENVIO_HABILITADO=true\nENVIO_HOST=1.1.1.1\nENVIO_PUERTO=22\n"
        "ENVIO_USUARIO=u\nENVIO_PASSWORD=p\n",
    )
    destino = tmp_path / "known_hosts"

    codigo = registrar(
        ["--env-file", str(env), "--host", "172.20.1.65", "--puerto", "4422",
         "--salida", str(destino)]
    )

    assert codigo == CODIGO_OK
    assert "[172.20.1.65]:4422" in destino.read_text(encoding="utf-8")


def test_reporta_error_si_el_servidor_no_responde(monkeypatch, tmp_path):
    class _TransporteQueFalla(_TransporteFalso):
        def start_client(self, timeout=None):
            raise OSError("Connection refused")

    _parchear(monkeypatch, transporte=_TransporteQueFalla)
    for clave in ("ENVIO_HABILITADO", "ENVIO_HOST", "ENVIO_KNOWN_HOSTS"):
        monkeypatch.delenv(clave, raising=False)

    codigo = registrar(
        ["--env-file", str(_env(tmp_path)), "--host", "1.2.3.4", "--puerto", "4422",
         "--salida", str(tmp_path / "kh")]
    )

    assert codigo == CODIGO_ERROR


def test_configuracion_incompleta_devuelve_error(tmp_path, capsys):
    vacio = tmp_path / "vacio.env"
    vacio.write_text("", encoding="utf-8")

    assert registrar(["--env-file", str(vacio)]) == CODIGO_ERROR
    assert "AMAGI_API_BASE_URL" in capsys.readouterr().err


def test_el_parser_expone_las_opciones_documentadas():
    argumentos = construir_parser().parse_args(
        ["--host", "h", "--puerto", "2222", "--salida", "kh", "--timeout", "5"]
    )
    assert argumentos.host == "h"
    assert argumentos.puerto == 2222
    assert argumentos.salida == Path("kh")
    assert argumentos.timeout == 5
