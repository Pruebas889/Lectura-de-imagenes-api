# Lectura de imágenes API

Aplicación web y API en Flask para leer facturas desde PDF e imágenes. Extrae datos como proveedor, total, fecha y banco, y guarda los resultados en SQLite o MySQL/MariaDB.

## Requisitos

- Python 3.10 o posterior.
- Tesseract OCR para procesar imágenes y PDF escaneados.
- Poppler para convertir páginas de PDF a imágenes (necesario para la vista previa y el OCR de PDF).
- Groq es opcional; se usa como respaldo si Tesseract y las reglas locales no detectan datos.
- MySQL/MariaDB es opcional; SQLite sigue siendo el motor predeterminado.

En Windows, instala Tesseract (con los datos de idioma español e inglés) y Poppler y asegúrate de que estén en `PATH`, o define las variables `TESSERACT_PATH` y `POPPLER_PATH`. El proyecto busca algunas ubicaciones habituales de Tesseract y Poppler automáticamente. Si no puede encontrar las herramientas, configura sus rutas en `config/settings.py` o mediante esas variables de entorno.

## Instalación en Windows

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\jcastillol\Documents\Lectura-de-imagenes-api"
```

Crea y activa un entorno virtual (si aún no existe) e instala las dependencias:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno, puedes omitirla y ejecutar Python directamente desde `.venv\Scripts\python.exe`.

## Configuración opcional de Groq

Groq es opcional y solo se consulta como respaldo cuando OCR y las reglas locales no detectan datos. Configura la clave como variable de entorno:

```powershell
$env:GROQ_API_KEY = "tu_clave_de_groq"
```

No publiques ni compartas una clave real. Sin ella, las funciones que dependen de Groq no estarán disponibles; la aplicación puede recurrir a la extracción basada en OCR y expresiones regulares.

Si Groq no está configurado o alcanza su cuota, el procesamiento local con Tesseract sigue siendo el camino principal.

## Iniciar la aplicación web

Desde la raíz del proyecto, con el entorno virtual activado:

```powershell
python app.py
```

También puedes ejecutarla sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abre [http://127.0.0.1:5000/](http://127.0.0.1:5000/) en el navegador. Detén el servidor con `Ctrl+C`.

Para iniciar o reiniciar localmente en el puerto `5001`, desde la raíz del proyecto ejecuta en PowerShell:

```powershell
$env:APP_HOST = "127.0.0.1"
$env:PORT = "5001"
.\.venv\Scripts\python.exe app.py
```

Abre [http://127.0.0.1:5001/](http://127.0.0.1:5001/). Este comando limita el acceso a tu propio equipo.

Por defecto, la aplicación crea la tabla de SQLite al iniciar. La base de datos local está en `database/facturas.db`.

## Migrar SQLite a MySQL/MariaDB

1. Crea una base de datos y un usuario en el servidor MySQL/MariaDB. El usuario necesita permisos para crear y modificar tablas, y leer e insertar datos.
2. Instala las dependencias actualizadas y configura la conexión en la sesión de PowerShell. No guardes contraseñas en el repositorio:

```powershell
python -m pip install -r requirements.txt
$env:DB_ENGINE = "mysql"
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_DATABASE = "lectura_ocr"
$env:MYSQL_USER = "tu_usuario"
$env:MYSQL_PASSWORD = "tu_contraseña"
```

3. Ejecuta el migrador desde la raíz del proyecto:

```powershell
python -m database.migrate_sqlite_to_mysql
```

También puedes indicar otra ubicación para la base SQLite con `--source "C:\ruta\facturas.db"`. El migrador conserva los IDs, fechas, campos extraídos y texto OCR; crea o completa el esquema MySQL y no modifica la base SQLite. Para evitar duplicados o sobrescrituras, se detiene si la tabla MySQL ya tiene registros.

4. Inicia la aplicación con `DB_ENGINE=mysql` y las mismas variables de conexión. Desde ese momento, las nuevas facturas se guardarán en MySQL/MariaDB.

La migración copia los registros de la base de datos, no los archivos originales. Si quieres que la aplicación siga mostrando los documentos ya cargados, conserva o copia también la carpeta `documentos` al servidor donde se ejecute.

## Uso desde la interfaz

La página principal permite elegir entre dos modos:

- **Cargue individual** (`/individual`): conserva la interfaz para cargar y consultar facturas. El detalle muestra la tabla de datos y dos paneles junto al texto OCR: el JSON estructurado y el texto detectado. Las imágenes se previsualizan en el navegador y el visor del documento original se carga bajo demanda.
- **Cargue masivo** (`/cargue-masivo`): acepta cualquier cantidad de PDF e imágenes compatibles, seleccionando una carpeta completa o arrastrándola. Recorre subcarpetas, omite otros tipos de archivo y procesa los documentos compatibles de uno en uno. El conteo aparece en la zona de carga y cada resultado se agrega a la tabla al terminar. El nombre abre el documento original en otra pestaña y cada factura leída tiene un enlace para descargar su JSON.

Los archivos subidos desde ambas interfaces se guardan en `documentos` (carpeta excluida de Git). La pantalla masiva envía cada documento por separado al endpoint de procesamiento individual, lo que permite actualizar el progreso y mostrar resultados durante el lote. El endpoint de API por lotes descrito abajo también está disponible para clientes externos.

## API

Los endpoints están disponibles en `http://127.0.0.1:5000`:

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/procesar` | Procesa un archivo enviado como `multipart/form-data`, en el campo `archivo`. |
| `POST` | `/api/procesar-lote` | Procesa varios archivos en el campo repetido `archivos` y devuelve un resultado JSON independiente por cada uno. |
| `GET` | `/api/facturas` | Devuelve las facturas guardadas. |
| `GET` | `/api/facturas/<id>` | Devuelve una factura por su ID. |
| `GET` | `/api/facturas/<id>/json` | Descarga los datos extraídos de una factura como archivo `.json`. |
| `GET` | `/api/facturas/<id>/original` | Abre el documento original guardado para esa factura. |
| `GET` | `/api/facturas/<id>/miniatura` | Devuelve la miniatura del documento original. |
| `GET` | `/api/facturas/<id>/previsualizar` | Devuelve todas las páginas como imágenes para el visor. |
| `DELETE` | `/api/facturas` | Borra todas las facturas guardadas. |
| `POST` | `/api/previsualizar-pdf` | Devuelve una vista previa de la primera página del PDF. |
| `POST` | `/api/previsualizar-pdf-completo` | Devuelve las páginas del PDF para el visor. |

Ejemplo para procesar una factura desde PowerShell:

```powershell
curl.exe -X POST -F "archivo=@C:\ruta\a\factura.pdf" http://127.0.0.1:5000/api/procesar
```

La respuesta correcta incluye `ok: true` y los datos extraídos: proveedor, NIT, total, estado de transacción, fecha, hora, referencia, número de autorización, punto de recaudo y banco. La vista de detalle los presenta en una tabla. El endpoint admite PDF e imágenes compatibles (JPG, JPEG, PNG, WEBP, BMP y TIFF). Las nuevas columnas se agregan automáticamente a bases de datos existentes; los datos históricos quedan vacíos hasta volver a procesar sus archivos.

El cargue masivo no limita la cantidad de archivos. Las solicitudes HTTP tienen un límite de tamaño total de 100 MB de forma predeterminada, configurable con `MAX_UPLOAD_BYTES`; en la interfaz los documentos se envían y procesan uno por uno. Cada resultado incluye `ok` y los datos o el error de ese archivo. Un archivo fallido no cancela los demás.

Ejemplo de lote desde PowerShell:

```powershell
curl.exe -X POST `
  -F "archivos=@C:\ruta\a\factura1.pdf" `
  -F "archivos=@C:\ruta\a\factura2.jpg" `
  http://127.0.0.1:5000/api/procesar-lote
```

## Procesar archivos por lotes

También puedes poner archivos PDF e imágenes en la carpeta `pdfs` y ejecutar el procesador por lotes:

```powershell
python main.py
```

Los resultados se guardan en la misma base de datos SQLite.

## Notas

- SQLite se usa de forma predeterminada. Selecciona MySQL/MariaDB con `DB_ENGINE=mysql`; configura `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER` y `MYSQL_PASSWORD` mediante variables de entorno.
- La aplicación inicia el servidor Flask de desarrollo con debug desactivado y enlazado a `127.0.0.1`. Sigue siendo un servidor de desarrollo y no tiene autenticación: no la expongas a la red. Antes del uso compartido hacen falta un servidor WSGI, autenticación/autorización y una estrategia de cola y trabajadores. `APP_HOST` permite cambiar el host solo cuando el despliegue ya esté protegido.
- Los resultados del OCR pueden requerir revisión, especialmente cuando el documento tiene baja resolución o está inclinado.
