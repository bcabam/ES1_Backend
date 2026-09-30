# Despliegue en AWS EC2 (AWS Academy)

Guía para desplegar **Colegio Digital** en una instancia EC2 de **AWS Academy (Learner Lab)**, con la base de datos MySQL y phpMyAdmin dentro de la misma instancia.

## Arquitectura

```
Navegador ──► Apache (puerto 80)
                ├── /static/      → archivos estáticos (staticfiles/)
                ├── /media/       → fotos y PDF subidos (media/)
                ├── /phpmyadmin   → phpMyAdmin
                └── /             → Gunicorn (127.0.0.1:8000) → Django
                                                        │
                                                        ▼
                                                 MySQL (colegio_digital)
```

## Antes de empezar: particularidades de AWS Academy

- La sesión del laboratorio dura unas **4 horas**. Al terminar, **la instancia se apaga**.
- **La IP pública cambia cada vez que se inicia el laboratorio.** El script `deploy/actualizar_ip.sh` la actualiza en el `.env` automáticamente al arrancar el servicio, así que solo cambia la URL que se abre en el navegador.
- Django queda instalado como servicio (`colegio`), por lo que **arranca solo** cuando se enciende la instancia.
- **Antes de la revisión presencial**, inicia el laboratorio con tiempo y comprueba que todo funcione.

---

## 1. Crear la instancia

1. En AWS Academy: **Start Lab** → esperar el círculo verde → clic en **AWS**.
2. Ir a **EC2 → Instances → Launch instances**:
   - **Name:** `colegio-digital`
   - **AMI:** Ubuntu Server **24.04 LTS**
   - **Instance type:** `t2.micro` (o `t3.micro`)
   - **Key pair:** `vockey`
   - **Network settings → Security group:** permitir **SSH (22)** y **HTTP (80)** desde cualquier lugar (0.0.0.0/0)
   - **Storage:** 16 GiB
3. **Launch instance** y copiar la **IP pública** (Public IPv4 address).

## 2. Conectarse por SSH

En AWS Academy: **AWS Details → Download PEM** (descarga `labsuser.pem`).

Desde PowerShell, en la carpeta donde quedó el archivo:

```powershell
ssh -i labsuser.pem ubuntu@IP_PUBLICA
```

> Si Windows reclama por los permisos del archivo:
> ```powershell
> icacls labsuser.pem /inheritance:r
> icacls labsuser.pem /grant:r "$($env:USERNAME):(R)"
> ```
> Alternativa sin SSH: en la consola de EC2, seleccionar la instancia → **Connect → EC2 Instance Connect**.

Todos los comandos siguientes se ejecutan **dentro de la instancia**.

## 3. Instalar paquetes del sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-dev build-essential pkg-config \
    default-libmysqlclient-dev mysql-server apache2 git
```

- `python3-dev`, `build-essential`, `pkg-config` y `default-libmysqlclient-dev` son necesarios para compilar `mysqlclient`.
- `mysql-server` es la base de datos; `apache2` es el servidor web.

## 4. Crear la base de datos

```bash
sudo mysql
```

Dentro de MySQL (cambiar `ClaveSegura` por una contraseña propia):

```sql
CREATE DATABASE colegio_digital CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'colegio'@'localhost' IDENTIFIED BY 'ClaveSegura';
GRANT ALL PRIVILEGES ON colegio_digital.* TO 'colegio'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 5. Instalar phpMyAdmin

```bash
sudo apt install -y phpmyadmin
```

Durante la instalación:

1. **Servidor web:** marcar **apache2** con la **barra espaciadora** (debe quedar con `*`) y luego Enter.
2. **¿Configurar la base de datos con dbconfig-common?** → **Yes**.
3. Ingresar una contraseña para el usuario interno de phpMyAdmin.

Queda disponible en `http://IP_PUBLICA/phpmyadmin`. Se ingresa con el usuario **`colegio`** y la contraseña del paso 4.

## 6. Clonar el proyecto desde GitHub

```bash
cd /home/ubuntu
git clone https://github.com/bcabam/ES1_Backend.git
cd ES1_Backend
```

