const zonaMasiva = document.getElementById('zonaMasiva');
const inputCarpetaMasiva = document.getElementById('inputCarpetaMasiva');
const btnSeleccionarCarpeta = document.getElementById('btnSeleccionarCarpeta');
const contenidoInicialBotonCarpeta = Array.from(btnSeleccionarCarpeta.childNodes, nodo =>
    nodo.cloneNode(true)
);
const btnProcesarMasivo = document.getElementById('btnProcesarMasivo');
const textoSeleccionMasiva = document.getElementById('textoSeleccionMasiva');
const temporizadorMasivo = document.getElementById('temporizadorMasivo');
const duracionMasiva = document.getElementById('duracionMasiva');
const contadorMasivo = document.getElementById('contadorMasivo');
const filasMasivas = document.getElementById('filasMasivas');
const btnDescargarJsonMasivo = document.getElementById('btnDescargarJsonMasivo');
const contenidoInicialBotonDescarga = Array.from(btnDescargarJsonMasivo.childNodes, nodo =>
    nodo.cloneNode(true)
);
const estadoDescargaMasiva = document.getElementById('estadoDescargaMasiva');
const visorSalidaMasiva = document.getElementById('visorSalidaMasiva');
const tituloSalidaMasiva = document.getElementById('tituloSalidaMasiva');
const contenidoSalidaMasiva = document.getElementById('contenidoSalidaMasiva');
const enlaceInicioMasivo = document.getElementById('enlaceInicioMasivo');
const enlacesNavegacion = document.querySelectorAll('.navegacion-principal a');
const confirmarSalidaMasiva = document.getElementById('confirmarSalidaMasiva');
const tituloConfirmarSalida = document.getElementById('tituloConfirmarSalida');
const textoConfirmarSalida = document.getElementById('textoConfirmarSalida');
const cancelarSalidaMasiva = document.getElementById('cancelarSalidaMasiva');
const aceptarSalidaMasiva = document.getElementById('aceptarSalidaMasiva');
const btnRevertirMasivo = document.getElementById('btnRevertirMasivo');
const extensionesPermitidas = /\.(pdf|jpe?g|png|webp|bmp|tiff?)$/i;
const camposFactura = [
    ['proveedor', 'Proveedor'],
    ['nit_proveedor', 'NIT proveedor'],
    ['total', 'Total'],
    ['estado_transaccion', 'Estado transacción'],
    ['fecha', 'Fecha'],
    ['hora', 'Hora'],
    ['referencia', 'Referencia'],
    ['numero_autorizacion', 'Nro autorización'],
    ['punto_recaudo', 'Punto de recaudo'],
    ['banco', 'Banco']
];

let archivosSeleccionados = [];
let facturasProcesadas = [];
const salidasProcesadas = new Map();
const urlsLocales = new Map();
let procesando = false;
let selectorCarpetaPendiente = false;
let arrastresActivos = 0;
let salidaConfirmada = false;
let accionConfirmacion = 'salir';
let controlConfirmacion = null;
let inicioProcesamiento = null;
let intervaloTemporizador = null;

function partesDuracion(duracionMs) {
    const milisegundos = Math.max(0, Math.floor(duracionMs));
    const segundosTotales = Math.floor(milisegundos / 1000);
    return {
        horas: Math.floor(segundosTotales / 3600),
        minutos: Math.floor((segundosTotales % 3600) / 60),
        segundos: segundosTotales % 60,
        milisegundos: milisegundos % 1000
    };
}

function actualizarTemporizador(duracionMs = performance.now() - inicioProcesamiento) {
    const partes = partesDuracion(duracionMs);
    const componentes = partes.horas > 0
        ? [partes.horas, partes.minutos, partes.segundos, partes.milisegundos]
        : [partes.horas * 60 + partes.minutos, partes.segundos, partes.milisegundos];
    temporizadorMasivo.textContent = componentes
        .map((valor, indice) => String(valor).padStart(indice === componentes.length - 1 ? 3 : 2, '0'))
        .join(':');
}

