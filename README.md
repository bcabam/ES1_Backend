# Colegio Digital

Aplicación web desarrollada con **Django** para la gestión académica de un colegio. Permite administrar estudiantes y docentes, registrar notas y controlar el acceso según el perfil de cada usuario.

Proyecto de la asignatura **Programación Back End (TI3V41)** — INACAP, Ingeniería en Informática.

| Integrante | Aplicación |
|---|---|
| Jorge Pavez Andía | `AdministrativosApp` |
| Silvana Bastidas | `DocentesApp` |
| Benjamín Caba | `EstudiantesApp` |

---

## Tecnologías

- Python 3.14 y Django 6.1
- MySQL 8.4 (WAMP en desarrollo) con `mysqlclient`
- `python-dotenv` para las variables de entorno
- `Pillow` para las imágenes (`ImageField`)
- Bootstrap 5 local (en `static/bootstrap/`)

---

## Aplicaciones

| App | Contenido |
|---|---|
| `AdministrativosApp` | Login único, perfiles y permisos, creación de usuarios, funcionarios administrativos con foto y contrato PDF |
| `DocentesApp` | Mantenedor de docentes (CRUD) y panel docente |
| `EstudiantesApp` | Visualización de notas del estudiante |
| `config` | Configuración del proyecto, rutas principales y control de acceso (`autorizacion.py`) |

---

## Perfiles de usuario

El acceso usa **Django Authentication**. Cada perfil es un **Grupo** de Django y cada uno ve un menú distinto.

| Perfil | Perfil de la pauta | Puede |
|---|---|---|
| Administrador | Administrador | Todo: crear, modificar, eliminar, consultar y administrar usuarios |
| Administrativo | Operador | Crear, modificar y consultar estudiantes y docentes. **No** elimina ni administra usuarios |
| Docente | — | Registrar y modificar notas |
| Estudiante | Consulta | Solo ver sus notas |

Usuarios de prueba (se crean con `crear_perfiles --demo`), todos con la clave **`Colegio2026!`**:

`admin` · `administrativo` · `docente` · `estudiante`

> Solo para desarrollo. En el servidor de producción se deben crear usuarios con contraseñas propias.

---

## Instalación en un equipo nuevo

### 1. Requisitos

- **WAMP** con **MySQL 8.4** (no usar XAMPP: su MariaDB es muy antigua para Django 6).
- Python 3.14 y Git.

> Si en el equipo hay otra MySQL instalada aparte de WAMP, puede estar ocupando el puerto 3306 y WAMP no podrá encender la suya. Revísalo en `services.msc`.

### 2. Clonar el repositorio

```bash
git clone https://github.com/bcabam/ES1_Backend.git
cd ES1_Backend
```

### 3. Crear la base de datos

Abre phpMyAdmin (`http://localhost/phpmyadmin5.2.3/` o desde el ícono de WAMP), entra con `root` y **Server Choice: MySQL**. En la pestaña **SQL** ejecuta, cambiando `TuContraseña`:

```sql
CREATE DATABASE colegio_digital CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'colegio'@'localhost' IDENTIFIED BY 'TuContraseña';
GRANT ALL PRIVILEGES ON colegio_digital.* TO 'colegio'@'localhost';
GRANT ALL PRIVILEGES ON test_colegio_digital.* TO 'colegio'@'localhost';
FLUSH PRIVILEGES;
```

> Crea el usuario **con este SQL**, no con el formulario de "Cuentas de usuarios": el formulario puede usar el método `mysql_native_password`, que MySQL 8.4 trae desactivado.

### 4. Crear el archivo `.env`

```powershell
copy .env.example .env
```

Completa en `.env`:

