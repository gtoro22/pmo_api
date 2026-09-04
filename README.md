# Invocador Tracking Goals — Amagi

Invocador en Python del servicio web de consulta de evaluaciones, perspectivas y
objetivos de Amagi (`GET /api/v1/tracking_goals`). Consulta el servicio desde
línea de comandos y exporta el resultado a un archivo Excel **plano** con todos
los parámetros del JSON de salida.

## Características

- Arquitectura **DDD** por capas (dominio / aplicación / infraestructura / interfaces).
- Ejecutable desde **CMD / terminal** con `python main.py`, sin instalar el proyecto ni usar venv.
- **Docker** y **docker compose** listos para usar.
- **Endpoint base y token en `.env`**; las rutas de la API viven en la capa de infraestructura.
- **Log de inicio de proceso** en consola y archivo por ejecución.
- **Excel** con la jerarquía usuario → evaluación → perspectiva → objetivo aplanada,
  incluyendo la sección `meta` y el `status`.
- **Entrega automática por SFTP, FTP o FTPS**, habilitable desde el `.env`.

---

## 1. Arquitectura (DDD)

```
main.py                            # ◄ Punto de entrada: python main.py --project 2026
src/tracking_goals/
├── domain/                        # Núcleo de negocio, sin dependencias externas
│   ├── model/                     # Entidades y objetos de valor
│   │   ├── usuario.py             #   Usuario
│   │   ├── evaluacion.py          #   Evaluación
│   │   ├── perspectiva.py         #   Perspectiva
│   │   ├── objetivo.py            #   Objetivo
│   │   ├── metadatos.py           #   meta (paginación / sincronización)
│   │   ├── resultado_consulta.py  #   Raíz de agregado (results + meta + status)
│   │   └── registro_plano.py      #   Fila plana del reporte (define las columnas)
│   ├── value_objects/
│   │   └── criterio_consulta.py   # project / identity / page / per_page / updated_since
│   ├── repositories/
│   │   └── repositorio_objetivos.py   # PUERTO de salida (abstracto)
│   ├── services/
│   │   └── aplanador_objetivos.py     # Servicio de dominio: aplanado jerárquico
│   └── exceptions.py
│
├── application/                   # Orquestación de casos de uso
│   ├── use_cases/
│   │   ├── consultar_objetivos.py        # Consulta (con paginación opcional)
│   │   └── exportar_objetivos_excel.py   # Consulta + aplanado + exportación
│   ├── ports/
│   │   ├── exportador_registros.py       # PUERTO de escritura del reporte
│   │   └── transportador_archivos.py     # PUERTO de entrega remota
│   └── dto/
│       └── solicitud_exportacion.py      # SolicitudExportacion / ResumenEjecucion
│
├── infrastructure/                # Adaptadores concretos
│   ├── config/settings.py                # Carga del .env (endpoint base + secretos)
│   ├── http/
│   │   ├── endpoints.py                  # ◄ RUTAS DE LA API (no van en el .env)
│   │   ├── cliente_http.py               # Bearer token, timeouts, reintentos
│   │   ├── mapeadores.py                 # JSON → dominio (anticorruption layer)
│   │   └── repositorio_objetivos_api.py  # Implementación del puerto
│   ├── exportacion/exportador_excel.py   # Implementación del puerto (openpyxl)
│   ├── transferencia/                    # Implementaciones del puerto de entrega
│   │   ├── fabrica.py                    #   elige el adaptador según el .env
│   │   ├── transportador_sftp.py         #   SFTP (paramiko)
│   │   ├── transportador_ftp.py          #   FTP y FTPS (ftplib)
│   │   └── transportador_nulo.py         #   envío deshabilitado (Null Object)
│   └── logging/configurador.py           # Log de inicio/fin de proceso
│
└── interfaces/cli/                # Punto de entrada
    ├── argumentos.py              # Definición de argumentos
    ├── contenedor.py              # Raíz de composición (inyección de dependencias)
    └── main.py                    # main()
```