function mostrarDuracionFinal(duracionMs) {
    const partes = partesDuracion(duracionMs);
    const segundos = partes.segundos + partes.milisegundos / 1000;
    const horaTexto = `${partes.horas} ${partes.horas === 1 ? 'hora' : 'horas'}`;
    const minutoTexto = `${partes.minutos} ${partes.minutos === 1 ? 'minuto' : 'minutos'}`;
    duracionMasiva.textContent =
        `Tardó ${horaTexto}, ${minutoTexto} y ${segundos.toFixed(3)} segundos.`;
    duracionMasiva.hidden = false;
}

function solicitarConfirmacion(event, accion, control) {
    if (accion !== 'revertir' && archivosSeleccionados.length === 0) return;
    event.preventDefault();
    accionConfirmacion = accion;
    controlConfirmacion = control;
    if (accion === 'revertir') {
        const cantidadArchivos = archivosSeleccionados.length;
        const etiquetaArchivos = cantidadArchivos === 1 ? 'archivo' : 'archivos';
        tituloConfirmarSalida.textContent = '¿Revertir el lote actual?';
        textoConfirmarSalida.textContent = cantidadArchivos
            ? `Se descartarán los ${cantidadArchivos} ${etiquetaArchivos} de esta cola y se limpiará esta pantalla. Las facturas ya procesadas permanecerán en el historial.`
            : 'Se limpiará la pantalla actual. No hay archivos pendientes y ninguna factura del historial será eliminada.';
        aceptarSalidaMasiva.textContent = 'Revertir';
    } else {
        tituloConfirmarSalida.textContent = '¿Salir del cargue masivo?';
        textoConfirmarSalida.textContent = 'Los archivos pendientes se descartarán sin procesarse. Las facturas ya procesadas permanecerán en el historial.';
        aceptarSalidaMasiva.textContent = 'Salir';
    }
    confirmarSalidaMasiva.showModal();
    cancelarSalidaMasiva.focus();
}

if (confirmarSalidaMasiva && cancelarSalidaMasiva && aceptarSalidaMasiva) {
    [enlaceInicioMasivo, ...enlacesNavegacion].forEach(enlace => {
        enlace.addEventListener('click', event => {
            solicitarConfirmacion(event, 'salir', enlace);
        });
    });

    btnRevertirMasivo.addEventListener('click', event => {
        solicitarConfirmacion(event, 'revertir', btnRevertirMasivo);
    });

    cancelarSalidaMasiva.addEventListener('click', () => {
        confirmarSalidaMasiva.close();
        controlConfirmacion?.focus();
    });

    aceptarSalidaMasiva.addEventListener('click', () => {
        confirmarSalidaMasiva.close();
        if (accionConfirmacion === 'revertir') {
            revertirLote();
            btnRevertirMasivo.focus();
            return;
        }

        salidaConfirmada = true;
        window.location.assign(controlConfirmacion.href);
    });
}

window.addEventListener('beforeunload', event => {
    if (archivosSeleccionados.length === 0 || salidaConfirmada) return;
    event.preventDefault();
    event.returnValue = '';
});

function liberarUrlsLocales() {
    urlsLocales.forEach(url => URL.revokeObjectURL(url));
    urlsLocales.clear();
}

function revertirLote() {
    if (procesando) return;
    liberarUrlsLocales();
    archivosSeleccionados = [];
    facturasProcesadas = [];
    salidasProcesadas.clear();
    inputCarpetaMasiva.value = '';
    temporizadorMasivo.textContent = '00:00:000';
    duracionMasiva.hidden = true;
    inicioProcesamiento = null;
    if (intervaloTemporizador !== null) {
        window.clearInterval(intervaloTemporizador);
        intervaloTemporizador = null;
    }

    textoSeleccionMasiva.textContent = '';
    estadoDescargaMasiva.hidden = true;
    estadoDescargaMasiva.textContent = '';
    btnDescargarJsonMasivo.disabled = true;
    btnDescargarJsonMasivo.replaceChildren(
        ...contenidoInicialBotonDescarga.map(nodo => nodo.cloneNode(true))
    );
    btnProcesarMasivo.disabled = true;
    btnProcesarMasivo.textContent = 'Leer';
    btnRevertirMasivo.disabled = false;
    btnSeleccionarCarpeta.disabled = false;
    mostrarEstadoSeleccionCarpeta('', 'Subir');
    actualizarContador(0);
    mostrarFilaVacia('Selecciona documentos para comenzar.');
    zonaMasiva.classList.remove('procesando-masivo');
}

