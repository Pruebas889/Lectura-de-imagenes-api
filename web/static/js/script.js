
const input     = document.getElementById('inputArchivo');
const uploadBox = document.querySelector('.upload-box');
const btnSubir  = uploadBox.querySelector('.btn-subir');
const iconoSubir = btnSubir.querySelector('.icono-subir');
const iconoProcesar = btnSubir.querySelector('.icono-procesar');
const btnTema = document.getElementById('btnTema');
const iconoTema = document.getElementById('iconoTema');
const resultado = document.getElementById('resultado');
const avisoHistorialAgregado = document.getElementById('avisoHistorialAgregado');
const nombreArchivoAgregado = document.getElementById('nombreArchivoAgregado');
const textoAvisoHistorialAgregado = document.getElementById('textoAvisoHistorialAgregado');
const previewC  = document.getElementById('preview-container');
const previewI  = document.getElementById('preview-img');
const previewStatus = document.getElementById('preview-status');
const visorDocumento = document.getElementById('visor-documento');
const visorTitulo = document.getElementById('visor-titulo');
const visorImagen = document.getElementById('visor-imagen');
const visorEstado = document.getElementById('visor-estado');
const visorPaginas = document.getElementById('visor-paginas');
const visorSalidaFactura = document.getElementById('visorSalidaFactura');
const tituloSalidaFactura = document.getElementById('tituloSalidaFactura');
const contenidoSalidaFactura = document.getElementById('contenidoSalidaFactura');
const descargarJsonFactura = document.getElementById('descargarJsonFactura');
const avisoNoLegible = document.getElementById('avisoNoLegible');
const tituloNoLegible = document.getElementById('tituloNoLegible');
const btnRevertirIndividual = document.getElementById('btnRevertirIndividual');
const confirmarReversionIndividual = document.getElementById('confirmarReversionIndividual');
const cancelarReversionIndividual = document.getElementById('cancelarReversionIndividual');
const aceptarReversionIndividual = document.getElementById('aceptarReversionIndividual');
const miniaturaFactura = document.querySelector('.miniatura-factura');
const panelLista = document.querySelector('.panel-lista');
const panelDetalle = document.querySelector('.panel-detalle');
const esqueletoDetalle = document.getElementById('esqueletoDetalleFactura');
let previewUrl = null;
let documentUrl = null;
let selectedDocumentIsPdf = false;
let viewerRequestId = 0;
const textoBtnSubir = btnSubir.textContent.trim();
let selectorBloqueado = false;
let selectorEsperandoArchivos = false;
let seleccionCambiadaDuranteExplorador = false;
let accionSelector = 'subir';

function mostrarAvisoHistorial(nombres) {
    const archivos = Array.isArray(nombres)
        ? nombres.filter(nombre => typeof nombre === 'string' && nombre.trim())
        : [];
    nombreArchivoAgregado.textContent = archivos.join(', ');
    textoAvisoHistorialAgregado.textContent = archivos.length > 1
        ? 'Se agregaron al historial con éxito.'
        : 'Se agregó al historial con éxito.';
    avisoHistorialAgregado.hidden = archivos.length === 0;
}

const archivosAgregadosPendientes = sessionStorage.getItem('archivosAgregadosHistorial');
if (archivosAgregadosPendientes) {
    try {
        mostrarAvisoHistorial(JSON.parse(archivosAgregadosPendientes));
    } catch {
        mostrarAvisoHistorial([]);
    } finally {
        sessionStorage.removeItem('archivosAgregadosHistorial');
    }
}

function bloquearSelector(bloqueado) {
    selectorBloqueado = bloqueado;
    btnSubir.classList.toggle('bloqueado', bloqueado);
    btnSubir.setAttribute('aria-disabled', String(bloqueado));
}

