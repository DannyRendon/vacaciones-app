const API = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "https://vacaciones-backend-3frq.onrender.com";
let usuarioActual = null;

// Cargar usuarios al iniciar
async function cargarUsuarios() {
    const res = await fetch(`${API}/usuarios/`);
    const usuarios = await res.json();
    const selector = document.getElementById("selector-usuario");
    usuarios.forEach(u => {
        const option = document.createElement("option");
        option.value = u.id;
        option.textContent = `${u.nombre} (${u.rol})`;
        selector.appendChild(option);
    });

    const idEnUrl = window.location.hash.replace("#", "");
    if (idEnUrl) {
        selector.value = idEnUrl;
        await entrar();
    }
}

// Entrar al sistema
async function entrar() {
    const id = document.getElementById("selector-usuario").value;
    if (!id) return alert("Selecciona un usuario");

    const res = await fetch(`${API}/usuarios/${id}`);
    usuarioActual = await res.json();

    window.location.hash = usuarioActual.id;

    document.getElementById("pantalla-login").classList.add("oculto");
    document.getElementById("panel-principal").classList.remove("oculto");
    document.getElementById("saludo").textContent = `Hola, ${usuarioActual.nombre}`;

    if (usuarioActual.rol === "empleado") {
        document.getElementById("vista-empleado").classList.remove("oculto");
        mostrarSaldoEmpleado();
        cargarSolicitudesEmpleado();
    } else if (usuarioActual.rol === "jefe") {
        document.getElementById("vista-jefe").classList.remove("oculto");
        cargarSolicitudesJefe();
    } else if (usuarioActual.rol === "rrhh") {
        document.getElementById("vista-rrhh").classList.remove("oculto");
        cargarSolicitudesRrhh();
    }
}

// Cerrar sesión
function cerrarSesion() {
    window.location.hash = "";
    location.reload();
}

// Mostrar saldo de días del empleado
async function mostrarSaldoEmpleado() {
    const res = await fetch(`${API}/usuarios/${usuarioActual.id}`);
    const usuario = await res.json();
    document.getElementById("saldo-empleado").textContent =
        `Te quedan ${usuario.dias_disponibles} días de vacaciones`;
}

// Empleado crea solicitud
async function crearSolicitud() {
    const inicio = document.getElementById("fecha-inicio").value;
    const fin = document.getElementById("fecha-fin").value;
    const motivo = document.getElementById("motivo").value;

    if (!inicio || !fin || !motivo) return alert("Completa todos los campos");
    if (fin < inicio) return alert("La fecha fin no puede ser menor que la fecha inicio");

    const res = await fetch(`${API}/solicitudes/?empleado_id=${usuarioActual.id}&fecha_inicio=${inicio}&fecha_fin=${fin}&motivo=${motivo}`, {
        method: "POST"
    });

    if (res.ok) {
        alert("Solicitud enviada correctamente");
        mostrarSaldoEmpleado();
        cargarSolicitudesEmpleado();
    } else {
        const error = await res.json();
        alert("Error: " + error.detail);
    }
}

// Ver solicitudes del empleado
async function cargarSolicitudesEmpleado() {
    const res = await fetch(`${API}/solicitudes/empleado/${usuarioActual.id}`);
    const solicitudes = await res.json();
    const contenedor = document.getElementById("lista-solicitudes-empleado");
    contenedor.innerHTML = "";

    if (solicitudes.length === 0) {
        contenedor.innerHTML = "<p class='sin-datos'>No tienes solicitudes aún.</p>";
        return;
    }

    solicitudes.forEach(s => {
        contenedor.innerHTML += `
            <div class="tarjeta ${s.estado}">
                <h4>${s.motivo}</h4>
                <p>📅 ${s.fecha_inicio} → ${s.fecha_fin} (${s.dias_solicitados} ${s.dias_solicitados === 1 ? "día" : "días"})</p>
                <span class="badge ${s.estado}">${s.estado.replace(/_/g, " ")}</span>
                ${s.comentario_jefe ? `<p>💬 Jefe: ${s.comentario_jefe}</p>` : ""}
                ${s.comentario_rrhh ? `<p>💬 RRHH: ${s.comentario_rrhh}</p>` : ""}
            </div>
        `;
    });
}

// Ver solicitudes pendientes para el jefe
async function cargarSolicitudesJefe() {
    const res = await fetch(`${API}/solicitudes/jefe/${usuarioActual.id}`);
    const delEquipo = await res.json();
    const pendientes = delEquipo.filter(s => s.estado === "pendiente_jefe");
    const contenedor = document.getElementById("lista-solicitudes-jefe");
    contenedor.innerHTML = "";

    if (pendientes.length === 0) {
        contenedor.innerHTML = "<p class='sin-datos'>No hay solicitudes pendientes de tu equipo.</p>";
        return;
    }

    for (const s of pendientes) {
        const resEmpleado = await fetch(`${API}/usuarios/${s.empleado_id}`);
        const empleado = await resEmpleado.json();

        contenedor.innerHTML += `
            <div class="tarjeta pendiente_jefe" id="tarjeta-${s.id}">
                <h4>Solicitud #${s.id} — ${empleado.nombre}</h4>
                <p>📅 ${s.fecha_inicio} → ${s.fecha_fin} (${s.dias_solicitados} ${s.dias_solicitados === 1 ? "día" : "días"})</p>
                <p>📝 ${s.motivo}</p>
                <div class="resumen-ia" id="resumen-${s.id}">
                    <button class="btn-ia" onclick="cargarResumenJefe(${s.id})">🤖 Ver análisis IA</button>
                </div>
                <div class="acciones">
                    <input type="text" id="comentario-jefe-${s.id}" placeholder="Comentario (opcional)">
                    <button class="btn-aprobar" onclick="decidirJefe(${s.id}, 'aprobar')">Aprobar</button>
                    <button class="btn-rechazar" onclick="decidirJefe(${s.id}, 'rechazar')">Rechazar</button>
                </div>
            </div>
        `;
    }
}