function mostrarFilaVacia(mensaje) {
    const fila = document.createElement('tr');
    fila.className = 'fila-vacia-masiva';
    const celda = document.createElement('td');
    celda.colSpan = 15;
    celda.textContent = mensaje;
    fila.append(celda);
    filasMasivas.replaceChildren(fila);
}

function actualizarContador(cantidad, total = null) {
    if (total !== null) {
        contadorMasivo.textContent = `${cantidad} / ${total}`;
        contadorMasivo.setAttribute(
            'aria-label',
            `${cantidad} de ${total} archivos procesados`
        );
        return;
    }

    contadorMasivo.textContent = `${cantidad} ${cantidad === 1 ? 'archivo' : 'archivos'}`;
    contadorMasivo.setAttribute(
        'aria-label',
        `${cantidad} ${cantidad === 1 ? 'archivo' : 'archivos'} seleccionados`
    );
}

function crearFila(archivoSeleccionado, indice) {
    const fila = document.createElement('tr');
    fila.dataset.indice = String(indice);

    const nombre = document.createElement('td');
    nombre.className = 'archivo-masivo';
    const urlLocal = URL.createObjectURL(archivoSeleccionado.archivo);
    urlsLocales.set(indice, urlLocal);
    agregarEnlace(nombre, archivoSeleccionado.nombre, urlLocal);

    const tipo = document.createElement('td');
    tipo.textContent = archivoSeleccionado.archivo.name.split('.').pop().toUpperCase();

    const estado = document.createElement('td');
    estado.className = 'estado-fila-masiva';
    estado.textContent = 'Pendiente';

    const celdasDatos = camposFactura.map(([campo]) => {
        const celda = document.createElement('td');
        celda.className = `dato-factura-masiva dato-${campo}`;
        celda.textContent = '—';
        return celda;
    });

    const texto = document.createElement('td');
    texto.className = 'texto-fila-masiva';
    texto.textContent = '—';

    const json = document.createElement('td');
    json.className = 'json-fila-masiva';
    json.textContent = '—';

    fila.append(nombre, tipo, estado, ...celdasDatos, texto, json);
    return fila;
}

function actualizarFila(indice, estado, mensaje) {
    const fila = filasMasivas.querySelector(`tr[data-indice="${indice}"]`);
    fila.classList.remove('fila-cargando');
    const celdaEstado = fila.querySelector('.estado-fila-masiva');
    celdaEstado.replaceChildren();

    const etiquetaEstado = document.createElement('span');
    etiquetaEstado.className = `estado-etiqueta estado-${estado}`;
    if (estado === 'procesando') {
        const spinner = document.createElement('span');
        spinner.className = 'spinner-circular spinner-circular-pequeno';
        spinner.setAttribute('aria-hidden', 'true');
        etiquetaEstado.append(spinner, document.createTextNode(mensaje));
    } else {
        etiquetaEstado.textContent = mensaje;
    }
    celdaEstado.append(etiquetaEstado);
    return fila;
}

function crearBotonVer(etiqueta, tipoSalida, claveSalida) {
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'btn-ver-salida-masiva';
    boton.textContent = etiqueta;
    boton.title = tipoSalida === 'texto'
        ? 'Ver el texto extraído del documento'
        : 'Ver los datos del documento en formato JSON';
    boton.dataset.tipoSalida = tipoSalida;
    boton.dataset.claveSalida = claveSalida;
    return boton;
}

