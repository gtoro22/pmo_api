"""Pruebas de los adaptadores de entrega remota (SFTP / FTP) y su configuracion."""

from __future__ import annotations

import ftplib
from dataclasses import replace
from pathlib import Path

import pytest

from tracking_goals.application.dto.solicitud_exportacion import SolicitudExportacion
from tracking_goals.application.ports.transportador_archivos import (
    ResultadoEnvio,
    TransportadorArchivos,
)
from tracking_goals.application.use_cases.consultar_objetivos import ConsultarObjetivos
from tracking_goals.application.use_cases.exportar_objetivos_excel import (
    ExportarObjetivosExcel,
)
from tracking_goals.domain.exceptions import ErrorDeEnvio
from tracking_goals.domain.model.metadatos import Metadatos
from tracking_goals.domain.model.resultado_consulta import ResultadoConsulta
from tracking_goals.domain.model.usuario import Usuario
from tracking_goals.domain.repositories.repositorio_objetivos import RepositorioObjetivos
from tracking_goals.domain.services.aplanador_objetivos import AplanadorObjetivos
from tracking_goals.domain.value_objects.criterio_consulta import CriterioConsulta
from tracking_goals.infrastructure.config.settings import (
    ConfiguracionEnvio,
    ConfiguracionInvalida,
)
from tracking_goals.infrastructure.exportacion.exportador_excel import ExportadorExcel
from tracking_goals.infrastructure.transferencia import transportador_ftp
from tracking_goals.infrastructure.transferencia.fabrica import construir_transportador
from tracking_goals.infrastructure.transferencia.transportador_ftp import TransportadorFtp
from tracking_goals.infrastructure.transferencia.transportador_nulo import TransportadorNulo
from tracking_goals.infrastructure.transferencia.transportador_sftp import TransportadorSftp


@pytest.fixture
def archivo(tmp_path) -> Path:
    ruta = tmp_path / "reporte.xlsx"
    ruta.write_bytes(b"contenido-de-prueba")
    return ruta


@pytest.fixture
def config_sftp(tmp_path) -> ConfiguracionEnvio:
    return ConfiguracionEnvio(
        habilitado=True,
        protocolo="sftp",
        host="sftp.ejemplo.co",
        puerto=22,
        usuario="usuario",
        password="secreto",
        directorio_remoto="/reportes/objetivos",
    )


# =============================================================================
# Seleccion del adaptador
# =============================================================================


def test_deshabilitado_usa_el_transportador_nulo():
    transportador = construir_transportador(ConfiguracionEnvio(habilitado=False))
    assert isinstance(transportador, TransportadorNulo)


@pytest.mark.parametrize(
    "protocolo,esperado",
    [("sftp", TransportadorSftp), ("ftp", TransportadorFtp), ("ftps", TransportadorFtp)],
)
def test_cada_protocolo_construye_su_adaptador(protocolo, esperado):
    config = ConfiguracionEnvio(
        habilitado=True, protocolo=protocolo, host="h", usuario="u", password="p"
    )
    assert isinstance(construir_transportador(config), esperado)