function mostrarEstadoCarga(estado, texto) {
    accionSelector = estado === 'subiendo'
        ? 'abriendo'
        : estado === 'cargado'
            ? 'procesar'
            : estado === 'procesando'
                ? 'procesando'
                : 'subir';
    btnSubir.classList.remove('estado-subiendo', 'estado-cargado', 'estado-error', 'listo-para-procesar');
    btnSubir.setAttribute('aria-busy', String(accionSelector === 'abriendo' || accionSelector === 'procesando'));
    bloquearSelector(accionSelector === 'procesando');
    btnRevertirIndividual.disabled = accionSelector === 'abriendo' || accionSelector === 'procesando';

    if (accionSelector === 'subir' || accionSelector === 'procesar') {
        const icono = accionSelector === 'procesar' ? iconoProcesar : iconoSubir;
        const iconoClonado = icono.cloneNode(true);
        iconoClonado.hidden = false;
        const etiqueta = document.createElement('span');
        etiqueta.textContent = accionSelector === 'procesar' ? texto : textoBtnSubir;
        btnSubir.replaceChildren(iconoClonado, etiqueta);
        btnSubir.classList.toggle('listo-para-procesar', accionSelector === 'procesar');
        btnSubir.title = accionSelector === 'procesar'
            ? 'Leer los documentos seleccionados'
            : 'Seleccionar uno o varios documentos para cargar';
        return;
    }

    const contenido = document.createElement('span');
    contenido.className = 'spinner-accion';
    if (accionSelector === 'abriendo' || accionSelector === 'procesando') {
        const spinner = document.createElement('span');
        spinner.className = 'spinner-circular spinner-circular-pequeno';
        spinner.setAttribute('aria-hidden', 'true');
        contenido.append(spinner);
    }
    const etiqueta = document.createElement('span');
    etiqueta.textContent = texto;
    contenido.append(etiqueta);
    btnSubir.replaceChildren(contenido);
    if (accionSelector === 'abriendo') {
        btnSubir.classList.add('estado-subiendo');
    }
    btnSubir.title = texto;
}

function mostrarEstadoLeido(alTerminar) {
    accionSelector = 'leido';
    bloquearSelector(true);
    btnRevertirIndividual.disabled = true;
    btnSubir.classList.remove('estado-subiendo', 'estado-cargado', 'estado-error', 'listo-para-procesar');
    btnSubir.classList.add('estado-leido');
    btnSubir.setAttribute('aria-busy', 'false');
    btnSubir.title = 'Lectura completada';

    const icono = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    icono.setAttribute('viewBox', '0 0 24 24');
    icono.setAttribute('fill', 'none');
    icono.setAttribute('class', 'icono-leido');
    icono.setAttribute('aria-hidden', 'true');
    const marca = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    marca.setAttribute('d', 'm5 12.5 4.5 4.5L19 7');
    marca.setAttribute('stroke', 'currentColor');
    marca.setAttribute('stroke-width', '2.5');
    marca.setAttribute('stroke-linecap', 'round');
    marca.setAttribute('stroke-linejoin', 'round');
    icono.append(marca);

    const etiqueta = document.createElement('span');
    etiqueta.textContent = 'Leído';
    btnSubir.replaceChildren(icono, etiqueta);
    window.setTimeout(() => {
        mostrarEstadoCarga('', textoBtnSubir);
        bloquearSelector(false);
        if (alTerminar) alTerminar();
    }, 1000);
}

btnSubir.addEventListener('click', event => {
    if (selectorBloqueado) {
        event.preventDefault();
        return;
    }
    if (accionSelector === 'procesar') {
        event.preventDefault();
        procesarArchivos();
        return;
    }
    if (accionSelector !== 'subir') {
        event.preventDefault();
        return;
    }
    selectorEsperandoArchivos = true;
    seleccionCambiadaDuranteExplorador = false;
    mostrarEstadoCarga('subiendo', 'Cargando');
});

btnSubir.addEventListener('keydown', event => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    if (selectorBloqueado) return;
    if (accionSelector === 'procesar') {
        procesarArchivos();
        return;
    }
    if (accionSelector === 'subir') {
        selectorEsperandoArchivos = true;
        seleccionCambiadaDuranteExplorador = false;
        mostrarEstadoCarga('subiendo', 'Cargando');
        input.click();
    }
});