async function mostrarSalidaMasiva(tipoSalida, claveSalida) {
    const salida = salidasProcesadas.get(claveSalida);
    if (!salida) return;
    tituloSalidaMasiva.textContent = tipoSalida === 'texto'
        ? `Texto extraído: ${salida.archivo}`
        : `JSON: ${salida.archivo}`;
    visorSalidaMasiva.showModal();

    if (tipoSalida === 'texto') {
        contenidoSalidaMasiva.textContent = salida.texto;
        return;
    }

    contenidoSalidaMasiva.textContent = 'Cargando JSON...';
    try {
        const respuesta = await fetch(`/api/v1/documentos/${salida.facturaId}`);
        const documento = await respuesta.json();
        if (!respuesta.ok) {
            throw new Error(documento.error || 'No se pudo cargar el documento.');
        }
        contenidoSalidaMasiva.textContent = JSON.stringify(documento, null, 2);
    } catch (error) {
        contenidoSalidaMasiva.textContent =
            `No se pudo cargar el JSON del documento: ${error.message}`;
    }
}

filasMasivas.addEventListener('click', event => {
    const boton = event.target.closest('.btn-ver-salida-masiva');
    if (boton) {
        mostrarSalidaMasiva(boton.dataset.tipoSalida, boton.dataset.claveSalida);
    }
});

const cerrarSalidaMasiva = document.getElementById('cerrarSalidaMasiva');
if (visorSalidaMasiva && cerrarSalidaMasiva) {
    cerrarSalidaMasiva.addEventListener('click', () => {
        visorSalidaMasiva.close();
    });

    visorSalidaMasiva.addEventListener('click', event => {
        if (event.target === visorSalidaMasiva) visorSalidaMasiva.close();
    });
}

function mostrarEsqueletosDeCarga() {
    filasMasivas.querySelectorAll('tr[data-indice]').forEach(fila => {
        fila.classList.add('fila-cargando');
        fila.querySelectorAll(
            '.estado-fila-masiva, .dato-factura-masiva, .texto-fila-masiva, .json-fila-masiva'
        ).forEach((celda, indice) => {
            const esqueleto = document.createElement('span');
            esqueleto.className = 'skeleton-line skeleton-celda-masiva';
            esqueleto.setAttribute('aria-hidden', 'true');
            if (celda.classList.contains('estado-fila-masiva')) {
                esqueleto.classList.add('skeleton-estado');
            } else if (celda.classList.contains('json-fila-masiva')) {
                esqueleto.classList.add('skeleton-json');
            } else {
                esqueleto.classList.add(`skeleton-dato-${indice % 3 + 1}`);
            }
            celda.replaceChildren(esqueleto);
        });
    });
}

function mostrarBotonProcesando(boton, texto) {
    boton.replaceChildren();
    const contenido = document.createElement('span');
    contenido.className = 'spinner-accion';
    const spinner = document.createElement('span');
    spinner.className = 'spinner-circular spinner-circular-pequeno';
    spinner.setAttribute('aria-hidden', 'true');
    const etiqueta = document.createElement('span');
    etiqueta.textContent = texto;
    contenido.append(spinner, etiqueta);
    boton.append(contenido);
}

function mostrarEstadoSeleccionCarpeta(estado, texto = 'Subir') {
    btnSeleccionarCarpeta.classList.remove(
        'estado-subiendo',
        'estado-cargado',
        'estado-error'
    );
    btnSeleccionarCarpeta.setAttribute('aria-busy', String(estado === 'subiendo'));

    if (!estado) {
        btnSeleccionarCarpeta.replaceChildren(
            ...contenidoInicialBotonCarpeta.map(nodo => nodo.cloneNode(true))
        );
        btnSeleccionarCarpeta.setAttribute('aria-label', texto);
        return;
    }

    btnSeleccionarCarpeta.removeAttribute('aria-label');
    btnSeleccionarCarpeta.classList.add(`estado-${estado}`);
    const contenido = document.createElement('span');
    contenido.className = 'spinner-accion';
    if (estado === 'subiendo') {
        const spinner = document.createElement('span');
        spinner.className = 'spinner-circular spinner-circular-pequeno';
        spinner.setAttribute('aria-hidden', 'true');
        contenido.append(spinner);
    } else if (estado === 'cargado') {
        const check = document.createElement('span');
        check.setAttribute('aria-hidden', 'true');
        check.textContent = '✓';
        contenido.append(check);
    }
    const etiqueta = document.createElement('span');
    etiqueta.textContent = texto;
    contenido.append(etiqueta);
    btnSeleccionarCarpeta.replaceChildren(contenido);
}