**Regla de dependencias:** `interfaces → application → domain`, e
`infrastructure → domain`. El dominio no conoce a `requests` ni a `openpyxl`;
los adaptadores se inyectan en `interfaces/cli/contenedor.py`.

### Endpoint base vs. rutas

| Dato | Dónde vive | Ejemplo |
|------|-----------|---------|
| Endpoint base | `.env` → `AMAGI_API_BASE_URL` | `https://amagi.elearning.co` |
| Token | `.env` → `AMAGI_API_TOKEN` | `b1f941…` |
| Ruta del llamado | `infrastructure/http/endpoints.py` | `/api/v1/tracking_goals` |

---

## 2. Configuración

```bash
cp .env.example .env
```

Editar `.env`:

```dotenv
AMAGI_API_BASE_URL=https://amagi.elearning.co
AMAGI_API_TOKEN=su-bearer-token
```

| Variable | Descripción | Defecto |
|----------|-------------|---------|
| `AMAGI_API_BASE_URL` | Endpoint base del servicio (**obligatorio**) | — |
| `AMAGI_API_TOKEN` | Bearer token de autenticación (**obligatorio**) | — |
| `AMAGI_API_TIMEOUT` | Timeout por petición (segundos) | `30` |
| `AMAGI_API_MAX_REINTENTOS` | Reintentos ante errores de red / 5xx / 429 | `3` |
| `AMAGI_API_BACKOFF` | Base del backoff exponencial | `2` |
| `AMAGI_API_VERIFICAR_SSL` | Verificación de certificados TLS | `true` |
| `AMAGI_PROYECTO_DEFECTO` | Proyecto usado si no se pasa `--project` | *(vacío)* |
| `AMAGI_PER_PAGE_DEFECTO` | Usuarios por página | `50` |
| `LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` | `INFO` |
| `LOG_DIR` | Carpeta de logs | `logs` |
| `OUTPUT_DIR` | Carpeta de salida de los Excel | `output` |

Entrega remota (ver sección 5):

| Variable | Descripción | Defecto |
|----------|-------------|---------|
| `ENVIO_HABILITADO` | Interruptor principal del envío | `false` |
| `ENVIO_PROTOCOLO` | `sftp` · `ftp` · `ftps` | `sftp` |
| `ENVIO_HOST` | Servidor destino | — |
| `ENVIO_PUERTO` | Puerto | `22` sftp · `21` ftp/ftps |
| `ENVIO_USUARIO` | Usuario | — |
| `ENVIO_PASSWORD` | Contraseña | — |
| `ENVIO_LLAVE_PRIVADA` | Ruta a la llave privada (alternativa a la contraseña, solo sftp) | — |
| `ENVIO_LLAVE_PASSPHRASE` | Passphrase de la llave | — |
| `ENVIO_DIRECTORIO_REMOTO` | Carpeta destino en el servidor | `.` |
| `ENVIO_NOMBRE_REMOTO` | Nombre fijo remoto. Vacío conserva el nombre con fecha | *(vacío)* |
| `ENVIO_CREAR_DIRECTORIO` | Crea la carpeta remota y sus padres si no existen | `true` |
| `ENVIO_TIMEOUT` | Timeout de conexión y transferencia (segundos) | `30` |
| `ENVIO_VERIFICAR_HOST_KEY` | Exige que la llave del servidor esté en `known_hosts` | `true` |
| `ENVIO_KNOWN_HOSTS` | `known_hosts` propio. Vacío usa el del sistema | *(vacío)* |
| `ENVIO_FTP_PASIVO` | Modo pasivo (solo ftp/ftps) | `true` |

> El archivo `.env` está en `.gitignore`: **nunca** se versionan el token ni las
> credenciales del servidor de archivos.

---

## 3. Ejecución desde CMD / terminal

### Forma recomendada: `main.py`

Solo se instalan las tres librerías; **el proyecto no se instala como paquete y
no requiere entorno virtual**:

```bat
pip install -r requirements.txt

python main.py --project 2026 --identity 5555553333
```

```bat
:: Todas las páginas del proyecto, 100 usuarios por página
python main.py --project 2026 --per-page 100 --todas-las-paginas

:: Sincronización incremental + archivo de salida explícito
python main.py --updated-since 2026-07-29T10:38:00-05:00 --salida C:\reportes\objetivos.xlsx

:: Ver el detalle de cada petición HTTP
python main.py --project 2026 --log-level DEBUG

:: Ayuda
python main.py --help
```

`main.py` agrega `src/` al path de importación y delega en
`interfaces/cli/main.py`. Puede invocarse con ruta absoluta desde cualquier
carpeta (`python C:\ruta\pmo_api\main.py --project 2026`); en ese caso el Excel
y los logs se crean en el directorio actual, y el `.env` puede indicarse con
`--env-file`.

Si `python` no responde en Windows, usar el lanzador `py`:

```bat
py -m pip install -r requirements.txt
py main.py --project 2026
```

### Alternativa: instalar el paquete

Habilita el comando `tracking-goals` y la ejecución por módulo desde cualquier
directorio:

```bash
pip install -e .

tracking-goals --project 2026 --identity 5555553333
python -m tracking_goals --project 2026
```

> Si `tracking-goals` no se reconoce, la carpeta `Scripts` de Python no está en
> el `PATH`. Se ubica con
> `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"`, o se
> evita el problema usando `python main.py`.

### Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `--project`, `-p` | Código o nombre del proyecto (ej. `2026`) |
| `--identity`, `-i` | Número de identificación del usuario |
| `--updated-since` | Marca temporal ISO 8601 para consulta incremental |
| `--page` | Página inicial (por defecto `1`) |
| `--per-page` | Usuarios por página |
| `--todas-las-paginas` / `--all-pages` | Recorre hasta `total_pages` y consolida |
| `--salida`, `-o` | Ruta del `.xlsx` a generar |
| `--enviar` | Fuerza el envío remoto aunque `ENVIO_HABILITADO` sea `false` |
| `--no-enviar` | Omite el envío aunque `ENVIO_HABILITADO` sea `true` |
| `--log-level` | Nivel de detalle del log |
| `--env-file` | Ruta alternativa del `.env` |

Códigos de salida: `0` correcto · `1` error · `130` interrumpido.

---

## 4. Docker

Con Docker no hace falta instalar Python ni las dependencias en el servidor:
todo queda dentro de la imagen. Es la vía recomendada cuando no se tienen
permisos para instalar paquetes en la máquina.

### Puesta en marcha en un servidor Linux

```bash
git clone -b claude/tracking-goals-api-invoker-8nhx0x \
    https://github.com/gtoro22/pmo_api.git
cd pmo_api

cp .env.example .env
nano .env                      # completar token y datos del SFTP

# Las carpetas deben existir y pertenecer al usuario del contenedor (uid 1000)
mkdir -p output logs
sudo chown -R 1000:1000 output logs

docker compose build
docker compose run --rm tracking-goals --todas-las-paginas
```

El Excel y el log aparecen en `./output` y `./logs` del host.

> Si prefiere que los archivos queden con su propio usuario en lugar del uid
> 1000, exporte `DOCKER_UID=$(id -u)` y `DOCKER_GID=$(id -g)` antes de
> `docker compose run`; el `docker-compose.yml` los toma de ahí.

### Uso diario

```bash
# Los argumentos van después del nombre del servicio
docker compose run --rm tracking-goals --todas-las-paginas
docker compose run --rm tracking-goals --project 2026 --identity 5555553333
docker compose run --rm tracking-goals --help
```

Programarlo cada día a las 6:00 con cron (`crontab -e`):

```cron
0 6 * * * cd /ruta/a/pmo_api && /usr/bin/docker compose run --rm tracking-goals --todas-las-paginas >> logs/cron.log 2>&1
```

### Si el build falla con «Network is unreachable»