window.addEventListener('focus', () => {
    if (!selectorEsperandoArchivos) return;

    window.setTimeout(() => {
        if (!selectorEsperandoArchivos) return;
        selectorEsperandoArchivos = false;
        if (!seleccionCambiadaDuranteExplorador) {
            mostrarEstadoCarga('', textoBtnSubir);
            bloquearSelector(false);
        }
        seleccionCambiadaDuranteExplorador = false;
    }, 0);
});

function enviarArchivosConProgreso(formData) {
    return new Promise((resolve, reject) => {
        const solicitud = new XMLHttpRequest();
        solicitud.open('POST', '/api/procesar-lote');
        solicitud.addEventListener('load', () => {
            let json;
            try {
                json = JSON.parse(solicitud.responseText);
            } catch {
                reject(new Error('El servidor devolvió una respuesta inválida.'));
                return;
            }
            resolve({
                ok: solicitud.status >= 200 && solicitud.status < 300,
                json
            });
        });
        solicitud.addEventListener('error', () => {
            reject(new Error('No se pudo conectar al servidor. Verifica tu conexión e inténtalo de nuevo.'));
        });
        solicitud.addEventListener('abort', () => {
            reject(new Error('La carga fue cancelada.'));
        });
        solicitud.send(formData);
    });
}

function mostrarBotonCargando(boton, texto) {
    boton.disabled = true;
    const contenido = document.createElement('span');
    contenido.className = 'spinner-accion';
    const indicador = document.createElement('span');
    indicador.className = 'spinner-circular spinner-circular-pequeno';
    indicador.setAttribute('aria-hidden', 'true');
    const etiqueta = document.createElement('span');
    etiqueta.textContent = texto;
    contenido.append(indicador, etiqueta);
    boton.replaceChildren(contenido);
}

function mostrarEstadoVisorCargando(texto) {
    visorEstado.replaceChildren();
    visorEstado.classList.add('visor-estado-cargando');
    const contenido = document.createElement('span');
    contenido.className = 'spinner-accion';
    const indicador = document.createElement('span');
    indicador.className = 'spinner-circular';
    indicador.setAttribute('aria-hidden', 'true');
    const etiqueta = document.createElement('span');
    etiqueta.textContent = texto;
    contenido.append(indicador, etiqueta);
    visorEstado.append(contenido);
    visorEstado.style.display = 'flex';
}

function mostrarEstadoVisorMensaje(texto) {
    visorEstado.classList.remove('visor-estado-cargando');
    visorEstado.textContent = texto;
    visorEstado.style.display = 'block';
}

if (visorSalidaFactura && panelDetalle) {
    panelDetalle.addEventListener('click', event => {
        const botonNoLegible = event.target.closest('.btn-dato-no-legible');
        if (botonNoLegible && avisoNoLegible) {
            tituloNoLegible.textContent = `Dato no legible: ${botonNoLegible.dataset.campo}`;
            avisoNoLegible.showModal();
            return;
        }

        const boton = event.target.closest('.btn-ver-salida');
        if (!boton) return;

        const esTexto = boton.dataset.tipoSalida === 'texto';
        const datos = document.getElementById(
            esTexto ? 'textoExtraidoFacturaData' : 'jsonFacturaData'
        );
        if (!datos) return;

        const valor = JSON.parse(datos.textContent);
        tituloSalidaFactura.textContent = esTexto ? 'Texto extraído' : 'JSON de la factura';
        descargarJsonFactura.hidden = esTexto;
        contenidoSalidaFactura.textContent = esTexto
            ? (valor || '')
            : JSON.stringify(valor, null, 2);
        visorSalidaFactura.showModal();
    });

    document.getElementById('cerrarSalidaFactura').addEventListener('click', () => {
        visorSalidaFactura.close();
    });

    visorSalidaFactura.addEventListener('click', event => {
        if (event.target === visorSalidaFactura) visorSalidaFactura.close();
    });

    document.getElementById('cerrarAvisoNoLegible').addEventListener('click', () => {
        avisoNoLegible.close();
    });

    avisoNoLegible.addEventListener('click', event => {
        if (event.target === avisoNoLegible) avisoNoLegible.close();
    });
}