btnSeleccionarCarpeta.addEventListener('click', () => {
    if (procesando) return;
    selectorCarpetaPendiente = true;
    btnSeleccionarCarpeta.disabled = true;
    mostrarEstadoSeleccionCarpeta('subiendo', 'Cargando');
    try {
        if (typeof inputCarpetaMasiva.showPicker === 'function') {
            inputCarpetaMasiva.showPicker();
        } else {
            inputCarpetaMasiva.click();
        }
    } catch (error) {
        try {
            inputCarpetaMasiva.click();
        } catch (fallbackError) {
            selectorCarpetaPendiente = false;
            console.error('No se pudo abrir el selector de carpetas.', fallbackError);
            mostrarEstadoSeleccionCarpeta('error', 'Error al cargar');
            btnSeleccionarCarpeta.disabled = false;
            textoSeleccionMasiva.textContent =
                'No se pudo abrir el selector de carpetas. Inténtalo nuevamente.';
        }
    }
});

function restaurarBotonSiSeCanceloSelector() {
    if (!selectorCarpetaPendiente) return;
    window.setTimeout(() => {
        if (!selectorCarpetaPendiente) return;
        selectorCarpetaPendiente = false;
        if (procesando) return;
        mostrarEstadoSeleccionCarpeta('', 'Subir');
        btnSeleccionarCarpeta.disabled = archivosSeleccionados.length > 0;
    }, 250);
}

window.addEventListener('focus', restaurarBotonSiSeCanceloSelector);
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) restaurarBotonSiSeCanceloSelector();
});

function seleccionarArchivos(archivos, ignorarNoSoportados = false) {
    if (procesando) return;

    function rechazarSeleccion(mensaje) {
        liberarUrlsLocales();
        archivosSeleccionados = [];
        facturasProcesadas = [];
        salidasProcesadas.clear();
        inicioProcesamiento = null;
        temporizadorMasivo.textContent = '00:00:000';
        duracionMasiva.hidden = true;
        btnDescargarJsonMasivo.disabled = true;
        estadoDescargaMasiva.hidden = true;
        estadoDescargaMasiva.textContent = '';
        inputCarpetaMasiva.value = '';
        textoSeleccionMasiva.textContent = mensaje;
        btnProcesarMasivo.disabled = true;
        btnSeleccionarCarpeta.disabled = false;
        actualizarContador(0);
        mostrarFilaVacia('Corrige la selección para continuar.');
        zonaMasiva.classList.remove('procesando-masivo');
    }

    if (archivos.length === 0) {
        if (ignorarNoSoportados) {
            rechazarSeleccion('La carpeta no contiene archivos PDF o imágenes compatibles.');
        }
        return;
    }

    const validos = archivos.filter(archivo =>
        extensionesPermitidas.test(archivo.archivo.name)
    );
    const omitidos = archivos.length - validos.length;
    if (omitidos > 0 && !ignorarNoSoportados) {
        const noSoportados = archivos
            .filter(archivo => !extensionesPermitidas.test(archivo.archivo.name))
            .map(archivo => archivo.nombre);
        rechazarSeleccion(
            `Formato no soportado: ${noSoportados.join(', ')}.`
        );
        return;
    }

    if (validos.length === 0) {
        rechazarSeleccion('La carpeta no contiene archivos PDF o imágenes compatibles.');
        return;
    }

    liberarUrlsLocales();
    archivosSeleccionados = validos;
    btnSeleccionarCarpeta.disabled = true;
    facturasProcesadas = [];
    salidasProcesadas.clear();
    btnDescargarJsonMasivo.disabled = true;
    estadoDescargaMasiva.hidden = true;
    estadoDescargaMasiva.textContent = '';
    filasMasivas.replaceChildren(
        ...archivosSeleccionados.map(crearFila)
    );
    actualizarContador(archivosSeleccionados.length);
    const resumenOmitidos = omitidos
        ? ` Se omitieron ${omitidos} archivos no compatibles.`
        : '';
    textoSeleccionMasiva.textContent =
        `${archivosSeleccionados.length} ${archivosSeleccionados.length === 1 ? 'archivo' : 'archivos'} listos para procesar.${resumenOmitidos}`;
    inicioProcesamiento = null;
    temporizadorMasivo.textContent = '00:00:000';
    duracionMasiva.hidden = true;
    zonaMasiva.classList.remove('procesando-masivo');
    inputCarpetaMasiva.value = '';
    btnProcesarMasivo.disabled = false;
    btnProcesarMasivo.textContent = 'Leer';
}

