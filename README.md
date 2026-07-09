# Sistema de Vacaciones — OMG Worldwide Group

Una mini-aplicación para ordenar el proceso de solicitud de vacaciones en una empresa, sin WhatsApps ni "déjame te confirmo".

## 🚀 Demo en vivo

- **App:** https://vacaciones-app-three.vercel.app
- **API (docs interactivos):** https://vacaciones-backend-3frq.onrender.com/docs

> El backend está en el plan gratis de Render, así que si nadie lo usa por 15 minutos "se duerme". La primera petición puede tardar 30-60 segundos mientras despierta — es normal.

---

## ¿Qué problema resuelve?

En casi toda empresa pedir vacaciones es un caos: WhatsApp al jefe, el jefe le escribe a RRHH, nadie sabe en qué estado quedó. Esta app ordena ese proceso de principio a fin con tres roles claros y un flujo que siempre sigue el mismo camino.

---

## Cómo funciona el flujo
Empleado crea solicitud → Jefe aprueba o rechaza → RRHH confirma o rechaza

Cada paso tiene un estado claro:

| Estado | Significa |
|---|---|
| Pendiente jefe | El empleado envió la solicitud, el jefe no ha respondido |
| Aprobada por jefe | El jefe dijo que sí, ahora le toca a RRHH |
| Rechazada por jefe | El jefe dijo que no, con comentario |
| Pendiente RRHH | RRHH tiene que confirmar |
| Confirmada | RRHH aprobó, vacaciones listas |
| Rechazada por RRHH | RRHH rechazó, con comentario |

### Lo que puede hacer cada rol

**Empleado:**
- Crea una solicitud con fecha inicio, fecha fin y motivo
- Ve el estado de todas sus solicitudes e historial
- Ve cuántos días le quedan disponibles
- El sistema no le deja pedir vacaciones en fechas que ya tiene ocupadas
- Si no tiene suficientes días, el sistema se lo avisa

**Jefe:**
- Ve solo las solicitudes de su equipo (empleados asignados a él)
- Aprueba o rechaza con un comentario
- Puede pedir un análisis de IA que resume la situación del empleado antes de decidir
- Solo puede actuar sobre solicitudes en estado "pendiente jefe"

**RRHH:**
- Ve todas las solicitudes que el jefe ya aprobó
- Confirma o rechaza con comentario
- Ve el saldo de días disponibles de cada empleado antes de confirmar
- Puede pedir una sugerencia de comentario generada por IA
- Si el saldo es insuficiente, el sistema lo advierte y bloquea la confirmación
- Al confirmar, descuenta los días del saldo del empleado automáticamente

---

## Lógica de días (contexto colombiano)

En Colombia los trabajadores tienen 15 días hábiles de vacaciones por año. Cada usuario empieza con ese saldo. El sistema descuenta los días cuando RRHH confirma la solicitud — no antes, porque hasta ese momento no es oficial.

Se valida dos veces:
1. Cuando el empleado crea la solicitud (para no dejar pasar algo imposible desde el inicio)
2. Cuando RRHH confirma (porque pueden haber cambiado las cosas entre medias)

También se valida que no se puedan crear dos solicitudes con fechas que se crucen.

---

## Componente IA dentro del producto

Integré **Groq** (con el modelo llama-3.3-70b-versatile) en dos puntos del flujo:

**1. Análisis para el jefe**
Cuando el jefe va a aprobar o rechazar una solicitud, puede pedir un análisis automático que resume la situación del empleado: cuántos días pide, cuántos le quedan, cuántas solicitudes lleva este año. El objetivo es que el jefe tome la decisión con más contexto sin tener que buscar esa información manualmente.

**2. Sugerencia de comentario para RRHH**
Cuando RRHH va a confirmar o rechazar, puede pedir una sugerencia de comentario profesional según la decisión que va a tomar. La sugerencia se pone en el campo de comentario pero RRHH puede editarla antes de enviar.

**Por qué aquí y no en otro lugar:**
Estos son los dos puntos donde alguien tiene que tomar una decisión y un poco de contexto adicional ayuda. La IA no toma ninguna decisión — solo informa y sugiere. Los cálculos de saldo, estados y aprobaciones siguen siendo 100% determinísticos en el backend.

---

## Arquitectura

```mermaid
flowchart LR
    subgraph Vercel["Vercel (estático)"]
        FE[Frontend<br/>HTML + CSS + JS]
    end

    subgraph Render["Render"]
        API[Backend<br/>FastAPI]
        DB[(PostgreSQL)]
    end

    subgraph Groq["Groq API"]
        IA[LLM<br/>llama-3.3-70b]
    end

    FE -- HTTP/JSON --> API
    API -- SQLAlchemy --> DB
    API -- Análisis y sugerencias --> IA

    E([Empleado]) --> FE
    J([Jefe]) --> FE
    R([RRHH]) --> FE

    API --> S1[Pendiente jefe]
    S1 --> S2[Aprobada/Rechazada jefe]
    S2 --> S3[Pendiente RRHH]
    S3 --> S4[Confirmada/Rechazada RRHH]
```