function mostrarEsqueletosPaneles() {
    const contenidoDetalleOriginal = document.createDocumentFragment();
    let restaurado = false;

    while (panelDetalle.firstChild) {
        contenidoDetalleOriginal.append(panelDetalle.firstChild);
    }

    panelDetalle.setAttribute('aria-busy', 'true');
    panelDetalle.replaceChildren(esqueletoDetalle.content.cloneNode(true));

    return () => {
        if (restaurado) return;
        restaurado = true;
        panelDetalle.replaceChildren(contenidoDetalleOriginal);
        panelDetalle.removeAttribute('aria-busy');
    };
}

function finalizarCargaResultado(clase) {
    resultado.className = `resultado ${clase}`;
    resultado.setAttribute('aria-busy', 'false');
}

function esNavegacionNormal(event, enlace) {
    return !event.defaultPrevented &&
        event.button === 0 &&
        !event.metaKey &&
        !event.ctrlKey &&
        !event.shiftKey &&
        !event.altKey &&
        !enlace.target &&
        enlace.origin === window.location.origin;
}

if (panelLista && panelDetalle && esqueletoDetalle) {
    window.addEventListener('pageshow', event => {
        if (event.persisted && panelLista.getAttribute('aria-busy') === 'true') {
            window.location.reload();
        }
    });

    panelLista.addEventListener('click', event => {
        const enlace = event.target.closest('a.tarjeta-factura');
        if (!enlace || !esNavegacionNormal(event, enlace)) return;

        event.preventDefault();
        panelLista.setAttribute('aria-busy', 'true');
        panelDetalle.setAttribute('aria-busy', 'true');
        enlace.classList.add('tarjeta-cargando');
        enlace.setAttribute('aria-current', 'page');
        enlace.replaceChildren(
            Object.assign(document.createElement('span'), {
                className: 'skeleton-line esqueleto-tarjeta-tipo'
            }),
            Object.assign(document.createElement('span'), {
                className: 'skeleton-line esqueleto-tarjeta-proveedor'
            }),
            Object.assign(document.createElement('span'), {
                className: 'skeleton-line esqueleto-tarjeta-monto'
            }),
            Object.assign(document.createElement('span'), {
                className: 'skeleton-line esqueleto-tarjeta-fecha'
            })
        );
        panelDetalle.replaceChildren(esqueletoDetalle.content.cloneNode(true));

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                window.setTimeout(() => window.location.assign(enlace.href), 80);
            });
        });
    });
}

function actualizarControlTema() {
    const temaOscuro = document.documentElement.dataset.theme === 'dark';
    const etiqueta = temaOscuro ? 'Modo claro' : 'Modo oscuro';
    btnTema.setAttribute('aria-pressed', String(temaOscuro));
    btnTema.setAttribute('aria-label', etiqueta);
    btnTema.title = etiqueta;
    iconoTema.src = temaOscuro ? iconoTema.dataset.dark : iconoTema.dataset.light;
}

actualizarControlTema();
let themeTransitionTimer;
btnTema.addEventListener('click', () => {
    const tema = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    const root = document.documentElement;
    root.classList.add('theme-transition');
    root.dataset.theme = tema;
    window.clearTimeout(themeTransitionTimer);
    themeTransitionTimer = window.setTimeout(() => root.classList.remove('theme-transition'), 720);
    localStorage.setItem('tema-facturas', tema);
    actualizarControlTema();
});

function contieneArchivos(event) {
    return Array.from(event.dataTransfer.types).includes('Files');
}

function formatoSoportado(file) {
    return /\.(pdf|jpe?g|png|webp|bmp|tiff?)$/i.test(file.name);
}

let arrastresActivos = 0;

