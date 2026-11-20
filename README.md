# Lectura de imágenes API

Aplicación web y API en Flask para leer facturas desde PDF e imágenes. Extrae datos como proveedor, total, fecha y banco, y guarda los resultados en SQLite o MySQL/MariaDB.

## Requisitos

- Python 3.10 o posterior. Las dependencias, las rutas web y el preprocesamiento de imágenes se validaron en Windows con Python 3.10.22 y 3.13.15.
- Tesseract OCR para procesar imágenes y PDF escaneados.
- Poppler para convertir páginas de PDF a imágenes (necesario para la vista previa y el OCR de PDF).
- MySQL/MariaDB es opcional; SQLite sigue siendo el motor predeterminado.

En Windows, instala Tesseract (con los datos de idioma español e inglés) y Poppler y asegúrate de que estén en `PATH`, o define las variables `TESSERACT_PATH` y `POPPLER_PATH`. El proyecto busca algunas ubicaciones habituales de Tesseract y Poppler automáticamente. Si no puede encontrar las herramientas, configura sus rutas en `config/settings.py` o mediante esas variables de entorno.

La aplicación web y `main.py` procesan los documentos localmente con Tesseract y reglas de extracción; no envían su contenido a servicios externos. Las rutas JSON existentes muestran `No legible` cuando un campo no se identifica; la API v1 representa esos valores como `null`.

## Instalación en Windows

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\jcastillol\Documents\Lectura-de-imagenes-api"
```

Para desplegar en el servidor, selecciona explícitamente Python 3.13; `py -3` selecciona Python 3.15 en ese equipo, versión que aún no se ha validado:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno, puedes omitirla y ejecutar Python directamente desde `.venv\Scripts\python.exe`.

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

1. Detén la aplicación y respalda `database/facturas.db` y la carpeta `documentos`. Conserva la carpeta original en el mismo servidor; el migrador no copia ni elimina archivos.
2. Crea una base de datos vacía y un usuario en el servidor MySQL/MariaDB. El usuario necesita permisos para crear y modificar tablas, leer, insertar e indexar datos.
3. En la raíz del proyecto, instala las dependencias si es necesario y configura la conexión en la sesión de PowerShell. No guardes contraseñas en el repositorio:

```powershell
python -m pip install -r requirements.txt
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"
$env:MYSQL_DATABASE = "lectura_ocr"
$env:MYSQL_USER = "tu_usuario"
$env:MYSQL_PASSWORD = "tu_contraseña"
```

4. Ejecuta el migrador con la misma configuración `MYSQL_*`:

```powershell
python -m database.migrate_sqlite_to_mysql
```

También puedes indicar otra ubicación para la base SQLite con `--source "C:\ruta\facturas.db"`. El migrador crea o completa la tabla e índice, copia en lotes de 500 y verifica el total. Preserva IDs, fechas, campos y OCR, no modifica SQLite, y se detiene si MySQL ya tiene registros.

5. Si el total migrado coincide con el histórico, inicia la aplicación con `DB_ENGINE=mysql` y las mismas variables `MYSQL_*`. Desde ese momento, las nuevas facturas se guardarán en MySQL/MariaDB:

```powershell
$env:DB_ENGINE = "mysql"
$env:APP_HOST = "0.0.0.0"
$env:PORT = "5012"
python app.py
```

`DOCUMENT_FOLDER` permite apuntar a una ruta de almacenamiento dedicada; si la cambias, copia allí los originales existentes y configura esa misma ruta en cada reinicio de la aplicación. Tras la migración, prueba algunos documentos antes de volver a habilitar el servicio.

## Uso desde la interfaz

La página principal permite elegir entre dos modos:

- **Cargue individual** (`/individual`): conserva la interfaz para cargar y consultar facturas. El detalle muestra la tabla de datos y dos paneles junto al texto OCR: el JSON estructurado y el texto detectado. Las imágenes se previsualizan en el navegador y el visor del documento original se carga bajo demanda.
- **Cargue masivo** (`/cargue-masivo`): acepta PDF e imágenes compatibles de una carpeta o arrastrados, recorre subcarpetas y procesa los documentos de uno en uno. Para no crear una tabla enorme en el navegador, muestra hasta 100 filas por página y avanza la vista mientras procesa lotes grandes. El procesamiento continúa secuencialmente; no requiere cargar los contenidos de todos los archivos a la vez.
- **Historial** (`/historial`): consulta 50 documentos por página, sin recuperar el OCR completo. El botón JSON descarga el contenido de la página visible.

Los archivos subidos desde ambas interfaces se guardan en `documentos` (carpeta excluida de Git). La pantalla masiva envía cada documento por separado al endpoint de procesamiento individual, lo que permite actualizar el progreso y mostrar resultados durante el lote. El endpoint de API por lotes descrito abajo también está disponible para clientes externos.

## API

La base local es `http://127.0.0.1:5000` por defecto. Si iniciaste la aplicación con `PORT=5001`, utiliza `http://127.0.0.1:5001`. Las rutas de esta tabla son relativas a esa base:

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
| `GET` | `/api/v1/documentos` | Lista documentos con metadatos resumidos, sin incluir el texto OCR. Acepta paginación opcional. |
| `GET` | `/api/v1/documentos/<id>` | Devuelve los datos normalizados y el texto OCR completo de un documento. |
| `GET` | `/api/v1/documentos/<id>/json` | Descarga el mismo detalle v1 como archivo JSON. |
| `POST` | `/api/v1/documentos/json/descargar-lote` | Descarga los detalles v1 de varias facturas dentro de un ZIP. |
| `DELETE` | `/api/facturas` | Borra todas las facturas guardadas. |
| `POST` | `/api/previsualizar-pdf` | Devuelve una vista previa de la primera página del PDF. |
| `POST` | `/api/previsualizar-pdf-completo` | Devuelve las páginas del PDF para el visor. |