## 7. Entorno virtual y dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 8. Crear el archivo `.env`

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # copia la clave generada
nano .env
```

Dejarlo así (con la clave generada y la contraseña del paso 4):

```ini
SECRET_KEY=la-clave-generada
DEBUG=False
ALLOWED_HOSTS=localhost
CSRF_TRUSTED_ORIGINS=

DB_NAME=colegio_digital
DB_USER=colegio
DB_PASSWORD=ClaveSegura
DB_HOST=127.0.0.1
DB_PORT=3306
```

`ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` se completan solos con la IP pública al iniciar el servicio (paso 10). Para guardar en nano: `Ctrl+O`, Enter, `Ctrl+X`.

## 9. Preparar Django

```bash
python manage.py migrate
python manage.py crear_perfiles --demo
python manage.py loaddata funcionarios docentes estudiantes
python manage.py collectstatic --noinput
mkdir -p media
```

## 10. Servicio de Django (Gunicorn)

```bash
sudo cp deploy/colegio.service /etc/systemd/system/colegio.service
sudo systemctl daemon-reload
sudo systemctl enable --now colegio
sudo systemctl status colegio
```

Debe decir **active (running)**. Salir con `q`.

## 11. Configurar Apache

```bash
sudo cp deploy/apache-colegio.conf /etc/apache2/sites-available/colegio.conf
sudo a2enmod proxy proxy_http
sudo a2dissite 000-default
sudo a2ensite colegio
chmod 755 /home/ubuntu
sudo systemctl restart apache2
```

`chmod 755 /home/ubuntu` permite que Apache lea los archivos estáticos y subidos.

## 12. Probar

- Sitio: `http://IP_PUBLICA/login/` (usuarios `admin`, `administrativo`, `docente`, `estudiante` — clave `Colegio2026!`)
- Django Admin: `http://IP_PUBLICA/admin/`
- phpMyAdmin: `http://IP_PUBLICA/phpmyadmin`

> Las fotos y PDF subidos en los equipos locales **no** están en el servidor: hay que volver a subirlos desde el sitio o el admin para la demostración.

---

## Cada vez que se inicia el laboratorio

1. **Start Lab** → AWS → EC2. Si la instancia está detenida: **Instance state → Start instance**.
2. Copiar la **nueva IP pública**.
3. Abrir `http://NUEVA_IP/login/`. El servicio ya actualizó la IP en el `.env` al arrancar.

Si algo no responde:

```bash
sudo systemctl restart colegio
sudo systemctl restart apache2
```

## Actualizar el servidor con cambios nuevos de GitHub

```bash
cd /home/ubuntu/ES1_Backend
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py crear_perfiles
python manage.py collectstatic --noinput
sudo systemctl restart colegio
```

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El navegador no carga nada | Falta el puerto 80 en el Security Group, o la IP cambió | Revisar el Security Group y usar la IP actual |
| `502 Bad Gateway` | Gunicorn no está corriendo | `sudo systemctl status colegio` y `journalctl -u colegio -n 50` |
| `400 Bad Request` | La IP no está en `ALLOWED_HOSTS` | `sudo systemctl restart colegio` (vuelve a leer la IP) |
| `403 CSRF verification failed` al enviar un formulario | Falta la IP en `CSRF_TRUSTED_ORIGINS` | `sudo systemctl restart colegio` |
| Página sin estilos | Falta `collectstatic` o permisos | `python manage.py collectstatic --noinput` y `chmod 755 /home/ubuntu` |
| Error al instalar `mysqlclient` | Faltan paquetes de compilación | Repetir el paso 3 |
| `Access denied for user 'colegio'` | La contraseña del `.env` no coincide con la de MySQL | Revisar `DB_PASSWORD` |

Ver errores de Django: `journalctl -u colegio -n 50`
Ver errores de Apache: `sudo tail -n 50 /var/log/apache2/colegio_error.log`

---

## Evidencias para la revisión presencial

- [ ] Conexión a la instancia por SSH
- [ ] Entorno virtual activo (`source venv/bin/activate`)
- [ ] Proyecto clonado con `git clone` (`git remote -v`, `git log --oneline`)
- [ ] Servicio corriendo (`sudo systemctl status colegio`)
- [ ] Sitio funcionando en `http://IP_PUBLICA`
- [ ] Tablas y relaciones en phpMyAdmin
- [ ] `.env` con la configuración sensible fuera del código (`cat .env.example`)