document.addEventListener('dragenter', event => {
    if (!contieneArchivos(event)) return;
    event.preventDefault();
    arrastresActivos += 1;
    document.body.classList.add('arrastrando-archivo');
});

document.addEventListener('dragover', event => {
    if (!contieneArchivos(event)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
});

document.addEventListener('dragleave', event => {
    if (!contieneArchivos(event)) return;
    arrastresActivos = Math.max(0, arrastresActivos - 1);
    if (arrastresActivos === 0 || event.relatedTarget === null) {
        arrastresActivos = 0;
        document.body.classList.remove('arrastrando-archivo');
    }
});

document.addEventListener('drop', event => {
    if (!contieneArchivos(event)) return;
    event.preventDefault();
    arrastresActivos = 0;
    document.body.classList.remove('arrastrando-archivo');

    const archivos = Array.from(event.dataTransfer.files).filter(formatoSoportado);

    if (!archivos.length) {
        window.alert('Selecciona al menos una imagen o un documento PDF compatible.');
        return;
    }

    const transferencia = new DataTransfer();
    archivos.forEach(archivo => transferencia.items.add(archivo));
    input.files = transferencia.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
});

function limpiarVistaPrevia() {
    previewI.removeAttribute('src');
    previewI.style.display = 'none';
    previewStatus.style.display = 'none';
    previewC.style.display = 'none';
    cerrarVistaCompleta();

    if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }
    if (documentUrl) {
        URL.revokeObjectURL(documentUrl);
        documentUrl = null;
    }
}

function cerrarVistaCompleta() {
    viewerRequestId += 1;
    if (visorDocumento.open) {
        visorDocumento.close();
    }
    visorImagen.removeAttribute('src');
    visorImagen.style.display = 'none';
    visorEstado.style.display = 'none';
    visorPaginas.replaceChildren();
    visorPaginas.style.display = 'none';
}

function mostrarPaginas(data) {
    visorEstado.style.display = 'none';
    visorPaginas.replaceChildren();
    data.paginas.forEach(pagina => {
        const hoja = document.createElement('figure');
        hoja.className = 'visor-pagina';

        const imagen = document.createElement('img');
        imagen.src = pagina.imagen;
        imagen.alt = `Página ${pagina.numero}`;

        const etiqueta = document.createElement('figcaption');
        etiqueta.textContent = `Página ${pagina.numero}`;

        hoja.append(imagen, etiqueta);
        visorPaginas.append(hoja);
    });
    visorPaginas.style.display = 'block';
}

async function mostrarVistaCompleta() {
    const file = input.files[0];
    if (!file || !documentUrl) return;

    visorTitulo.textContent = file.name;
    if (!selectedDocumentIsPdf) {
        visorImagen.src = documentUrl;
        visorImagen.style.display = 'block';
        visorDocumento.showModal();
        return;
    }

    const requestId = ++viewerRequestId;
    mostrarEstadoVisorCargando('Cargando todas las páginas...');
    visorDocumento.showModal();

    const formData = new FormData();
    formData.append('archivo', file);

    try {
        const response = await fetch('/api/previsualizar-pdf-completo', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo abrir el documento.');
        }
        if (requestId !== viewerRequestId) return;

        mostrarPaginas(data);
    } catch (error) {
        if (requestId !== viewerRequestId) return;
        mostrarEstadoVisorMensaje(error.message || 'No se pudo abrir el documento.');
    }
}

async function mostrarFacturaGuardada() {
    const requestId = ++viewerRequestId;
    visorTitulo.textContent = miniaturaFactura.dataset.nombre;
    visorImagen.removeAttribute('src');
    visorImagen.style.display = 'none';
    visorPaginas.replaceChildren();
    visorPaginas.style.display = 'none';
    mostrarEstadoVisorCargando('Cargando documento completo...');
    visorDocumento.showModal();

    try {
        const response = await fetch(
            `/api/facturas/${miniaturaFactura.dataset.facturaId}/previsualizar`
        );
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo abrir el documento.');
        }
        if (requestId !== viewerRequestId) return;
        mostrarPaginas(data);
    } catch (error) {
        if (requestId !== viewerRequestId) return;
        mostrarEstadoVisorMensaje(error.message || 'No se pudo abrir el documento.');
    }
}