### Formato JSON de documentos v1

`GET /api/v1/documentos` devuelve una lista resumida con el enlace al archivo original. La fecha de procesamiento se normaliza a ISO 8601. Sin parámetros conserva la respuesta completa por compatibilidad. Para consultar por páginas usa, por ejemplo, `GET /api/v1/documentos?pagina=1&por_pagina=100`; `por_pagina` admite de 1 a 500 y el resultado agrega metadatos `paginacion`:

```json
{
  "total": 1234,
  "paginacion": {
    "pagina": 1,
    "por_pagina": 100,
    "total_paginas": 13
  },
  "documentos": []
}
```

La consulta resumida selecciona solo las columnas necesarias y no carga el texto OCR completo. El historial web se pagina de 50 en 50 y el cargue masivo presenta 100 filas por página. Se crea un índice por fecha de procesamiento e ID para ordenar y recorrer listas de gran tamaño. Para lotes grandes de exportación, los IDs se consultan en bloques de 500 y el ZIP se escribe en un archivo temporal en vez de acumularlo completo en memoria. La ruta heredada `GET /api/facturas` mantiene su formato y devuelve los registros completos; para listados grandes, prefiere la API v1.

```json
{
  "total": 1,
  "documentos": [
    {
      "id": 26,
      "archivo": {
        "nombre": "comprobante.png",
        "original_url": "/api/facturas/26/original"
      },
      "documento": {
        "tipo": "comprobante_transferencia",
        "entidad": "Nequi"
      },
      "procesamiento": {
        "fecha": "2026-04-19T10:10:00"
      }
    }
  ]
}
```

`GET /api/v1/documentos/26` devuelve además `datos` y `texto_extraido`. Los campos no identificados se representan como `null`. `otros_campos` está reservado para campos variables; actualmente queda vacío porque la base de datos solo persiste los campos normalizados definidos. El archivo original se obtiene por separado desde la ruta indicada en `archivo.original_url`.

El visor JSON del cargue individual y del cargue masivo usa el detalle v1. Sus descargas individuales y el ZIP del lote contienen el mismo formato normalizado. Las rutas heredadas `/api/facturas/<id>/json` y `/api/facturas/json/descargar-lote` conservan su formato anterior.

### Consumir la API desde Postman

1. Inicia la aplicación con `python app.py` y confirma el puerto que muestra la consola. Por defecto es `5000`; si la iniciaste con `PORT=5001`, usa ese puerto.
2. En Postman, crea una variable de entorno `baseUrl`, por ejemplo `http://127.0.0.1:5001` (o `http://127.0.0.1:5000` si usas el puerto predeterminado).
3. Para consultar una factura, crea una petición **GET** a `{{baseUrl}}/api/facturas/951`. No requiere body. La respuesta es JSON con los campos guardados.

   La ruta `{{baseUrl}}/factura/951` **no es un endpoint JSON**: sirve la página HTML de detalle para el navegador.

4. Para procesar un documento, crea una petición **POST** a `{{baseUrl}}/api/procesar`. En **Body → form-data**, agrega una fila con la clave `archivo`, cambia su tipo de **Text** a **File** y selecciona un PDF o imagen. No agregues manualmente el encabezado `Content-Type`; Postman lo configura para `multipart/form-data`.
5. Para procesar varios documentos en una petición, usa **POST** `{{baseUrl}}/api/procesar-lote` y agrega una fila de tipo **File** por cada documento, usando la misma clave `archivos`.
6. También puedes probar **GET** `{{baseUrl}}/api/facturas` para listar los registros o **GET** `{{baseUrl}}/api/facturas/951/json` para obtener el JSON descargable de una factura.
7. Para consumir el formato normalizado, usa **GET** `{{baseUrl}}/api/v1/documentos` para el listado o **GET** `{{baseUrl}}/api/v1/documentos/951` para el detalle con texto OCR.

Una petición de procesamiento individual exitosa responde con `ok: true` y un objeto `datos` que incluye `factura_id`, `nombre_archivo`, `tipo`, `proveedor`, `total`, `fecha`, `banco` y los demás campos extraídos. En el procesamiento por lote la respuesta incluye `total`, `exitosos`, `fallidos` y un resultado por archivo. Si hay un error, revisa el código HTTP y el campo `error` (o el resultado individual fallido en un lote).

La ruta **DELETE** `{{baseUrl}}/api/facturas` borra todos los registros de facturas de la base de datos; úsala con cuidado. No requiere body.

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
- Los resultados del OCR pueden requerir revisión, especialmente cuando el documento tiene baja resolución o está inclinado. Los campos marcados `No legible` son interactivos y muestran recomendaciones para subir una imagen más clara.
