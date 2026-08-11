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
│   │   └── exportador_registros.py       # PUERTO de escritura del reporte
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

> El archivo `.env` está en `.gitignore`: **nunca** se versiona el token.

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
| `--log-level` | Nivel de detalle del log |
| `--env-file` | Ruta alternativa del `.env` |

Códigos de salida: `0` correcto · `1` error · `130` interrumpido.

---

## 4. Docker

```bash
# Construir
docker compose build

# Ejecutar (los argumentos van después del nombre del servicio)
docker compose run --rm tracking-goals --project 2026 --identity 5555553333
docker compose run --rm tracking-goals --project 2026 --todas-las-paginas
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

---

## 5. Salida en Excel

Una fila por objetivo, con la jerarquía repetida y la sección `meta` incorporada
en cada fila (29 columnas):

| Bloque | Columnas |
|--------|----------|
| Usuario | `usuario_id`, `identificacion`, `nombres`, `apellidos`, `nombre_completo` |
| Evaluación | `evaluacion_id`, `proyecto`, `evaluacion_nombre`, `total_perspectivas`, `total_objetivos` |
| Perspectiva | `perspectiva_id`, `perspectiva_nombre` |
| Objetivo | `objetivo_id`, `objetivo`, `meta`, `unidad_medida`, `tipo_calculo`, `tipo_indicador`, `indicador`, `resultado`, `cumplimiento` |
| Metadatos | `meta_page`, `meta_per_page`, `meta_total_users`, `meta_total_pages`, `meta_updated_since`, `meta_server_time`, `meta_next_updated_since`, `status` |

Criterios aplicados según el documento técnico:

- `identificacion` se escribe como **texto** (conserva ceros iniciales).
- `resultado` y `cumplimiento` conservan `null` (celda vacía), sin sustituirlos por `"--"`.
- Los arreglos vacíos **no se pierden**: un usuario sin evaluaciones, una
  evaluación sin perspectivas o una perspectiva sin objetivos generan igualmente
  una fila con los niveles inferiores en blanco (útil para auditoría).
- `total_perspectivas` y `total_objetivos` se toman del servicio, no se recalculan.

---

## 6. Logging

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

## 7. Pruebas

```bash
pip install -r requirements-dev.txt
pytest -q
```

35 pruebas cubren el mapeo del JSON del documento técnico, el aplanado, el
criterio de consulta, la construcción del endpoint, el cliente HTTP (401, 400,
JSON inválido, reintento ante 5xx), la exportación a Excel y el flujo del CLI,
incluida la ejecución de `main.py` sin el paquete instalado.

---

## 8. Manejo de errores

| Situación | Excepción | Código de salida |
|-----------|-----------|------------------|
| Falta `AMAGI_API_BASE_URL` / `AMAGI_API_TOKEN` | `ConfiguracionInvalida` | 1 |
| `page`/`per_page` fuera de rango | `CriterioInvalido` | 1 |
| Red, DNS, TLS o timeout | `ErrorDeConexion` | 1 |
| HTTP 401 / 403 | `ErrorDeAutenticacion` | 1 |
| HTTP 400 u otros 4xx | `ErrorDeConsulta` | 1 |
| Respuesta no JSON o con estructura inesperada | `RespuestaInvalida` | 1 |
| Fallo al escribir el Excel | `ErrorDeExportacion` | 1 |

Los errores 429 y 5xx se reintentan automáticamente con backoff exponencial.
