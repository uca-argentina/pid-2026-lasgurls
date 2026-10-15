# JuntApp

Aplicación web para organizar juntadas con amigos: cada persona carga su agenda, ve cuándo están libres sus amigos y coordina encuentros, con invitaciones, encuestas de fecha y notificaciones dentro de la app.

**Demo:** https://juntapp.onrender.com/

Proyecto de la materia PID (UCA, 2026).

---

## Funcionalidades

**Agenda y calendario**
- Eventos personales y juntadas en un calendario semanal, con vista de un solo día en el celular.
- Categorías con color y filtros por categoría y por tipo de juntada.
- Visibilidad por evento: tus amigos ven el título, solo que estás ocupado/a, o nada.

**Juntadas**
- Invitaciones individuales o a grupos, con respuesta *Sí*, *Tal vez* o *No*.
- Buscador de horarios libres en común a partir de la disponibilidad de los invitados.
- Juntadas recurrentes: se repiten todas las semanas, hasta un año.
- Reprogramación: los invitados vuelven a confirmar el nuevo horario.
- Cancelación de una fecha o de toda la serie; el horario vuelve a quedar libre.
- Lugar opcional, con vista previa del mapa y link a Google Maps.
- Comentarios en cada juntada.

**Encuestas de fecha**
- El organizador propone de 2 a 5 opciones de fecha y horario.
- Los invitados votan, y se ve en vivo quién votó y qué opción va ganando.
- Al confirmar la opción ganadora se crea la juntada automáticamente y se cierra la encuesta.
- La encuesta puede ser semanal: la juntada confirmada se repite ese mismo día y horario durante un año.

**Inicio (dashboard)**
- Invitaciones pendientes para responder en el momento.
- Próximas juntadas, estado de las encuestas y un mini calendario de la semana.
- Clic en un horario libre de la semana para crear un evento o una juntada.

**Notificaciones**
- Avisos de invitaciones, respuestas, bajas, reprogramaciones, cancelaciones, comentarios, votos y encuestas.
- Se actualizan solas, igual que el inicio, el calendario y las encuestas: no hace falta recargar la página.

**Amistades y grupos**
- Búsqueda de personas, solicitudes de amistad y grupos de amigos para invitar más rápido.

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3, Flask |
| Base de datos | MySQL alojada en [Aiven](https://aiven.io), con SQLAlchemy como ORM |
| Frontend | Plantillas Jinja, HTML, CSS y JavaScript sin frameworks |
| Tests | pytest |
| Producción | [Render](https://render.com) con gunicorn |

---

## Estructura del proyecto

```
pid-2026-lasgurls/
├── app.py                    Rutas de Flask y armado de las vistas
├── dominio/                  Reglas de negocio y validaciones (sin base de datos)
│   ├── juntada/              Juntada, recurrencia y reprogramación
│   ├── agenda/               Eventos personales
│   ├── disponibilidad/       Búsqueda de horarios libres en común
│   ├── encuesta.py, ubicacion.py, usuario.py, grupo.py, ...
│   └── modulo_utilidades/    Parseo de fechas y horarios, validaciones comunes
├── base_datos/
│   ├── *_tabla.py            Modelos de SQLAlchemy (una tabla por archivo)
│   ├── *_acciones.py         Consultas y operaciones sobre la base
│   ├── crear_tabla.py        Crea todas las tablas en una base nueva
│   ├── migrar_*.py           Migraciones para bases que ya existen
│   ├── configuracion.py      Conexión a la base
│   └── secretos.py           Lee las credenciales (variables de entorno o credenciales.py)
├── templates/                Plantillas HTML (Jinja)
├── static/                   CSS, JavaScript e imágenes
├── tests/                    Tests de dominio con pytest
└── pruebas_en_base_de_datos/ Scripts manuales para probar contra la base real
```

El código está separado en capas: `dominio/` valida las reglas sin conocer la base de datos, `base_datos/` se ocupa de guardar y consultar, y `app.py` une las dos con las vistas.

---

## Cómo correrlo en local

### Requisitos
- Python 3.12 o superior
- Acceso a la base MySQL de Aiven (credenciales y certificado `ca.pem`)

### 1. Clonar el repositorio y crear el entorno virtual
```bash
git clone https://github.com/uca-argentina/pid-2026-lasgurls.git
cd pid-2026-lasgurls
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar las credenciales
Crear el archivo `base_datos/credenciales.py`, que no se sube al repositorio:

```python
HOST = "tu-servicio.aivencloud.com"
PUERTO = 12345
USUARIO = "usuario"
PASSWORD = "contraseña"
BASE = "defaultdb"
SECRET_KEY = "una-clave-larga-y-aleatoria"
```

Copiar el certificado de Aiven como `ca.pem` en la raíz del proyecto. También está excluido del repositorio.

### 3. Crear las tablas (solo para una base nueva)
```bash
python3 -m base_datos.crear_tabla
python3 -m base_datos.migrar_categorias
```
El segundo comando carga las categorías que vienen con la app. Si la base ya existe y se agregó una tabla o columna nueva, alcanza con correr el `migrar_*.py` correspondiente. Todos se pueden correr más de una vez sin romper nada.

### 4. Levantar la app
```bash
python3 app.py
```
Abrir **http://localhost:5001**.

Para probarla desde el celular en la misma red WiFi, entrar a `http://<IP de la compu>:5001`. La IP se ve en Mac con `ipconfig getifaddr en0`.

---

## Tests

```bash
pytest -v
```

Los tests cubren las reglas de dominio: registro y login, juntadas, recurrencia, reprogramación, encuestas, disponibilidad, categorías, grupos, comentarios y ubicación. No necesitan conexión a la base.

---

## Deploy

La app está publicada en Render y se actualiza automáticamente con cada push a `main`.

| Configuración | Valor |
|---|---|
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app` |
| Variables de entorno | `DB_HOST`, `DB_PUERTO`, `DB_USUARIO`, `DB_PASSWORD`, `DB_BASE`, `SECRET_KEY` |
| Secret file | `ca.pem` |

Si existen las variables de entorno, la app las usa. Si no, lee `base_datos/credenciales.py`. La zona horaria se fija en Argentina desde el código, así que no depende de la configuración del servidor.

> En el plan gratuito de Render, el servicio se suspende después de unos 15 minutos sin uso; la primera visita después de eso puede tardar alrededor de un minuto.

---

## Flujo de trabajo con Git

| Rama | Uso |
|---|---|
| `main` | Versión publicada en Render. |
| `develop` | Integración y pruebas antes de pasar a `main`. |
| `S<n>/<funcionalidad>` | Una rama por funcionalidad, que se mergea con un pull request. |