def test_sin_paramiko_falla_al_armar_el_contenedor(monkeypatch):
    """Falta de dependencia: mensaje accionable y antes de consultar la API."""
    import builtins

    importar_real = builtins.__import__

    def sin_paramiko(nombre, *args, **kwargs):
        if nombre == "paramiko":
            raise ImportError("No module named 'paramiko'")
        return importar_real(nombre, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", sin_paramiko)
    config = ConfiguracionEnvio(
        habilitado=True, protocolo="sftp", host="h", usuario="u", password="p"
    )

    with pytest.raises(ErrorDeEnvio, match="pip install -r requirements.txt"):
        construir_transportador(config)


def test_sin_paramiko_ftps_sigue_funcionando(monkeypatch, archivo, config_ftp):
    """FTPS usa ftplib de la biblioteca estandar: no depende de paramiko."""
    import builtins

    importar_real = builtins.__import__

    def sin_paramiko(nombre, *args, **kwargs):
        if nombre == "paramiko":
            raise ImportError("No module named 'paramiko'")
        return importar_real(nombre, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", sin_paramiko)
    monkeypatch.setattr(transportador_ftp.ftplib, "FTP_TLS", _FtpFalso)

    transportador = construir_transportador(replace(config_ftp, protocolo="ftps"))
    assert transportador.enviar(archivo).enviado is True


def test_transportador_nulo_no_transfiere(archivo):
    resultado = TransportadorNulo().enviar(archivo)
    assert resultado.enviado is False
    assert resultado.destino is None


# =============================================================================
# SFTP (paramiko simulado)
# =============================================================================


class _SftpFalso:
    def __init__(self, existentes=(), tamano=len(b"contenido-de-prueba")):
        self.subidos: list[tuple[str, str]] = []
        self.creados: list[str] = []
        self._existentes = set(existentes)
        self._tamano = tamano

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def get_channel(self):
        class _Canal:
            def settimeout(self, _):
                pass

        return _Canal()

    def stat(self, ruta):
        if ruta in self._existentes or ruta in [d for _, d in self.subidos]:
            class _Info:
                st_size = self._tamano

            return _Info()
        raise OSError(f"no existe: {ruta}")

    def mkdir(self, ruta):
        self.creados.append(ruta)
        self._existentes.add(ruta)

    def put(self, local, remoto):
        self.subidos.append((local, remoto))
        self._existentes.add(remoto)


class _ClienteSshFalso:
    def __init__(self, sftp: _SftpFalso, al_conectar=None):
        self._sftp = sftp
        self._al_conectar = al_conectar
        self.conexion: dict | None = None
        self.politica = None
        self.cerrado = False

    def set_missing_host_key_policy(self, politica):
        self.politica = politica

    def load_system_host_keys(self):
        pass

    def load_host_keys(self, ruta):
        pass

    def connect(self, **kwargs):
        if self._al_conectar is not None:
            raise self._al_conectar
        self.conexion = kwargs

    def open_sftp(self):
        return self._sftp

    def close(self):
        self.cerrado = True


def _parchear_paramiko(monkeypatch, cliente):
    """Sustituye `paramiko.SSHClient` conservando las clases de excepcion reales."""
    import paramiko

    monkeypatch.setattr(paramiko, "SSHClient", lambda: cliente)
    return paramiko


def test_sftp_sube_el_archivo_al_directorio_configurado(monkeypatch, archivo, config_sftp):
    sftp = _SftpFalso(existentes={"/reportes/objetivos"})
    cliente = _ClienteSshFalso(sftp)
    _parchear_paramiko(monkeypatch, cliente)

    resultado = TransportadorSftp(config_sftp).enviar(archivo)

    assert resultado.enviado is True
    assert resultado.protocolo == "sftp"
    assert resultado.destino == "/reportes/objetivos/reporte.xlsx"
    assert sftp.subidos == [(str(archivo), "/reportes/objetivos/reporte.xlsx")]
    assert cliente.conexion["hostname"] == "sftp.ejemplo.co"
    assert cliente.conexion["username"] == "usuario"
    assert cliente.conexion["password"] == "secreto"
    assert cliente.cerrado is True


def test_sftp_crea_el_directorio_remoto_si_no_existe(monkeypatch, archivo, config_sftp):
    sftp = _SftpFalso()
    _parchear_paramiko(monkeypatch, _ClienteSshFalso(sftp))

    TransportadorSftp(config_sftp).enviar(archivo)

    assert sftp.creados == ["/reportes", "/reportes/objetivos"]


def test_sftp_respeta_el_nombre_remoto_configurado(monkeypatch, archivo, config_sftp):
    sftp = _SftpFalso(existentes={"/reportes/objetivos"})
    _parchear_paramiko(monkeypatch, _ClienteSshFalso(sftp))

    config = replace(config_sftp, nombre_remoto="objetivos_ultimo.xlsx")
    resultado = TransportadorSftp(config).enviar(archivo)

    assert resultado.destino == "/reportes/objetivos/objetivos_ultimo.xlsx"


def test_sftp_verifica_host_key_por_defecto(monkeypatch, archivo, config_sftp):
    import paramiko

    sftp = _SftpFalso(existentes={"/reportes/objetivos"})
    cliente = _ClienteSshFalso(sftp)
    _parchear_paramiko(monkeypatch, cliente)

    TransportadorSftp(config_sftp).enviar(archivo)

    assert isinstance(cliente.politica, paramiko.RejectPolicy)


def test_sftp_acepta_cualquier_host_key_si_se_desactiva(monkeypatch, archivo, config_sftp):
    import paramiko

    sftp = _SftpFalso(existentes={"/reportes/objetivos"})
    cliente = _ClienteSshFalso(sftp)
    _parchear_paramiko(monkeypatch, cliente)

    TransportadorSftp(replace(config_sftp, verificar_host_key=False)).enviar(archivo)

    assert isinstance(cliente.politica, paramiko.AutoAddPolicy)


def test_sftp_traduce_el_fallo_de_autenticacion(monkeypatch, archivo, config_sftp):
    import paramiko

    cliente = _ClienteSshFalso(
        _SftpFalso(), al_conectar=paramiko.AuthenticationException("denegado")
    )
    _parchear_paramiko(monkeypatch, cliente)

    with pytest.raises(ErrorDeEnvio, match="Autenticacion SFTP rechazada"):
        TransportadorSftp(config_sftp).enviar(archivo)
    assert cliente.cerrado is True


def test_sftp_detecta_transferencia_incompleta(monkeypatch, archivo, config_sftp):
    sftp = _SftpFalso(existentes={"/reportes/objetivos"}, tamano=3)
    _parchear_paramiko(monkeypatch, _ClienteSshFalso(sftp))

    with pytest.raises(ErrorDeEnvio, match="incompleta"):
        TransportadorSftp(config_sftp).enviar(archivo)


# =============================================================================
# FTP / FTPS (ftplib simulado)
# =============================================================================


class _FtpFalso:
    instancia: "_FtpFalso | None" = None

    def __init__(self, dirs_existentes=("/reportes",)):
        self.subidos: list[str] = []
        self.creados: list[str] = []
        self.cwd_visitados: list[str] = []
        self.login_args: dict | None = None
        self.pasivo: bool | None = None
        self.tls_activado = False
        self.cerrado = False
        self._dirs = set(dirs_existentes)
        _FtpFalso.instancia = self

    def connect(self, host, port, timeout):
        self.conexion = {"host": host, "port": port, "timeout": timeout}

    def login(self, user, passwd):
        self.login_args = {"user": user, "passwd": passwd}

    def prot_p(self):
        self.tls_activado = True

    def set_pasv(self, valor):
        self.pasivo = valor

    def cwd(self, ruta):
        if ruta not in self._dirs and ruta != "/":
            raise ftplib.error_perm(f"550 no existe: {ruta}")
        self.cwd_visitados.append(ruta)

    def mkd(self, ruta):
        self.creados.append(ruta)
        self._dirs.add(ruta)

    def storbinary(self, comando, flujo):
        self.subidos.append(comando)
        flujo.read()

    def size(self, nombre):
        return len(b"contenido-de-prueba")

    def quit(self):
        self.cerrado = True


@pytest.fixture
def config_ftp() -> ConfiguracionEnvio:
    return ConfiguracionEnvio(
        habilitado=True,
        protocolo="ftp",
        host="ftp.ejemplo.co",
        puerto=21,
        usuario="usuario",
        password="secreto",
        directorio_remoto="/reportes",
    )


def test_ftp_sube_el_archivo(monkeypatch, archivo, config_ftp):
    monkeypatch.setattr(transportador_ftp.ftplib, "FTP", _FtpFalso)

    resultado = TransportadorFtp(config_ftp).enviar(archivo)
    falso = _FtpFalso.instancia

    assert resultado.enviado is True
    assert resultado.destino == "/reportes/reporte.xlsx"
    assert falso.subidos == ["STOR reporte.xlsx"]
    assert falso.login_args == {"user": "usuario", "passwd": "secreto"}
    assert falso.pasivo is True
    assert falso.tls_activado is False
    assert falso.cerrado is True


def test_ftps_activa_el_cifrado_del_canal_de_datos(monkeypatch, archivo, config_ftp):
    monkeypatch.setattr(transportador_ftp.ftplib, "FTP_TLS", _FtpFalso)

    resultado = TransportadorFtp(replace(config_ftp, protocolo="ftps")).enviar(archivo)

    assert resultado.protocolo == "ftps"
    assert _FtpFalso.instancia.tls_activado is True


def test_ftp_crea_el_directorio_remoto_si_falta(monkeypatch, archivo, config_ftp):
    monkeypatch.setattr(transportador_ftp.ftplib, "FTP", lambda: _FtpFalso(dirs_existentes=()))

    TransportadorFtp(replace(config_ftp, directorio_remoto="/salidas/2026")).enviar(archivo)

    assert _FtpFalso.instancia.creados == ["salidas", "2026"]


def test_ftp_traduce_el_rechazo_del_servidor(monkeypatch, archivo, config_ftp):
    class _FtpQueRechaza(_FtpFalso):
        def login(self, user, passwd):
            raise ftplib.error_perm("530 login incorrect")

    monkeypatch.setattr(transportador_ftp.ftplib, "FTP", _FtpQueRechaza)

    with pytest.raises(ErrorDeEnvio, match="rechazo la operacion"):
        TransportadorFtp(config_ftp).enviar(archivo)


# =============================================================================
# Validacion de configuracion
# =============================================================================


def _cargar(monkeypatch, tmp_path, **variables):
    from tracking_goals.infrastructure.config.settings import cargar_settings

    base = {
        "AMAGI_API_BASE_URL": "https://amagi.elearning.co",
        "AMAGI_API_TOKEN": "token",
        "LOG_DIR": str(tmp_path / "logs"),
        "OUTPUT_DIR": str(tmp_path / "output"),
    }
    for clave in list(base) + [
        "ENVIO_HABILITADO", "ENVIO_PROTOCOLO", "ENVIO_HOST", "ENVIO_PUERTO",
        "ENVIO_USUARIO", "ENVIO_PASSWORD", "ENVIO_LLAVE_PRIVADA",
        "ENVIO_DIRECTORIO_REMOTO", "ENVIO_KNOWN_HOSTS", "ENVIO_VERIFICAR_HOST_KEY",
    ]:
        monkeypatch.delenv(clave, raising=False)
    for clave, valor in {**base, **variables}.items():
        monkeypatch.setenv(clave, valor)
    vacio = tmp_path / "vacio.env"
    vacio.touch()
    return cargar_settings(vacio)


def test_envio_deshabilitado_no_exige_parametros(monkeypatch, tmp_path):
    settings = _cargar(monkeypatch, tmp_path, ENVIO_HABILITADO="false")
    assert settings.envio.habilitado is False
    assert settings.envio.describir() == "deshabilitado"


def test_envio_habilitado_exige_host_y_usuario(monkeypatch, tmp_path):
    with pytest.raises(ConfiguracionInvalida, match="ENVIO_HOST"):
        _cargar(monkeypatch, tmp_path, ENVIO_HABILITADO="true")


def test_envio_habilitado_exige_credencial(monkeypatch, tmp_path):
    with pytest.raises(ConfiguracionInvalida, match="ENVIO_PASSWORD"):
        _cargar(
            monkeypatch, tmp_path,
            ENVIO_HABILITADO="true", ENVIO_HOST="h", ENVIO_USUARIO="u",
        )


def test_protocolo_invalido_se_rechaza(monkeypatch, tmp_path):
    with pytest.raises(ConfiguracionInvalida, match="ENVIO_PROTOCOLO"):
        _cargar(
            monkeypatch, tmp_path,
            ENVIO_HABILITADO="true", ENVIO_PROTOCOLO="scp",
            ENVIO_HOST="h", ENVIO_USUARIO="u", ENVIO_PASSWORD="p",
        )


def test_llave_privada_inexistente_se_rechaza(monkeypatch, tmp_path):
    with pytest.raises(ConfiguracionInvalida, match="llave privada"):
        _cargar(
            monkeypatch, tmp_path,
            ENVIO_HABILITADO="true", ENVIO_HOST="h", ENVIO_USUARIO="u",
            ENVIO_LLAVE_PRIVADA=str(tmp_path / "no_existe.pem"),
        )


def test_puerto_por_defecto_segun_protocolo(monkeypatch, tmp_path):
    sftp = _cargar(
        monkeypatch, tmp_path,
        ENVIO_HABILITADO="true", ENVIO_PROTOCOLO="sftp",
        ENVIO_HOST="h", ENVIO_USUARIO="u", ENVIO_PASSWORD="p",
    )
    ftp = _cargar(
        monkeypatch, tmp_path,
        ENVIO_HABILITADO="true", ENVIO_PROTOCOLO="ftp",
        ENVIO_HOST="h", ENVIO_USUARIO="u", ENVIO_PASSWORD="p",
    )
    assert sftp.envio.puerto == 22
    assert ftp.envio.puerto == 21


def test_descripcion_no_expone_la_contrasena(monkeypatch, tmp_path):
    settings = _cargar(
        monkeypatch, tmp_path,
        ENVIO_HABILITADO="true", ENVIO_HOST="h", ENVIO_USUARIO="u",
        ENVIO_PASSWORD="contrasena-secreta",
    )
    assert "contrasena-secreta" not in settings.envio.describir()


# =============================================================================
# Integracion con el caso de uso
# =============================================================================


class _RepositorioFijo(RepositorioObjetivos):
    def consultar(self, criterio: CriterioConsulta) -> ResultadoConsulta:
        return ResultadoConsulta(
            usuarios=(Usuario(id=1, identificacion="1", nombres="A", apellidos="B"),),
            metadatos=Metadatos(1, 50, 1, 1, None, "2026-08-24T15:55:17-05:00", None),
        )


class _TransportadorEspia(TransportadorArchivos):
    def __init__(self, error: Exception | None = None):
        self.recibidos: list[Path] = []
        self._error = error

    def enviar(self, archivo: Path) -> ResultadoEnvio:
        if self._error is not None:
            raise self._error
        self.recibidos.append(archivo)
        return ResultadoEnvio(enviado=True, protocolo="sftp", destino=f"/remoto/{archivo.name}")


def _caso_de_uso(transportador) -> ExportarObjetivosExcel:
    return ExportarObjetivosExcel(
        consultar_objetivos=ConsultarObjetivos(_RepositorioFijo()),
        aplanador=AplanadorObjetivos(),
        exportador=ExportadorExcel(),
        transportador=transportador,
    )


def test_el_caso_de_uso_entrega_el_excel_generado(tmp_path):
    espia = _TransportadorEspia()
    destino = tmp_path / "reporte.xlsx"

    resumen = _caso_de_uso(espia).ejecutar(SolicitudExportacion(CriterioConsulta(), destino))

    assert espia.recibidos == [destino]
    assert resumen.envio.enviado is True
    assert resumen.envio.destino == "/remoto/reporte.xlsx"


def test_la_opcion_no_enviar_omite_la_entrega(tmp_path):
    espia = _TransportadorEspia()
    destino = tmp_path / "reporte.xlsx"

    resumen = _caso_de_uso(espia).ejecutar(
        SolicitudExportacion(CriterioConsulta(), destino, enviar=False)
    )

    assert espia.recibidos == []
    assert resumen.envio.enviado is False
    assert destino.exists()


def test_si_falla_el_envio_el_excel_queda_en_disco(tmp_path):
    espia = _TransportadorEspia(error=ErrorDeEnvio("servidor caido"))
    destino = tmp_path / "reporte.xlsx"

    with pytest.raises(ErrorDeEnvio):
        _caso_de_uso(espia).ejecutar(SolicitudExportacion(CriterioConsulta(), destino))

    assert destino.exists(), "el archivo generado no debe perderse si falla la entrega"