```
ERROR: Could not find a version that satisfies the requirement requests==2.32.3
Failed to establish a new connection: [Errno 101] Network is unreachable
```

Significa que el **contenedor de build** no alcanza PyPI, aunque el host sí haya
descargado la imagen base. Es habitual en redes corporativas donde la red bridge
de Docker no tiene salida. Tres alternativas, de más simple a más robusta:

**1. Construir usando la red del host**

```bash
docker build --network=host -t tracking-goals-invoker:1.0.0 .
docker compose run --rm --no-build tracking-goals --todas-las-paginas
```

**2. Pasar el proxy corporativo al build**, si la salida es por proxy:

```bash
docker build \
  --build-arg HTTP_PROXY=$HTTP_PROXY \
  --build-arg HTTPS_PROXY=$HTTPS_PROXY \
  -t tracking-goals-invoker:1.0.0 .
```

**3. Instalar desde wheels descargados en el host** (funciona siempre que el
host alcance PyPI, sin importar la red del contenedor):

```bash
python3 -m venv .venv
.venv/bin/pip download -r requirements.txt -d wheels

docker compose -f docker-compose.offline.yml build
docker compose -f docker-compose.offline.yml run --rm tracking-goals --todas-las-paginas
```

`Dockerfile.offline` instala con `--no-index --find-links=/wheels`, así que el
build no intenta ninguna conexión. La carpeta `wheels/` pesa unos 8 MB y está en
`.gitignore`: se regenera cuando cambien las dependencias.

### Servidor sin acceso a internet en absoluto

Si el host tampoco alcanza Docker Hub ni PyPI, construya en otra máquina y
transfiera la imagen ya armada:

```bash
# En la máquina con internet
docker compose build
docker save tracking-goals-invoker:1.0.0 | gzip > tracking-goals.tar.gz

# Copiar el .tar.gz al servidor, y allí:
gunzip -c tracking-goals.tar.gz | docker load

# Ejecutar sin volver a construir (usa la imagen ya cargada)
docker compose run --rm --no-build tracking-goals --todas-las-paginas
```

### Servidor sin pip, sin venv y sin salida a PyPI

Es el caso más restrictivo: `pip install` falla por PEP 668, `python3 -m venv`
falla porque falta `python3-venv`, y ni el host ni el contenedor alcanzan PyPI.
Se resuelve llevando las dependencias ya descomprimidas y apuntando
`PYTHONPATH` a ellas. **No requiere pip, ni entorno virtual, ni permisos de
administrador en el servidor.**

En una máquina con internet (sirve la de escritorio, aunque sea Windows):

```bash
bash herramientas/preparar_dependencias.sh
```

Descarga los wheels de **Linux** —independientemente del sistema donde se
ejecute— y los descomprime en `libs/` (unos 27 MB). Copiar esa carpeta al
servidor, junto al proyecto, y ejecutar:

```bash
PYTHONPATH=libs python3 main.py --todas-las-paginas
```

Para cron:

```cron
0 6 * * * cd /ruta/a/pmo_api && PYTHONPATH=libs /usr/bin/python3 main.py --todas-las-paginas >> logs/cron.log 2>&1
```

`libs/` está en `.gitignore`: se regenera cuando cambien las dependencias.

> Si solo se usa FTP o FTPS (no SFTP), `paramiko` no hace falta y bastan los
> tres paquetes de Python puro, que son unos pocos MB.

### Instalación con paquetes del sistema

Si se tiene `sudo` y el servidor alcanza los repositorios de Debian/Ubuntu
—habitual incluso cuando PyPI está bloqueado, porque suele haber un espejo
interno—, es la vía más limpia:

```bash
sudo apt install python3-requests python3-openpyxl python3-paramiko python3-dotenv

python3 main.py --todas-las-paginas
```

No hace falta pip ni entorno virtual. Las versiones que trae Debian 12 son más
antiguas que las fijadas en `requirements.txt` (requests 2.28, openpyxl 3.0.9,
paramiko 2.12, python-dotenv 0.21), pero el invocador es compatible con ellas:
la suite de 68 pruebas pasa completa contra esas versiones.