inputCarpetaMasiva.addEventListener('change', () => {
    selectorCarpetaPendiente = false;
    seleccionarArchivos(
        Array.from(inputCarpetaMasiva.files, archivo => ({
            archivo,
            nombre: archivo.webkitRelativePath || archivo.name
        })),
        true
    );
    mostrarEstadoSeleccionCarpeta(
        archivosSeleccionados.length ? 'cargado' : '',
        archivosSeleccionados.length ? 'Listo' : 'Subir'
    );
    btnSeleccionarCarpeta.disabled = archivosSeleccionados.length > 0;
});

function leerArchivoDeEntrada(entrada) {
    return new Promise((resolve, reject) => {
        entrada.file(resolve, reject);
    });
}

function leerSiguienteGrupo(lector) {
    return new Promise((resolve, reject) => {
        lector.readEntries(resolve, reject);
    });
}

async function leerEntradaDeCarpeta(entrada, ruta = '') {
    if (entrada.isFile) {
        const archivo = await leerArchivoDeEntrada(entrada);
        return [{ archivo, nombre: `${ruta}${archivo.name}` }];
    }

    if (!entrada.isDirectory) return [];

    const lector = entrada.createReader();
    const archivos = [];
    while (true) {
        const grupo = await leerSiguienteGrupo(lector);
        if (grupo.length === 0) break;
        for (const hijo of grupo) {
            archivos.push(
                ...await leerEntradaDeCarpeta(hijo, `${ruta}${entrada.name}/`)
            );
        }
    }
    return archivos;
}

async function leerElementosArrastrados(dataTransfer) {
    const elementos = Array.from(dataTransfer.items || []);
    const entradas = elementos
        .filter(elemento => elemento.kind === 'file')
        .map(elemento => elemento.webkitGetAsEntry?.())
        .filter(Boolean);

    if (entradas.length === 0) {
        return {
            archivos: Array.from(dataTransfer.files, archivo => ({
                archivo,
                nombre: archivo.webkitRelativePath || archivo.name
            })),
            incluyeCarpeta: false
        };
    }

    const archivos = [];
    for (const entrada of entradas) {
        archivos.push(...await leerEntradaDeCarpeta(entrada));
    }
    return {
        archivos,
        incluyeCarpeta: entradas.some(entrada => entrada.isDirectory)
    };
}

function esArrastreDeArchivos(event) {
    return Array.from(event.dataTransfer?.types || []).includes('Files');
}

document.addEventListener('dragenter', event => {
    if (!esArrastreDeArchivos(event)) return;
    event.preventDefault();
    arrastresActivos += 1;
    document.body.classList.add('arrastrando-masivo');
});

