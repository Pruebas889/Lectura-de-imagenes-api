const btnBorrarHistorial = document.getElementById('btnBorrarHistorial');
const btnDescargarJsonHistorial = document.getElementById('btnDescargarJsonHistorial');
const estadoDescargaHistorial = document.getElementById('estadoDescargaHistorial');
const confirmarBorrarHistorial = document.getElementById('confirmarBorrarHistorial');
const cancelarBorradoHistorial = document.getElementById('cancelarBorradoHistorial');
const aceptarBorradoHistorial = document.getElementById('aceptarBorradoHistorial');

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

if (btnBorrarHistorial) {
    btnBorrarHistorial.addEventListener('click', () => {
        confirmarBorrarHistorial.showModal();
    });

    cancelarBorradoHistorial.addEventListener('click', () => {
        confirmarBorrarHistorial.close();
    });

    confirmarBorrarHistorial.addEventListener('click', event => {
        if (event.target === confirmarBorrarHistorial) {
            confirmarBorrarHistorial.close();
        }
    });

    aceptarBorradoHistorial.addEventListener('click', async () => {
        confirmarBorrarHistorial.close();
        const etiquetaOriginal = btnBorrarHistorial.textContent.trim();
        mostrarBotonCargando(btnBorrarHistorial, 'Borrando...');

        try {
            const respuesta = await fetch('/api/facturas', { method: 'DELETE' });
            const resultado = await respuesta.json();
            if (!respuesta.ok || !resultado.ok) {
                throw new Error(resultado.error || 'No se pudo borrar el historial.');
            }
            window.location.reload();
        } catch (error) {
            window.alert(error.message || 'No se pudo conectar al servidor.');
            btnBorrarHistorial.replaceChildren(document.createTextNode(etiquetaOriginal));
            btnBorrarHistorial.disabled = false;
        }
    });
}

if (btnDescargarJsonHistorial) {
    const facturaIds = JSON.parse(btnDescargarJsonHistorial.dataset.facturaIds);
    const contenidoInicial = Array.from(
        btnDescargarJsonHistorial.childNodes,
        nodo => nodo.cloneNode(true)
    );

    btnDescargarJsonHistorial.addEventListener('click', async () => {
        if (facturaIds.length === 0 || btnDescargarJsonHistorial.disabled) return;

        btnDescargarJsonHistorial.disabled = true;
        estadoDescargaHistorial.hidden = false;
        estadoDescargaHistorial.textContent = 'Preparando descarga de JSON...';
        mostrarBotonCargando(btnDescargarJsonHistorial, 'Preparando descarga...');

        try {
            const respuesta = await fetch('/api/v1/documentos/json/descargar-lote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ factura_ids: facturaIds })
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
            estadoDescargaHistorial.textContent =
                `${facturaIds.length} JSON incluidos en la carpeta «Facturas JSON».`;
        } catch (error) {
            estadoDescargaHistorial.textContent =
                error.message || 'No se pudieron descargar los JSON.';
        } finally {
            btnDescargarJsonHistorial.disabled = false;
            btnDescargarJsonHistorial.replaceChildren(
                ...contenidoInicial.map(nodo => nodo.cloneNode(true))
            );
        }
    });
}
