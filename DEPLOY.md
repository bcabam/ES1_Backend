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
- Una `t3.micro` tiene solo **1 GB de RAM**: sin la memoria swap del paso 3b, MySQL, Apache y Django juntos la agotan y la instancia deja de responder (también se corta el SSH).
- **Antes de la revisión presencial**, inicia el laboratorio con tiempo y comprueba que todo funcione.

> **Consejo para la instalación:** los cortes de SSH interrumpen comandos largos. Conéctate con `ServerAliveInterval` (paso 2) y ejecuta las instalaciones dentro de `tmux`: si se corta la conexión, al volver escribes `tmux attach` y sigues donde estabas.

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

Desde PowerShell (con la ruta completa del archivo, funciona desde cualquier carpeta):

```powershell
ssh -o ServerAliveInterval=30 -i C:\Users\TU_USUARIO\Downloads\labsuser.pem ubuntu@IP_PUBLICA
```

`ServerAliveInterval=30` evita que la conexión se corte por inactividad. La primera vez pregunta *"Are you sure…?"*: responder `yes`.

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
sudo apt install -y python3-venv python3-dev build-essential pkg-config apache2 git tmux
```

- `python3-dev`, `build-essential` y `pkg-config` son necesarios para compilar `mysqlclient`.
- `apache2` es el servidor web. MySQL se instala aparte en el paso 3c, porque Ubuntu trae una versión muy antigua.
- Si aparece una pantalla preguntando qué servicios reiniciar, basta con presionar Enter.

> Si `apt` muestra errores **`503 Service Unavailable`** desde `us-east-1.ec2.archive.ubuntu.com`, ese servidor de Ubuntu está caído. Cambia al servidor principal y repite:
> ```bash
> sudo sed -i 's|http://us-east-1.ec2.archive.ubuntu.com/ubuntu|http://archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources
> sudo apt update
> ```

## 3b. Agregar memoria swap (obligatorio en t3.micro)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

La fila **Swap** debe mostrar `2.0Gi`. La última línea de `/etc/fstab` la mantiene activa después de reiniciar.

## 3c. Instalar MySQL 8.4

**Django 6.1 exige MySQL 8.4 o superior**, y Ubuntu 24.04 trae la 8.0 (con ella, `migrate` falla con *"MySQL 8.4 or later is required"*). Se instala desde el repositorio oficial de MySQL:

```bash
cd ~
ARCHIVO=$(curl -s https://repo.mysql.com/ | grep -o 'mysql-apt-config_[^"<]*_all\.deb' | sort -V | tail -1); echo $ARCHIVO
wget https://repo.mysql.com/$ARCHIVO
sudo dpkg -i $ARCHIVO
```

En la pantalla de configuración: Enter sobre **MySQL Server & Cluster** → elegir **`mysql-8.4-lts`** → bajar a **Ok** → Enter. Si no aparece la pantalla, ejecutar `sudo dpkg-reconfigure mysql-apt-config`.

Comprobar que quedó elegida la 8.4 (debe decir `mysql-8.4-lts`) e instalar:

```bash
grep -h "repo.mysql.com" /etc/apt/sources.list.d/*.list
sudo apt update
sudo apt install -y mysql-server libmysqlclient-dev
mysql --version
```

Si pide contraseña de root, dejarla **vacía** (root entra con `sudo mysql`). La versión debe ser **8.4.x**.

Reducir la memoria que usa MySQL (desactiva estadísticas internas que no se usan, unos 200 MB):

```bash
printf '[mysqld]\nperformance_schema = OFF\n' | sudo tee /etc/mysql/mysql.conf.d/bajo-consumo.cnf
sudo systemctl restart mysql
```

## 4. Crear la base de datos

```bash
sudo mysql
```

Dentro de MySQL (cambiar `ClaveSegura` por una contraseña propia).

> Al pegar varias líneas, cada salto de línea se ejecuta como Enter. **Edita la contraseña primero en el Bloc de notas** y pega el texto ya listo.

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

Conectar phpMyAdmin con Apache (necesario si no quedó marcado `apache2`, y no hace daño repetirlo):

```bash
sudo apt install -y libapache2-mod-php php-mysql
sudo ln -sf /etc/phpmyadmin/apache.conf /etc/apache2/conf-available/phpmyadmin.conf
sudo a2enconf phpmyadmin
sudo systemctl reload apache2
```

Queda disponible en `http://IP_PUBLICA/phpmyadmin`. Se ingresa con el usuario **`colegio`** y la contraseña del paso 4 (**no** con `root`: en el servidor, root solo entra desde la terminal con `sudo mysql`).

## 6. Clonar el proyecto desde GitHub

```bash
cd /home/ubuntu
git clone https://github.com/bcabam/ES1_Backend.git
cd ES1_Backend
git log --oneline -5
```

Desde aquí, todos los comandos se ejecutan **dentro de `~/ES1_Backend`**. Si te reconectas, lo primero es siempre:

```bash
cd ~/ES1_Backend
source venv/bin/activate
```

## 7. Entorno virtual y dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 8. Crear el archivo `.env`

**El archivo debe quedar dentro de `~/ES1_Backend`**, no en la carpeta personal (Django lo busca junto a `manage.py`).

```bash
cd ~/ES1_Backend
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
sudo sed -i 's/MaxRequestWorkers.*/MaxRequestWorkers 20/' /etc/apache2/mods-available/mpm_prefork.conf
sudo systemctl restart apache2
```

- `chmod 755 /home/ubuntu` permite que Apache lea los archivos estáticos y subidos.
- `MaxRequestWorkers 20` limita cuántos procesos abre Apache (por defecto hasta 150), para no agotar la memoria.

## 12. Probar

> Escribe siempre **`http://`**. Si el navegador lo cambia solo a `https://`, la página no carga (el servidor no tiene certificado). En Chrome, desactiva *Configuración → Privacidad y seguridad → Seguridad → "Usar siempre conexiones seguras"*.

- Sitio: `http://IP_PUBLICA/login/` (usuarios `admin`, `administrativo`, `docente`, `estudiante` — clave `Colegio2026!`; también se puede entrar con el correo, por ejemplo `docente@colegiodigital.cl`)
- Django Admin: `http://IP_PUBLICA/admin/`
- phpMyAdmin: `http://IP_PUBLICA/phpmyadmin`

> Las fotos y PDF subidos en los equipos locales **no** están en el servidor: hay que volver a subirlos desde el sitio o el admin para la demostración.

---

## Cada vez que se inicia el laboratorio

1. **Start Lab** → AWS → EC2. Si la instancia está detenida: **Instance state → Start instance**.
2. Copiar la **nueva IP pública**.
3. Abrir `http://NUEVA_IP/login/`. El servicio ya actualizó la IP en el `.env` al arrancar. No hace falta conectarse por SSH para usar el sitio.

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
sudo cp deploy/colegio.service /etc/systemd/system/colegio.service
sudo systemctl daemon-reload
sudo systemctl restart colegio
```

Las líneas de `colegio.service` aplican los cambios que haya tenido la configuración del servicio; si no cambió, no hacen daño.

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
| `MySQL 8.4 or later is required (found 8.0…)` | Se instaló la MySQL de Ubuntu | Seguir el paso 3c y luego `pip install --force-reinstall --no-cache-dir mysqlclient==2.3.0` |
| `503 Service Unavailable` al usar `apt` | Servidor de Ubuntu de la región caído | Cambiar a `archive.ubuntu.com` (nota del paso 3) |
| `dpkg frontend lock was locked by another process` | Otra instalación quedó abierta en otra ventana | Terminarla en esa ventana; si quedó colgada: `sudo kill PID` y `sudo dpkg --configure -a` |
| El SSH se corta seguido / la instancia deja de responder | Falta de memoria (`killed by the OOM killer`) | Paso 3b (swap) y `performance_schema = OFF` (paso 3c) |
| `ERR_CONNECTION_RESET` en el navegador del PC, pero funciona en el celular | El navegador cambió la dirección a `https://` | Escribir `http://` y desactivar "Usar siempre conexiones seguras" |
| `Identity file labsuser.pem not accessible` | PowerShell no está en la carpeta del `.pem` | Usar la ruta completa del archivo en `ssh -i` |
| `Permission denied (publickey)` | Llave equivocada | Descargar de nuevo el PEM (AWS Details → Download PEM) |
| phpMyAdmin da `404 Not Found` | phpMyAdmin no quedó conectado a Apache | Comandos `a2enconf phpmyadmin` del paso 5 |

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
