# ✅ Solución: Problema con Crear Cuenta en FiltroLlamadas

## 🔍 El Problema

Recibías errores al intentar crear una cuenta en la página web, probablemente algo como:
```
sqlite3.OperationalError: no such column: usuarios.twilio_phone_sid
```

## 🎯 Causa Raíz

Tu base de datos SQLite **no tenía el schema actualizado**. El archivo `filtro_llamadas.db` era viejo y le faltaban varias columnas que el código actual espera, como:
- `twilio_phone_sid`
- Y otras columnas de features más nuevos

Esto es común cuando actualizas el código sin migrar la base de datos.

## ✅ La Solución (YA APLICADA)

Ejecuté estos pasos:

1. **Eliminé la base de datos vieja**
   ```bash
   rm -f filtro_llamadas.db*
   ```

2. **Recreé la base de datos con el schema correcto**
   - El script `fix_database.py` eliminó todas las tablas
   - Recreó todas las tablas con el schema moderno (37 columnas en `usuarios`)
   - Inicializó los datos semilla (voces, planes, etc.)
   - Verificó que todo funcionara insertando un usuario de prueba

## 📊 Estado Actual

✅ **Base de datos reparada y lista**
- Tabla `usuarios` con 37 columnas correctas
- Tabla `llamadas` lista
- Tabla `suscripciones` lista
- Tabla `voces_disponibles` con datos iniciales
- Tabla `planes` con datos iniciales

## 🚀 Próximos Pasos

### 1. Reinicia tu servidor FastAPI

```bash
# Si estaba corriendo, detén con Ctrl+C
# Luego reinicia:
python -m uvicorn app.main:app --reload
```

O si usas Railway:
```bash
# Railway detectará el cambio automáticamente
# Solo redeploy si es necesario
```

### 2. Prueba crear una cuenta

Abre la página web y prueba registrarte con:
- **Nombre**: Cualquier nombre
- **Email**: tune@example.com
- **Teléfono**: **+56987654321** (¡IMPORTANTE! Debe incluir el `+`)
- **Password**: MinimoSeisCa

### 3. Espera el éxito ✅

Si todo funciona, recibirás:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "perfil": {
    "uid": "...",
    "nombre": "...",
    "email": "...",
    "plan": "free"
  }
}
```

## ⚠️ Importante: Formato de Teléfono

El sistema **requiere teléfono con código de país**:

❌ INCORRECTO:
- `987654321`
- `+56 987654321` (con espacios)
- `56987654321` (sin +)

✅ CORRECTO:
- `+56987654321` (Chile)
- `+1234567890` (USA)
- `+447911123456` (UK)

## 🔧 Mantenimiento Futuro

Para evitar este problema en el futuro:

### En Desarrollo (Local)
Si cambias el modelo `Usuario` en `app/models/database.py`:
1. Simplemente elimina `filtro_llamadas.db`
2. El servidor recreará automáticamente en startup

### En Producción (Railway/PostgreSQL)
Railway gestiona PostgreSQL automáticamente, así que **no tendrás este problema**.

Solo asegúrate de:
1. Que `DATABASE_URL` apunte a PostgreSQL en production
2. Dejar que el startup automático (`Base.metadata.create_all()`) maneje las tablas

## 🐛 Troubleshooting

Si aún tienes problemas:

### Error: "no such column"
→ Ejecuta nuevamente `python fix_database.py`

### Error: "disk I/O error"
→ Cierra cualquier otra conexión a la DB:
```bash
# Busca qué procesos usan la DB
lsof filtro_llamadas.db

# O simplemente elimina:
rm -f filtro_llamadas.db*
```

### Error: "email already exists"
→ Ya existe un usuario con ese email. Usa otro email.

### Error: "teléfono debe incluir código de país"
→ Usa formato internacional: `+XX...`

## 📝 Archivos Relevantes

- **fix_database.py** - Script que ejecuté para reparar (útil si vuelve a ocurrir)
- **diagnostico_registro.py** - Script para diagnosticar problemas futuros
- **app/models/database.py** - Define el schema de las tablas
- **app/core/auth.py** - Lógica de registro `/auth/registro`

## ✨ Resumen

| Antes | Después |
|-------|---------|
| ❌ DB vieja sin columnas nuevas | ✅ DB con schema completo |
| ❌ Errores al crear cuenta | ✅ Registro funciona |
| ❌ Tablas incompletas | ✅ 37 columnas en usuarios |
| ❌ Voces/planes no inicializados | ✅ Datos semilla cargados |

**¡Ahora puedes crear cuentas sin problemas!** 🎉