if (miniaturaFactura) {
    const imagenMiniatura = miniaturaFactura.querySelector('img');
    const errorMiniatura = document.querySelector('.miniatura-error');
    imagenMiniatura.addEventListener('load', () => {
        miniaturaFactura.classList.remove('cargando-miniatura');
    });
    imagenMiniatura.addEventListener('error', () => {
        miniaturaFactura.classList.remove('cargando-miniatura');
        miniaturaFactura.hidden = true;
        errorMiniatura.hidden = false;
    });
    if (imagenMiniatura.complete) {
        miniaturaFactura.classList.remove('cargando-miniatura');
        if (imagenMiniatura.naturalWidth === 0) {
            miniaturaFactura.hidden = true;
            errorMiniatura.hidden = false;
        }
    }
    miniaturaFactura.addEventListener('click', mostrarFacturaGuardada);
}

previewI.addEventListener('click', mostrarVistaCompleta);
previewI.addEventListener('keydown', event => {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        mostrarVistaCompleta();
    }
});
previewI.tabIndex = 0;
previewI.setAttribute('role', 'button');
previewI.setAttribute('aria-label', 'Abrir documento completo');
previewI.title = 'Ampliar la vista previa del documento';

document.getElementById('cerrar-visor').addEventListener('click', cerrarVistaCompleta);
visorDocumento.addEventListener('click', event => {
    if (event.target === visorDocumento) {
        cerrarVistaCompleta();
    }
});

btnRevertirIndividual.addEventListener('click', () => {
    confirmarReversionIndividual.showModal();
    cancelarReversionIndividual.focus();
});

cancelarReversionIndividual.addEventListener('click', () => {
    confirmarReversionIndividual.close();
    btnRevertirIndividual.focus();
});

aceptarReversionIndividual.addEventListener('click', () => {
    confirmarReversionIndividual.close();
    input.value = '';
    selectorEsperandoArchivos = false;
    seleccionCambiadaDuranteExplorador = false;
    mostrarAvisoHistorial([]);
    limpiarVistaPrevia();
    resultado.replaceChildren();
    resultado.className = 'resultado';
    resultado.setAttribute('aria-busy', 'false');
    resultado.style.display = 'none';
    mostrarEstadoCarga('', textoBtnSubir);
    bloquearSelector(false);
    btnRevertirIndividual.focus();
});

confirmarReversionIndividual.addEventListener('click', event => {
    if (event.target === confirmarReversionIndividual) {
        confirmarReversionIndividual.close();
        btnRevertirIndividual.focus();
    }
});

// Muestra una vista previa de la imagen o de la primera página del PDF.
input.addEventListener('change', () => {
    if (selectorEsperandoArchivos) {
        seleccionCambiadaDuranteExplorador = true;
        selectorEsperandoArchivos = false;
    }
    const archivos = Array.from(input.files);
    const file = archivos[0];
    limpiarVistaPrevia();
    mostrarAvisoHistorial([]);
    if (!file) {
        mostrarEstadoCarga('', textoBtnSubir);
        return;
    }

    if (archivos.length > 1) {
        selectedDocumentIsPdf = false;
        previewC.style.display = 'block';
        previewStatus.textContent = `${archivos.length} documentos seleccionados. Se procesarán individualmente.`;
        previewStatus.style.display = 'block';
        previewI.style.display = 'none';
        mostrarEstadoCarga('cargado', `Procesar ${archivos.length} documentos`);
        resultado.style.display = 'none';
        return;
    }

    if (file.type.startsWith('image/')) {
        selectedDocumentIsPdf = false;
        documentUrl = URL.createObjectURL(file);
        previewUrl = documentUrl;
        previewI.src = previewUrl;
        previewI.style.display = 'block';
        previewC.style.display = 'block';
    } else if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        selectedDocumentIsPdf = true;
        documentUrl = URL.createObjectURL(file);
        previewC.style.display = 'block';
        previewStatus.textContent = '';
        previewStatus.style.display = 'none';
    } else {
        limpiarVistaPrevia();
        mostrarEstadoCarga('', textoBtnSubir);
        return;
    }

    mostrarEstadoCarga('cargado', 'Procesar factura');
    resultado.style.display = 'none';
});