// Cargar resumen de IA para el jefe
async function cargarResumenJefe(id) {
    const contenedor = document.getElementById(`resumen-${id}`);
    contenedor.innerHTML = "<p class='cargando-ia'>🤖 Analizando solicitud...</p>";

    const res = await fetch(`${API}/solicitudes/${id}/resumen-jefe`);
    const data = await res.json();

    contenedor.innerHTML = `
        <div class="caja-ia">
            <span class="ia-label">🤖 Análisis IA</span>
            <p>${data.resumen}</p>
        </div>
    `;
}

// Jefe toma decisión
async function decidirJefe(id, decision) {
    const comentario = document.getElementById(`comentario-jefe-${id}`).value;
    const res = await fetch(`${API}/solicitudes/${id}/jefe?decision=${decision}&comentario=${comentario}`, {
        method: "PUT"
    });

    if (res.ok) {
        alert(`Solicitud ${decision === "aprobar" ? "aprobada" : "rechazada"} correctamente`);
        cargarSolicitudesJefe();
    }
}

// Ver solicitudes pendientes para RRHH
async function cargarSolicitudesRrhh() {
    const res = await fetch(`${API}/solicitudes/`);
    const todas = await res.json();
    const pendientes = todas.filter(s => s.estado === "pendiente_rrhh");
    const contenedor = document.getElementById("lista-solicitudes-rrhh");
    contenedor.innerHTML = "";

    if (pendientes.length === 0) {
        contenedor.innerHTML = "<p class='sin-datos'>No hay solicitudes pendientes de confirmación.</p>";
        return;
    }

    for (const s of pendientes) {
        const resEmpleado = await fetch(`${API}/usuarios/${s.empleado_id}`);
        const empleado = await resEmpleado.json();
        const alcanza = empleado.dias_disponibles >= s.dias_solicitados;

        contenedor.innerHTML += `
            <div class="tarjeta pendiente_rrhh">
                <h4>Solicitud #${s.id} — ${empleado.nombre}</h4>
                <p>📅 ${s.fecha_inicio} → ${s.fecha_fin} (${s.dias_solicitados} ${s.dias_solicitados === 1 ? "día" : "días"})</p>
                <p>📝 ${s.motivo}</p>
                <p class="${alcanza ? "saldo-ok" : "saldo-bajo"}">
                    Saldo del empleado: ${empleado.dias_disponibles} días
                    ${alcanza ? "" : "⚠️ insuficiente para esta solicitud"}
                </p>
                ${s.comentario_jefe ? `<p>💬 Jefe: ${s.comentario_jefe}</p>` : ""}
                <div class="sugerencia-ia" id="sugerencia-${s.id}">
                    <button class="btn-ia" onclick="cargarSugerenciaRrhh(${s.id}, 'confirmar')">🤖 Sugerencia para confirmar</button>
                    <button class="btn-ia" onclick="cargarSugerenciaRrhh(${s.id}, 'rechazar')">🤖 Sugerencia para rechazar</button>
                </div>
                <div class="acciones">
                    <input type="text" id="comentario-rrhh-${s.id}" placeholder="Comentario (opcional)">
                    <button class="btn-aprobar" onclick="decidirRrhh(${s.id}, 'confirmar')">Confirmar</button>
                    <button class="btn-rechazar" onclick="decidirRrhh(${s.id}, 'rechazar')">Rechazar</button>
                </div>
            </div>
        `;
    }
}

// Cargar sugerencia de IA para RRHH
async function cargarSugerenciaRrhh(id, decision) {
    const contenedor = document.getElementById(`sugerencia-${id}`);
    contenedor.innerHTML = "<p class='cargando-ia'>🤖 Generando sugerencia...</p>";

    const res = await fetch(`${API}/solicitudes/${id}/sugerencia-rrhh?decision=${decision}`);
    const data = await res.json();

    document.getElementById(`comentario-rrhh-${id}`).value = data.sugerencia;

    contenedor.innerHTML = `
        <div class="caja-ia">
            <span class="ia-label">🤖 Sugerencia IA — puedes editarla antes de enviar</span>
        </div>
    `;
}

// RRHH toma decisión
async function decidirRrhh(id, decision) {
    const comentario = document.getElementById(`comentario-rrhh-${id}`).value;
    const res = await fetch(`${API}/solicitudes/${id}/rrhh?decision=${decision}&comentario=${comentario}`, {
        method: "PUT"
    });

    if (res.ok) {
        alert(`Solicitud ${decision === "confirmar" ? "confirmada" : "rechazada"} correctamente`);
        cargarSolicitudesRrhh();
    } else {
        const error = await res.json();
        alert("Error: " + error.detail);
    }
}

// Arrancar
cargarUsuarios();