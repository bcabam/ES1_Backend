# API REST de Colegio Digital

Guía para usar la API y para **agregar endpoints nuevos** siguiendo el mismo patrón que la API de funcionarios (`AdministrativosApp`).

---

## 1. Cómo se usa

| Qué | Dirección |
|---|---|
| Swagger (documentación y pruebas) | `/api/docs/` |
| Esquema OpenAPI | `/api/schema/` |
| Obtener tokens | `POST /api/token/` con `{"username": "...", "password": "..."}` (acepta usuario o correo) |
| Renovar el access | `POST /api/token/refresh/` con `{"refresh": "..."}` |
| Mi perfil (prueba de token) | `GET /api/perfil/` |
| Funcionarios | `/api/administrativos/` |

Cada petición protegida lleva el encabezado:

```
Authorization: Bearer <access token>
```

En Swagger: obtén el token en `POST /api/token/`, presiona **Authorize** y pega solo el `access`.

- **Access token:** dura 15 minutos.
- **Refresh token:** dura 1 día. Al usarlo entrega uno nuevo y el anterior queda invalidado.
- **Login de la API:** máximo 10 intentos por minuto (después responde 429).

### Formato de los errores

Todos los errores responden JSON con la misma forma:

```json
{"error": "El perfil docente no tiene permiso para eliminar este recurso.", "codigo": 403}
```

Los errores de validación agregan `detalle` con los campos que fallaron:

```json
{"error": "Los datos enviados no son válidos.", "codigo": 400, "detalle": {"telefono": ["Teléfono no válido: ..."]}}
```

| Código | Cuándo |
|---|---|
| 200 | Consulta, modificación o eliminación correcta |
| 201 | Registro creado |
| 400 | Datos inválidos |
| 401 | Sin token, token vencido o inválido |
| 403 | El perfil no tiene permiso |
| 404 | El registro no existe |
| 405 | Método no permitido |
| 429 | Demasiados intentos |
| 500 | Error interno (sin detalles del servidor) |

---

## 2. Piezas de seguridad compartidas (`config/api.py`)

| Pieza | Para qué |
|---|---|
| `PermisoPorPerfil` | Decide quién puede leer, escribir y eliminar según su perfil (el administrador siempre puede todo) |
| `OcultaCamposSensiblesMixin` | Quita los campos sensibles de las respuestas si quien consulta no es administrador |
| `respuestas_error(400, 401, …)` | Documenta en Swagger las respuestas de error |
| `validar_tamano_archivo(archivo, maximo_mb)` | Rechaza archivos demasiado grandes |

**No modifiques `config/api.py` ni `config/urls.py`**: cada app tiene sus propios archivos de API.

---

## 3. Agregar un endpoint en 5 pasos

Ejemplo con **Docente** (en `DocentesApp`). Para Estudiante o Nota es igual, en su propia app.

### Paso 1: `serializers.py`

```python
from rest_framework import serializers

from config.api import OcultaCamposSensiblesMixin
from .models import Docente


class DocenteSerializer(OcultaCamposSensiblesMixin, serializers.ModelSerializer):
    class Meta:
        model = Docente
        fields = ['id', 'nombre', 'rut', 'cuenta']
        # Solo el administrador recibe estos campos en las respuestas.
        campos_sensibles = ['rut', 'cuenta']

    # Validaciones: un método validate_<campo> por cada regla.
    def validate_nombre(self, valor):
        valor = valor.strip()
        if len(valor) < 3:
            raise serializers.ValidationError('El nombre debe tener al menos 3 caracteres.')
        return valor
```

### Paso 2: `api.py` (el ViewSet)