document.addEventListener('dragover', event => {
    if (!esArrastreDeArchivos(event)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
});

document.addEventListener('dragleave', event => {
    if (!esArrastreDeArchivos(event)) return;
    arrastresActivos = Math.max(0, arrastresActivos - 1);
    if (arrastresActivos === 0 || event.relatedTarget === null) {
        arrastresActivos = 0;
        document.body.classList.remove('arrastrando-masivo');
    }
});

document.addEventListener('drop', async event => {
    if (!esArrastreDeArchivos(event)) return;
    event.preventDefault();
    arrastresActivos = 0;
    document.body.classList.remove('arrastrando-masivo');
    if (procesando) return;
    btnSeleccionarCarpeta.disabled = true;
    mostrarEstadoSeleccionCarpeta('subiendo', 'Cargando');
    try {
        const seleccion = await leerElementosArrastrados(event.dataTransfer);
        if (seleccion.archivos.length === 0) {
            mostrarEstadoSeleccionCarpeta('error', 'Error al cargar');
            textoSeleccionMasiva.textContent =
                'No se pudo leer la carpeta. Intenta seleccionarla con el botón «Subir».';
            return;
        }
        seleccionarArchivos(seleccion.archivos, seleccion.incluyeCarpeta);
        mostrarEstadoSeleccionCarpeta(
            archivosSeleccionados.length ? 'cargado' : 'error',
            archivosSeleccionados.length ? 'Listo' : 'Error al cargar'
        );
    } catch (error) {
        mostrarEstadoSeleccionCarpeta('error', 'Error al cargar');
        textoSeleccionMasiva.textContent =
            `No se pudo leer la carpeta. Intenta seleccionarla con el botón «Subir». ${error.message || ''}`.trim();
    } finally {
        btnSeleccionarCarpeta.disabled = archivosSeleccionados.length > 0;
    }
});

function agregarEnlace(celda, etiqueta, url, descarga = false) {
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.textContent = etiqueta;
    if (descarga) {
        enlace.download = '';
        enlace.title = 'Descargar el JSON de esta factura';
    } else {
        enlace.target = '_blank';
        enlace.rel = 'noopener';
        enlace.title = 'Abrir el documento original en otra pestaña';
    }
    celda.replaceChildren(enlace);
}

async function procesarArchivo(archivoSeleccionado, indice, total) {
    actualizarFila(indice, 'procesando', 'Leyendo');

    const datosFormulario = new FormData();
    datosFormulario.append('archivo', archivoSeleccionado.archivo);

    try {
        const respuesta = await new Promise((resolve, reject) => {
            const solicitud = new XMLHttpRequest();
            solicitud.open('POST', '/api/procesar');
            solicitud.upload.addEventListener('load', () => {
                mostrarEstadoSeleccionCarpeta('cargado', 'Listo');
            });
            solicitud.addEventListener('load', () => {
                let resultado;
                try {
                    resultado = JSON.parse(solicitud.responseText);
                } catch {
                    reject(new Error('El servidor devolvió una respuesta inválida.'));
                    return;
                }
                resolve({
                    ok: solicitud.status >= 200 && solicitud.status < 300,
                    json: resultado
                });
            });
            solicitud.addEventListener('error', () => {
                reject(new Error('No se pudo conectar al servidor.'));
            });
            solicitud.addEventListener('abort', () => {
                reject(new Error('La carga fue cancelada.'));
            });
            solicitud.send(datosFormulario);
        });
        const resultado = respuesta.json;
        if (!respuesta.ok || !resultado.ok) {
            throw new Error(resultado.error || 'No se pudo procesar el archivo.');
        }

        const facturaId = resultado.datos.factura_id;
        const claveSalida = String(indice);
        salidasProcesadas.set(claveSalida, {
            facturaId,
            archivo: resultado.datos.nombre_archivo || archivoSeleccionado.archivo.name,
            texto: resultado.datos.texto_extraido || ''
        });
        facturasProcesadas.push(facturaId);
        btnDescargarJsonMasivo.disabled = false;
        const filaResultado = actualizarFila(indice, 'exito', 'Leída');
        camposFactura.forEach(([campo]) => {
            filaResultado.querySelector(`.dato-${campo}`).textContent =
                resultado.datos[campo] || '—';
        });
        filaResultado.querySelector('.texto-fila-masiva').replaceChildren(
            crearBotonVer('Ver', 'texto', claveSalida)
        );
        agregarEnlace(
            filaResultado.querySelector('.archivo-masivo'),
            archivoSeleccionado.nombre,
            `/api/facturas/${facturaId}/original`
        );
        const urlLocal = urlsLocales.get(indice);
        if (urlLocal) {
            URL.revokeObjectURL(urlLocal);
            urlsLocales.delete(indice);
        }
        const celdaJson = filaResultado.querySelector('.json-fila-masiva');
        const botonVerJson = crearBotonVer('Ver', 'json', claveSalida);
        const enlaceJson = document.createElement('a');
        enlaceJson.href = `/api/v1/documentos/${facturaId}/json`;
        enlaceJson.download = '';
        enlaceJson.textContent = 'Descargar';
        enlaceJson.title = 'Descargar el JSON de esta factura';
        celdaJson.replaceChildren(botonVerJson, enlaceJson);
        return true;
    } catch (error) {
        const filaError = actualizarFila(indice, 'error', 'Error');
        filaError.querySelectorAll(
            '.dato-factura-masiva, .texto-fila-masiva'
        ).forEach(celda => {
            celda.textContent = '—';
        });
        filaError.querySelector('.json-fila-masiva').textContent = '—';
        const detalle = document.createElement('span');
        detalle.className = 'detalle-error-masivo';
        detalle.textContent = error.message || 'No se pudo conectar al servidor.';
        filaError.querySelector('.estado-fila-masiva').append(detalle);
        return false;
    } finally {
        actualizarContador(indice + 1, total);
    }
}

btnDescargarJsonMasivo.addEventListener('click', async () => {
    if (facturasProcesadas.length === 0 || btnDescargarJsonMasivo.disabled) return;

    btnDescargarJsonMasivo.disabled = true;
    estadoDescargaMasiva.hidden = false;
    estadoDescargaMasiva.textContent = 'Preparando descarga de JSON...';
    mostrarBotonProcesando(btnDescargarJsonMasivo, 'Preparando descarga...');

    try {
        const respuesta = await fetch('/api/v1/documentos/json/descargar-lote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ factura_ids: facturasProcesadas })
        });
        if (!respuesta.ok) {
            const error = await respuesta.json();
            throw new Error(error.error || 'No se pudieron preparar los JSON.');
        }

        const archivo = await respuesta.blob();
        const url = URL.createObjectURL(archivo);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = 'Facturas JSON.zip';
        document.body.append(enlace);
        enlace.click();
        enlace.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        estadoDescargaMasiva.textContent =
            `${facturasProcesadas.length} JSON incluidos en la carpeta «Facturas JSON».`;
    } catch (error) {
        estadoDescargaMasiva.textContent =
            error.message || 'No se pudieron descargar los JSON.';
    } finally {
        btnDescargarJsonMasivo.disabled = facturasProcesadas.length === 0;
        btnDescargarJsonMasivo.replaceChildren(
            ...contenidoInicialBotonDescarga.map(nodo => nodo.cloneNode(true))
        );
    }
});

