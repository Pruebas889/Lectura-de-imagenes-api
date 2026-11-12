
const input     = document.getElementById('inputArchivo');
const uploadBox = document.querySelector('.upload-box');
const btnSubir  = uploadBox.querySelector('.btn-subir');
const btnTema = document.getElementById('btnTema');
const iconoTema = document.getElementById('iconoTema');
const btnP      = document.getElementById('btnProcesar');
const resultado = document.getElementById('resultado');
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
const btnBorrarHistorial = document.getElementById('btnBorrarHistorial');
const miniaturaFactura = document.querySelector('.miniatura-factura');
const panelLista = document.querySelector('.panel-lista');
const panelDetalle = document.querySelector('.panel-detalle');
const esqueletoDetalle = document.getElementById('esqueletoDetalleFactura');
let previewUrl = null;
let documentUrl = null;
let selectedDocumentIsPdf = false;
let viewerRequestId = 0;
const iconoProcesarSrc = btnP.querySelector('img').getAttribute('src');
const textoBtnSubir = btnSubir.textContent.trim();

function mostrarEstadoCarga(estado, texto) {
    btnSubir.classList.remove('estado-subiendo', 'estado-cargado', 'estado-error');
    btnSubir.setAttribute('aria-busy', String(estado === 'subiendo'));

    if (!estado) {
        btnSubir.replaceChildren(Object.assign(document.createElement('span'), {
            textContent: textoBtnSubir
        }));
        return;
    }

    btnSubir.classList.add(`estado-${estado}`);
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
    btnSubir.replaceChildren(contenido);
}

btnSubir.addEventListener('click', () => {
    mostrarEstadoCarga('subiendo', 'Cargando');
});