### Alternativa sin Docker: entorno virtual

En Debian/Ubuntu, `pip install` contra el Python del sistema falla con
`externally-managed-environment` (PEP 668). **No hace falta sudo**: un entorno
virtual lo resuelve y es la vía que recomienda el propio mensaje de error.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python main.py --todas-las-paginas
```

No es necesario activar el entorno: basta invocar `.venv/bin/python`. Para cron:

```cron
0 6 * * * cd /ruta/a/pmo_api && .venv/bin/python main.py --todas-las-paginas >> logs/cron.log 2>&1
```

> Si `python3 -m venv` falla por `ensurepip`, falta el paquete del sistema:
> `sudo apt install python3-venv`.

### Actualizar a una versión nueva del código

```bash
git pull
docker compose build
```

Sin compose:

```bash
docker build -t tracking-goals-invoker:1.0.0 .

docker run --rm --env-file .env ^
  -v "%cd%\output:/app/output" -v "%cd%\logs:/app/logs" ^
  tracking-goals-invoker:1.0.0 --project 2026 --identity 5555553333
```

(en Linux/macOS usar `\` y `$(pwd)` en lugar de `^` y `%cd%`)

Los volúmenes `./output` y `./logs` exponen el Excel y los logs en el host.
La imagen corre con un usuario sin privilegios (`invoker`, uid 1000).

### Entrega por SFTP desde el contenedor

El contenedor no tiene `~/.ssh/known_hosts`, así que con la verificación de host
key activada (el valor por defecto) hay que montarlo:

```bash
mkdir -p .ssh
ssh-keyscan -p 22 172.20.1.65 > .ssh/known_hosts
```

Descomentar el volumen correspondiente en `docker-compose.yml` y añadir al `.env`:

```dotenv
ENVIO_KNOWN_HOSTS=/app/.ssh/known_hosts
```

Si autentica con llave privada, montarla igual y apuntar
`ENVIO_LLAVE_PRIVADA=/app/.ssh/id_ed25519`.

Sobre la red: un destino en la LAN (por ejemplo `172.20.1.65`) es alcanzable
desde el contenedor con la red bridge por defecto. Si el servidor SFTP corre en
la **misma máquina** que Docker, usar `host.docker.internal` en `ENVIO_HOST`.

---

## 5. Entrega remota del Excel (SFTP / FTP / FTPS)

Una vez generado el archivo, el invocador puede subirlo a un servidor. Está
**deshabilitado por defecto**: con `ENVIO_HABILITADO=false` el Excel solo queda
en disco y ninguna otra variable de la sección se lee.

### Ejemplo SFTP con contraseña

```dotenv
ENVIO_HABILITADO=true
ENVIO_PROTOCOLO=sftp
ENVIO_HOST=sftp.miempresa.co
ENVIO_USUARIO=integraciones
ENVIO_PASSWORD=su-contraseña
ENVIO_DIRECTORIO_REMOTO=/reportes/objetivos
```

### Ejemplo SFTP con llave privada

```dotenv
ENVIO_HABILITADO=true
ENVIO_PROTOCOLO=sftp
ENVIO_HOST=sftp.miempresa.co
ENVIO_USUARIO=integraciones
ENVIO_LLAVE_PRIVADA=C:\claves\integraciones_id_ed25519
ENVIO_LLAVE_PASSPHRASE=
ENVIO_DIRECTORIO_REMOTO=/reportes/objetivos
```

### Ejemplo FTPS

```dotenv
ENVIO_HABILITADO=true
ENVIO_PROTOCOLO=ftps
ENVIO_HOST=ftp.miempresa.co
ENVIO_USUARIO=integraciones
ENVIO_PASSWORD=su-contraseña
ENVIO_DIRECTORIO_REMOTO=/entrantes
ENVIO_FTP_PASIVO=true
```

### Comportamiento

- El archivo **siempre se conserva en local**, aunque el envío falle.
- Si `ENVIO_CREAR_DIRECTORIO=true`, la carpeta remota y sus padres se crean.
- Terminada la transferencia se compara el tamaño remoto contra el local; si no
  coinciden, la ejecución falla en lugar de dar por buena una subida parcial.
- `ENVIO_NOMBRE_REMOTO` permite dejar siempre el mismo nombre en el servidor
  (útil si el consumidor lee una ruta fija). Vacío conserva el nombre con fecha.
- La configuración se valida **al arrancar**, antes de consultar la API: si falta
  el host o la credencial, el proceso termina sin gastar la llamada al servicio.

### Anular el `.env` en una ejecución puntual

```bat
:: Genera el Excel sin subirlo, aunque el .env tenga el envío activo
python main.py --project 2026 --no-enviar