btnProcesarMasivo.addEventListener('click', async () => {
    if (procesando || archivosSeleccionados.length === 0) return;

    procesando = true;
    const total = archivosSeleccionados.length;
    let exitosos = 0;
    mostrarEsqueletosDeCarga();
    actualizarContador(0, total);
    zonaMasiva.classList.add('procesando-masivo');
    btnSeleccionarCarpeta.disabled = true;
    btnRevertirMasivo.disabled = true;
    btnProcesarMasivo.disabled = true;
    mostrarEstadoSeleccionCarpeta('subiendo', 'Cargando');
    mostrarBotonProcesando(btnProcesarMasivo, 'Procesando...');
    duracionMasiva.hidden = true;
    inicioProcesamiento = performance.now();
    actualizarTemporizador();
    intervaloTemporizador = window.setInterval(actualizarTemporizador, 10);

    for (let indice = 0; indice < total; indice += 1) {
        mostrarEstadoSeleccionCarpeta('subiendo', 'Cargando');
        if (await procesarArchivo(archivosSeleccionados[indice], indice, total)) {
            exitosos += 1;
        }
    }

    const fallidos = total - exitosos;
    window.clearInterval(intervaloTemporizador);
    intervaloTemporizador = null;
    const duracionTotal = performance.now() - inicioProcesamiento;
    actualizarTemporizador(duracionTotal);
    mostrarDuracionFinal(duracionTotal);
    zonaMasiva.classList.remove('procesando-masivo');
    btnSeleccionarCarpeta.disabled = true;
    btnRevertirMasivo.disabled = false;
    mostrarEstadoSeleccionCarpeta(
        fallidos === 0 ? 'cargado' : 'error',
        fallidos === 0 ? 'Listo' : 'Error al cargar'
    );
    btnProcesarMasivo.replaceChildren(document.createTextNode('Lote procesado'));
    btnProcesarMasivo.textContent = 'Lote procesado';
    procesando = false;
});