function enviarArchivosConProgreso(formData) {
    return new Promise((resolve, reject) => {
        const solicitud = new XMLHttpRequest();
        solicitud.open('POST', '/api/procesar-lote');
        solicitud.upload.addEventListener('load', () => {
            mostrarEstadoCarga('cargado', 'Listo');
        });
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
}

function mostrarEsqueletosPaneles() {
    const listaFacturas = panelLista.querySelector('.lista-facturas');
    const contenidoDetalleOriginal = document.createDocumentFragment();
    const estadoVacio = listaFacturas.querySelector('.vacio');
    const estabaVacioOculto = estadoVacio?.hidden ?? false;
    const tarjetaEsqueleto = document.createElement('div');
    let restaurado = false;

    while (panelDetalle.firstChild) {
        contenidoDetalleOriginal.append(panelDetalle.firstChild);
    }

    if (estadoVacio) {
        estadoVacio.hidden = true;
    }

    panelLista.setAttribute('aria-busy', 'true');
    panelDetalle.setAttribute('aria-busy', 'true');
    tarjetaEsqueleto.className = 'tarjeta-factura tarjeta-cargando tarjeta-factura-esqueleto';
    tarjetaEsqueleto.setAttribute('aria-hidden', 'true');
    tarjetaEsqueleto.innerHTML = `
        <span class="skeleton-line esqueleto-tarjeta-tipo"></span>
        <span class="skeleton-line esqueleto-tarjeta-proveedor"></span>
        <span class="skeleton-line esqueleto-tarjeta-monto"></span>
        <span class="skeleton-line esqueleto-tarjeta-fecha"></span>
    `;
    listaFacturas.append(tarjetaEsqueleto);
    panelDetalle.replaceChildren(esqueletoDetalle.content.cloneNode(true));

    return () => {
        if (restaurado) return;
        restaurado = true;
        tarjetaEsqueleto.remove();
        if (estadoVacio) {
            estadoVacio.hidden = estabaVacioOculto;
        }
        panelDetalle.replaceChildren(contenidoDetalleOriginal);
        panelLista.removeAttribute('aria-busy');
        panelDetalle.removeAttribute('aria-busy');
    };
}

function finalizarCargaResultado(clase) {
    resultado.className = `resultado ${clase}`;
    resultado.setAttribute('aria-busy', 'false');
}

function restaurarBotonProcesar(texto) {
    const icono = document.createElement('img');
    icono.src = iconoProcesarSrc;
    icono.alt = '';
    icono.setAttribute('aria-hidden', 'true');

    const etiqueta = document.createElement('span');
    etiqueta.textContent = texto;
    btnP.replaceChildren(icono, etiqueta);
    btnP.disabled = false;
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
btnTema.addEventListener('click', () => {
    const tema = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = tema;
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

if (btnBorrarHistorial) {
    btnBorrarHistorial.addEventListener('click', async () => {
        if (!window.confirm('¿Seguro que quieres borrar todo el historial? Esta acción no se puede deshacer.')) {
            return;
        }

        const etiquetaOriginal = btnBorrarHistorial.textContent.trim();
        mostrarBotonCargando(btnBorrarHistorial, 'Borrando...');

        try {
            const res = await fetch('/api/facturas', { method: 'DELETE' });
            const json = await res.json();

            if (!res.ok || !json.ok) {
                throw new Error(json.error || 'No se pudo borrar el historial.');
            }

            window.location.assign('/individual');
        } catch (error) {
            window.alert(error.message || 'No se pudo conectar al servidor.');
            btnBorrarHistorial.replaceChildren(document.createTextNode(etiquetaOriginal));
            btnBorrarHistorial.disabled = false;
        }
    });
}

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

document.getElementById('cerrar-visor').addEventListener('click', cerrarVistaCompleta);
visorDocumento.addEventListener('click', event => {
    if (event.target === visorDocumento) {
        cerrarVistaCompleta();
    }
});

// Muestra una vista previa de la imagen o de la primera página del PDF.
input.addEventListener('change', () => {
    const archivos = Array.from(input.files);
    const file = archivos[0];
    mostrarEstadoCarga('', textoBtnSubir);
    btnP.disabled = false;
    limpiarVistaPrevia();
    if (!file) {
        btnP.style.display = 'none';
        return;
    }

    if (archivos.length > 1) {
        mostrarEstadoCarga('cargado', 'Listo');
        selectedDocumentIsPdf = false;
        previewC.style.display = 'block';
        previewStatus.textContent = `${archivos.length} documentos seleccionados. Se procesarán individualmente.`;
        previewStatus.style.display = 'block';
        previewI.style.display = 'none';
        btnP.querySelector('span').textContent = `Procesar ${archivos.length} documentos`;
        btnP.style.display = 'block';
        resultado.style.display = 'none';
        return;
    }

    btnP.querySelector('span').textContent = 'Procesar factura';
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
        btnP.style.display = 'none';
        return;
    }

    mostrarEstadoCarga('cargado', 'Listo');
    btnP.style.display = 'block';
    resultado.style.display = 'none';
});

// Envía el archivo a la API
btnP.addEventListener('click', async () => {
    const archivos = Array.from(input.files);
    if (!archivos.length) return;

    const textoBoton = btnP.querySelector('span').textContent;
    btnP.style.display = 'block';
    mostrarBotonCargando(btnP, 'Procesando...');
    mostrarEstadoCarga('subiendo', 'Cargando');
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
            const ultimoResultado = json.resultados[json.resultados.length - 1];
            const facturaReciente = ultimoResultado && ultimoResultado.datos
                ? ultimoResultado.datos.factura_id
                : null;
            if (!Number.isInteger(facturaReciente)) {
                throw new Error('El procesamiento terminó, pero el servidor no devolvió el identificador de la factura.');
            }
            limpiarVistaPrevia();
            window.setTimeout(() => {
                window.location.assign(`/factura/${facturaReciente}`);
            }, 500);
        } else {
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
                restaurarBotonProcesar(textoBoton);
                btnP.disabled = true;
                const actualizar = document.createElement('button');
                actualizar.type = 'button';
                actualizar.textContent = 'Actualizar historial';
                actualizar.addEventListener('click', () => {
                    mostrarBotonCargando(actualizar, 'Actualizando...');
                    location.reload();
                });
                resultado.appendChild(actualizar);
            } else {
                restaurarBotonProcesar(textoBoton);
            }
            btnP.style.display = 'block';
        }
    } catch (e) {
        mostrarEstadoCarga('error', 'Error al cargar');
        restaurarPaneles();
        finalizarCargaResultado('error');
        resultado.textContent =
            e.message || 'No se pudo conectar al servidor. Verifica tu conexión e inténtalo de nuevo.';
        resultado.style.display = 'block';
        restaurarBotonProcesar(textoBoton);
        btnP.style.display = 'block';
    }
});