:: Sube el archivo aunque el .env tenga ENVIO_HABILITADO=false
:: (los datos de conexión deben estar igualmente en el .env)
python main.py --project 2026 --enviar
```

### Seguridad

`ENVIO_VERIFICAR_HOST_KEY=true` (el valor por defecto) exige que la llave del
servidor SFTP esté en `known_hosts`; si no está, la conexión se rechaza. Para
registrarla:

```bash
ssh-keyscan -p 22 sftp.miempresa.co >> ~/.ssh/known_hosts
```

o apuntar `ENVIO_KNOWN_HOSTS` a un archivo propio. Ponerlo en `false` acepta
cualquier llave y deja la conexión expuesta a suplantación del servidor: el log
lo advierte en cada ejecución.

El protocolo `ftp` no cifra nada — credenciales y archivo viajan en claro, y el
log lo advierte. Prefiera `sftp` o `ftps`.

---

## 6. Salida en Excel

Una fila por objetivo, con la jerarquía repetida y la sección `meta` incorporada
en cada fila (49 columnas):

| Bloque | Columnas |
|--------|----------|
| Usuario evaluado | `usuario_id`, `identificacion`, `nombres`, `apellidos`, `nombre_completo`, `cargo`, `nivel_cargo`, `area`, `grupo`, `localizacion`, `unidad_negocio` |
| Evaluación | `evaluacion_id`, `proyecto`, `evaluacion_nombre`, `evaluacion_inicio`, `evaluacion_fin`, `evaluador`, `estado_evaluacion`, `total_perspectivas`, `total_objetivos` |
| Perspectiva | `perspectiva_id`, `perspectiva_nombre`, `perspectiva_peso`, `perspectiva_cumplimiento` |
| Objetivo | `objetivo_id`, `objetivo`, `objetivo_estrategico`, `indicador_medicion`, `indicador`, `objetivo_peso`, `meta`, `minimo`, `sobresaliente`, `unidad_medida`, `tipo_calculo`, `tipo_indicador`, `periodo`, `resultado`, `cumplimiento`, `fecha_limite`, `estado_seguimientos` |
| Metadatos | `meta_page`, `meta_per_page`, `meta_total_users`, `meta_total_pages`, `meta_updated_since`, `meta_server_time`, `meta_next_updated_since`, `status` |

`peso` y `cumplimiento` existen en dos niveles distintos del JSON, por eso los de
perspectiva van prefijados (`perspectiva_peso`, `perspectiva_cumplimiento`) y el
del objetivo se llama `objetivo_peso`. Los campos propios del objetivo (`meta`,
`resultado`, `cumplimiento`) van sin prefijo porque el objetivo es el grano de la fila.

Criterios aplicados según el documento técnico:

- `identificacion` se escribe como **texto** (conserva ceros iniciales).
- `resultado` y `cumplimiento` conservan `null` (celda vacía), sin sustituirlos por `"--"`.
- Los arreglos vacíos **no se pierden**: un usuario sin evaluaciones, una
  evaluación sin perspectivas o una perspectiva sin objetivos generan igualmente
  una fila con los niveles inferiores en blanco (útil para auditoría).
- `total_perspectivas` y `total_objetivos` se toman del servicio, no se recalculan.

### Diferencias entre el documento técnico y el servicio real

El documento técnico v1.0 describe menos campos de los que el servicio entrega.
El invocador mapea **ambos** contratos, así que funciona con cualquiera de los dos:

| Nivel | Campos que llegan y no están documentados |
|-------|-------------------------------------------|
| Usuario | `cargo`, `nivel_cargo`, `area`, `grupo`, `localizacion`, `unidad_negocio` |
| Evaluación | `inicio`, `fin`, `evaluador`, `estado_evaluacion` |
| Perspectiva | `peso`, `cumplimiento` |
| Objetivo | `objetivo_estrategico`, `indicador_medicion`, `peso`, `minimo`, `sobresaliente`, `periodo`, `fecha_limite`, `estado_seguimientos` |

`indicador` figura en el documento pero el servicio ya no lo envía; en su lugar
llega `indicador_medicion`. La columna `indicador` se conserva para no perder el
dato si el servicio vuelve a exponerlo.

Dos advertencias sobre nombres parecidos:

- `status` (raíz) vale `"ok"` y describe si la **consulta** salió bien. El estado
  de la evaluación es `estado_evaluacion`.
- `evaluador` llega como nombre en texto libre. El servicio no expone
  identificación, correo, área ni cargo del evaluador, ni el correo del evaluado.

---

## 7. Logging

Cada ejecución escribe en consola y en `LOG_DIR/tracking-goals-invoker_<fecha>.log`,
registrando el inicio del proceso, el endpoint invocado, el criterio de consulta,
el avance por página y un resumen final. El token se registra **enmascarado**.

```
2026-08-10 19:04:04 | INFO | tracking-goals-invoker | ============================
2026-08-10 19:04:04 | INFO | tracking-goals-invoker | INICIO DEL PROCESO | tracking-goals-invoker
2026-08-10 19:04:04 | INFO | tracking-goals-invoker | Fecha de inicio    : 2026-08-10T19:04:04
2026-08-10 19:04:04 | INFO | tracking-goals-invoker | Endpoint base      : https://amagi.elearning.co
2026-08-10 19:04:04 | INFO | tracking-goals-invoker | Token              : ********92eb
2026-08-10 19:04:04 | INFO | tracking-goals-invoker | Endpoint invocado  : https://amagi.elearning.co/api/v1/tracking_goals
```

---

## 8. Pruebas

```bash
pip install -r requirements-dev.txt
pytest -q
```

68 pruebas cubren el mapeo del JSON del documento técnico, el aplanado, el
criterio de consulta, la construcción del endpoint, el cliente HTTP (401, 400,
JSON inválido, reintento ante 5xx), la exportación a Excel y el flujo del CLI,
incluida la ejecución de `main.py` sin el paquete instalado.

---

## 9. Manejo de errores

| Situación | Excepción | Código de salida |
|-----------|-----------|------------------|
| Falta `AMAGI_API_BASE_URL` / `AMAGI_API_TOKEN` | `ConfiguracionInvalida` | 1 |
| `page`/`per_page` fuera de rango | `CriterioInvalido` | 1 |
| Red, DNS, TLS o timeout | `ErrorDeConexion` | 1 |
| HTTP 401 / 403 | `ErrorDeAutenticacion` | 1 |
| HTTP 400 u otros 4xx | `ErrorDeConsulta` | 1 |
| Respuesta no JSON o con estructura inesperada | `RespuestaInvalida` | 1 |
| Fallo al escribir el Excel | `ErrorDeExportacion` | 1 |
| Fallo de conexión, autenticación o transferencia al servidor remoto | `ErrorDeEnvio` | 1 |

Los errores 429 y 5xx se reintentan automáticamente con backoff exponencial.

Si el Excel se genera pero la entrega remota falla, el proceso termina con
código 1 y el log indica la ruta local del archivo: **nunca se pierde el
reporte por un problema del servidor de archivos**.