async function procesarArchivos() {
    const archivos = Array.from(input.files);
    if (!archivos.length) return;

    const textoAccion = archivos.length > 1
        ? `Procesar ${archivos.length} documentos`
        : 'Procesar factura';
    mostrarEstadoCarga('procesando', 'Procesando...');
    resultado.replaceChildren();
    resultado.className = 'resultado';
    resultado.setAttribute('aria-busy', 'false');
    resultado.style.display = 'none';
    const restaurarPaneles = mostrarEsqueletosPaneles();

    const formData = new FormData();
    archivos.forEach(archivo => formData.append('archivos', archivo));

    try {
        const { ok, json } = await enviarArchivosConProgreso(formData);
        if (!ok) {
            throw new Error(json.error || 'No se pudo procesar el lote.');
        }

        if (json.fallidos === 0) {
            resultado.style.display = 'none';
            const nombresAgregados = json.resultados
                .filter(item => item.ok)
                .map(item => item.archivo);
            const ultimoResultado = json.resultados[json.resultados.length - 1];
            const facturaReciente = ultimoResultado && ultimoResultado.datos
                ? ultimoResultado.datos.factura_id
                : null;
            if (!Number.isInteger(facturaReciente)) {
                throw new Error('El procesamiento terminó, pero el servidor no devolvió el identificador de la factura.');
            }
            input.value = '';
            limpiarVistaPrevia();
            sessionStorage.setItem('archivosAgregadosHistorial', JSON.stringify(nombresAgregados));
            mostrarAvisoHistorial(nombresAgregados);
            mostrarEstadoLeido(() => {
                window.location.assign(`/factura/${facturaReciente}`);
            });
        } else {
            bloquearSelector(false);
            restaurarPaneles();
            resultado.replaceChildren();
            const resumen = document.createElement('strong');
            resumen.textContent = `Procesados: ${json.exitosos} de ${json.total}. Fallidos: ${json.fallidos}.`;
            resultado.appendChild(resumen);
            json.resultados.forEach(item => {
                const fila = document.createElement('p');
                fila.textContent = item.ok
                    ? `${item.archivo}: ${item.datos.proveedor || 'Proveedor no detectado'} | ${item.datos.total || 'Total no detectado'} | ${item.datos.fecha || 'Fecha no detectada'}`
                    : `${item.archivo || 'Archivo'}: Error: ${item.error}`;
                resultado.appendChild(fila);
            });
            finalizarCargaResultado(json.exitosos ? 'advertencia' : 'error');
            resultado.style.display = 'block';
            if (json.exitosos) {
                mostrarAvisoHistorial(json.resultados
                    .filter(item => item.ok)
                    .map(item => item.archivo));
                input.value = '';
                limpiarVistaPrevia();
                mostrarEstadoLeido();
                const actualizar = document.createElement('button');
                actualizar.type = 'button';
                actualizar.textContent = 'Actualizar historial';
                actualizar.title = 'Recargar la página para mostrar las facturas procesadas';
                actualizar.addEventListener('click', () => {
                    mostrarBotonCargando(actualizar, 'Actualizando...');
                    location.reload();
                });
                resultado.appendChild(actualizar);
            } else {
                mostrarEstadoCarga('cargado', textoAccion);
            }
        }
    } catch (e) {
        restaurarPaneles();
        finalizarCargaResultado('error');
        resultado.textContent =
            e.message || 'No se pudo conectar al servidor. Verifica tu conexión e inténtalo de nuevo.';
        resultado.style.display = 'block';
        mostrarEstadoCarga('cargado', textoAccion);
    }
}