```python
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from config.api import PermisoPorPerfil, respuestas_error
from .models import Docente
from .serializers import DocenteSerializer


@extend_schema_view(
    list=extend_schema(summary='Listar docentes', responses={200: DocenteSerializer(many=True), **respuestas_error(401, 403)}),
    retrieve=extend_schema(summary='Ver un docente', responses={200: DocenteSerializer, **respuestas_error(401, 403, 404)}),
    create=extend_schema(summary='Registrar un docente', responses={201: DocenteSerializer, **respuestas_error(400, 401, 403)}),
    update=extend_schema(summary='Modificar un docente', responses={200: DocenteSerializer, **respuestas_error(400, 401, 403, 404)}),
    destroy=extend_schema(summary='Eliminar un docente', responses=respuestas_error(401, 403, 404)),
)
@extend_schema(tags=['Docentes'])
class DocenteViewSet(viewsets.ModelViewSet):
    queryset = Docente.objects.all()
    serializer_class = DocenteSerializer
    permission_classes = [PermisoPorPerfil]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    # Quién puede hacer qué (el administrador siempre puede todo).
    perfiles_lectura = ['administrativo', 'docente']
    perfiles_escritura = ['administrativo']
    perfiles_eliminacion = []

    # Buscar solo por campos públicos.
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']

    def destroy(self, request, *args, **kwargs):
        docente = self.get_object()
        nombre = str(docente)
        docente.delete()
        return Response({'mensaje': f'Docente "{nombre}" eliminado correctamente.'}, status=status.HTTP_200_OK)
```

### Paso 3: registrar la ruta en `api_urls.py` de tu app

```python
from .api import DocenteViewSet

router.register('docentes', DocenteViewSet, basename='api-docentes')
```

Con eso quedan `/api/docentes/` y `/api/docentes/{id}/`, y aparecen solos en Swagger.

### Paso 4: tests en `test_api.py` de tu app

Copia la estructura de `AdministrativosApp/test_api.py`. Como mínimo, prueba:

- sin token → 401
- el administrador ve los campos sensibles y los demás perfiles no
- un perfil sin permiso → 403 (crear y eliminar)
- crear → 201, modificar → 200, eliminar → 200
- datos inválidos → 400 con `detalle`
- registro inexistente → 404

```bash
python manage.py test
```

### Paso 5: probar en Swagger y sacar capturas

1. `python manage.py runserver` → `http://127.0.0.1:8000/api/docs/`
2. Token como `admin` → Authorize → probar cada operación.
3. Token como otro perfil → mostrar que no ve los campos sensibles y que recibe 403 donde corresponde.
4. Guardar las capturas para el informe.

---

## 4. Reglas propuestas por recurso

Para que la API sea consistente con la aplicación web:

| Recurso | Lectura | Escritura (POST/PUT) | Eliminación | Campos sensibles |
|---|---|---|---|---|
| Funcionarios ✅ | todos | administrativo | solo administrador | correo, teléfono, fecha de contratación, contrato, cuenta |
| Docentes | administrativo, docente | administrativo | solo administrador | RUT, cuenta (correo), usuario |
| Estudiantes | administrativo, docente | administrativo | solo administrador | RUT, cuenta (correo), ficha de matrícula, usuario |
| Notas | administrativo, docente, estudiante | docente | docente (solo sus notas) | — |

### Notas: cada uno ve solo lo suyo

La transacción necesita además filtrar **qué registros** ve cada perfil. Se hace sobrescribiendo `get_queryset` en el ViewSet:

```python
from config.autorizacion import perfil_de

def get_queryset(self):
    notas = Nota.objects.select_related('estudiante', 'docente')
    perfil = perfil_de(self.request.user)
    if perfil == 'estudiante':
        return notas.filter(estudiante__usuario=self.request.user)   # solo sus notas
    if perfil == 'docente':
        return notas.filter(docente__usuario=self.request.user)      # solo las que registró
    return notas                                                     # administrativo y administrador: todas
```

Y al crear, el docente se toma del token, no de lo que envía el cliente:

```python
def perform_create(self, serializer):
    serializer.save(docente=self.request.user.docente)
```

(en el serializer, `docente` va como `read_only_fields`).

---

## 5. Reglas de trabajo

- Cada uno trabaja en **su rama** y solo en **su app**.
- Antes de empezar: `git pull origin main`.
- Antes de subir: `python manage.py test` (todo debe pasar).
- Todo entra a `main` por **Pull Request**.
- Las librerías nuevas se instalan con `pip install -r requirements.txt` (DRF, SimpleJWT y drf-spectacular ya están incluidas).