- `DB_PASSWORD`: la misma contraseña del paso 3.
- `SECRET_KEY`: una clave aleatoria. Puedes generarla con:
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```

El `.env` **nunca** se sube a GitHub (está en `.gitignore`).

### 5. Entorno virtual y dependencias

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Si PowerShell no deja activar el venv, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 6. Tablas, perfiles y datos iniciales

```powershell
python manage.py migrate
python manage.py crear_perfiles --demo
python manage.py loaddata funcionarios docentes
```

### 7. Ejecutar

```powershell
python manage.py runserver
```

- Sitio: http://127.0.0.1:8000/login/
- Django Admin: http://127.0.0.1:8000/admin/ (usuario `admin`)

---

## Trabajo en equipo

Cada integrante trabaja con **su propia base de datos** en su equipo. Por GitHub se comparte la **estructura** (modelos y migraciones) y los **datos de ejemplo** (fixtures), nunca la base en sí.

| Se sube a GitHub | Queda solo en cada equipo |
|---|---|
| `models.py`, `migrations/` | La base `colegio_digital` y sus registros |
| `fixtures/` | El archivo `.env` |
| `.env.example`, `requirements.txt` | La carpeta `media/` (fotos y PDF subidos) |

### Reglas

1. **Cada uno trabaja en su rama** y los cambios llegan a `main` mediante Pull Request.

2. **Después de cada `git pull` o `git merge`, ejecutar `migrate`**:
   ```powershell
   git fetch origin
   git merge origin/main
   python manage.py migrate
   ```

3. **Cada uno genera migraciones solo de su propia app** y las sube junto con su `models.py`:
   ```powershell
   python manage.py makemigrations DocentesApp
   ```
   Nunca editar ni borrar migraciones que ya subió otro integrante.

4. **Los datos de ejemplo se comparten con fixtures**:
   ```powershell
   # Exportar (quien creó los datos)
   python manage.py dumpdata DocentesApp.docente --indent 4 -o DocentesApp/fixtures/docentes.json
   # Cargar (los demás)
   python manage.py loaddata docentes
   ```

5. **Cuando aparezca un nuevo modelo con permisos**, volver a ejecutar `python manage.py crear_perfiles` para asignar sus permisos a los grupos.

6. **No subir** `.env`, `media/`, `venv/` ni `db.sqlite3`. Si `git status` los muestra, revisar el `.gitignore`.

---

## Pruebas

```powershell
python manage.py test
```

Requiere que el usuario `colegio` tenga permisos sobre `test_colegio_digital` (incluido en el SQL del paso 3).

---

## Problemas frecuentes

| Error | Solución |
|---|---|
| `Access denied for user 'colegio'@'localhost'` | La contraseña del `.env` no coincide con la de MySQL en ese equipo |
| `Plugin 'mysql_native_password' is not loaded` | En phpMyAdmin: `ALTER USER 'colegio'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'TuContraseña';` |
| `Can't connect to MySQL server on '127.0.0.1:3306'` | La MySQL de WAMP está apagada o hay otra MySQL usando el puerto 3306 |
| `The SECRET_KEY setting must not be empty` | Falta el archivo `.env` |
| `No module named 'dotenv'` / `'MySQLdb'` | Falta `pip install -r requirements.txt` (con el venv activo) |
| `Table ... doesn't exist` / `Unknown column` | Falta `python manage.py migrate` |
| `Conflicting migrations detected` | `python manage.py makemigrations --merge` |
| Not Found en `localhost/phpmyadmin` | En WAMP la ruta incluye la versión: `localhost/phpmyadmin5.2.3/` |

---

## Estructura del proyecto

```
ES1_Backend/
├── AdministrativosApp/       # Login, perfiles, usuarios y funcionarios
│   ├── fixtures/             # Datos iniciales (funcionarios.json)
│   ├── management/commands/  # Comando crear_perfiles
│   ├── forms.py, models.py, views.py, urls.py, admin.py
│   └── templates/AdministrativosApp/
├── DocentesApp/              # Mantenedor de docentes y panel docente
├── EstudiantesApp/           # Notas del estudiante
├── config/
│   ├── settings.py           # Lee la configuración sensible desde .env
│   ├── urls.py               # Rutas principales: login, logout, panel y apps
│   └── autorizacion.py       # Perfiles y decorador requiere_rol
├── templates/base.html       # Plantilla base con menú dinámico por perfil
├── static/                   # Bootstrap local, CSS e imágenes
├── media/                    # Archivos subidos (no se versiona)
├── .env.example              # Plantilla de variables de entorno
├── requirements.txt
└── manage.py
```