El frontend le habla al backend por peticiones HTTP. El backend valida todas las reglas de negocio y guarda todo en PostgreSQL. La IA se usa solo como apoyo informativo, nunca para tomar decisiones críticas. Los roles se simulan con un selector de usuario, sin login real como dice el reto.

**Estructura del proyecto:**
vacaciones-app/
├── backend/
│   ├── main.py              # Punto de entrada
│   ├── database.py          # Conexión a PostgreSQL
│   ├── models.py            # Tablas: usuarios y solicitudes
│   ├── ia.py                # Funciones de IA con Groq
│   └── routers/
│       ├── usuarios.py      # Crear y consultar usuarios
│       └── solicitudes.py   # Todo el flujo de aprobación
└── frontend/
├── index.html           # Estructura
├── style.css            # Estilos
└── app.js               # Lógica y llamadas al API

---

## Infraestructura

- **Backend:** Render — Web Service conectado al repositorio de GitHub, redeploy automático con cada `git push`
- **Base de datos:** Render PostgreSQL, en la misma región que el backend
- **Frontend:** Vercel — Static Site apuntando a la carpeta `frontend/`
- **IA:** Groq API — llamadas desde el backend, la API key se inyecta como variable de entorno
- **Variables de entorno:** La cadena de conexión y la API key de Groq se inyectan como variables en Render, no están hardcodeadas

---

## Tecnologías elegidas y por qué

- **FastAPI:** Ya lo había usado en proyectos académicos, es rápido de montar y tiene documentación automática en `/docs` que ayuda mucho para probar sin necesidad de Postman
- **PostgreSQL:** Base de datos relacional que encaja bien con los estados y relaciones entre usuarios y solicitudes
- **HTML + CSS + JS puro:** No necesitaba Angular ni React para este flujo, habría sido sobredimensionado y habría tomado más tiempo
- **SQLAlchemy:** Para manejar los modelos sin escribir SQL directo
- **Groq:** API de IA gratuita y muy rápida, perfecta para este caso donde necesitaba respuestas en menos de 2 segundos

**Alternativa descartada:** Pensé en usar SQLite para no necesitar instalar PostgreSQL, pero finalmente lo instalé porque el reto pedía algo más cercano a producción y Render también lo soporta gratis.

---

## Cómo correrlo en local

**Requisitos:** Python 3.10+, PostgreSQL instalado

**1. Clonar el repositorio**
```bash
git clone https://github.com/DannyRendon/vacaciones-app.git
cd vacaciones-app
```

**2. Configurar el backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configurar la base de datos**

Crear una base de datos en PostgreSQL llamada `vacaciones_db` y actualizar la contraseña en `database.py`:
```python
DATABASE_URL = "postgresql://postgres:TU_CONTRASEÑA@localhost:5432/vacaciones_db"
```

**4. Configurar la API key de Groq**

En `ia.py` reemplaza `TU_API_KEY_AQUI` con tu key de Groq (gratis en groq.com).

**5. Correr el backend**
```bash
uvicorn main:app --reload
```

**6. Correr el frontend**
```bash
cd ../frontend
python -m http.server 3000
```

**7. Abrir en el navegador**
http://localhost:3000

**8. Crear usuarios de prueba**

Ir a `http://localhost:8000/docs` y crear usuarios con los roles `rrhh`, `jefe` y `empleado`. Al crear un empleado, asignarle el `jefe_id` del jefe correspondiente para que quede en su equipo.

---

## Cómo usé la IA para construirlo

Usé Claude y Cursor principalmente. Claude me ayudó a planear la estructura, definir los modelos y escribir los endpoints. Cursor me ayudó a editar los archivos directamente dentro del proyecto.

Hubo varios momentos donde tuve que intervenir yo: el entorno virtual de Python se creó con carpeta `bin` en vez de `Scripts` porque tenía varios intérpretes instalados en Windows, y eso lo tuve que depurar yo en la terminal. También hubo un problema con el CSS donde el login con `position: fixed` tapaba el panel al entrar, y lo resolví revisando el comportamiento en el navegador. Otro caso fue que Groq descontinuó el modelo `llama3-8b-8192` y tuve que identificar el error en los logs y cambiar al modelo actualizado.

En general usé la IA como un par de programación, no como alguien que hace todo solo — las decisiones de arquitectura, qué validar y cómo estructurar el flujo las tomé yo.

---

## Respuestas a las preguntas del reto

Las respuestas están en el archivo `RESPUESTAS.md`.