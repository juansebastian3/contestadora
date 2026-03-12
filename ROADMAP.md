# FiltroLlamadas - Roadmap hacia App Store

## Estado actual: ~60% del MVP

### Lo que ya funciona (backend)

- Twilio contesta llamadas con voz IA (Polly)
- Conversación multi-turno con OpenAI (historial completo)
- Análisis post-llamada: Categoría, Prioridad, Resumen (JSON)
- Notificación WhatsApp estructurada al finalizar
- Base de datos SQLite con modelos de Usuario, Llamada, Voz, Plan
- Lógica de filtrado: modo desconocidos vs modo luna
- Servicio TTS dual: Polly (gratis) + ElevenLabs (premium) con cache
- API REST completa: dashboard, historial, voces, planes, perfil
- Catálogo de 8 voces (5 Polly + 3 ElevenLabs) con seed automático
- 3 planes definidos: Gratis / Pro $4.99 / Premium $12.99

### Lo que ya funciona (mobile)

- App React Native/Expo con 4 pantallas
- Dashboard con stats, distribución y últimas llamadas
- Historial con filtros por categoría y prioridad + modal detalle
- Pantalla de voces con selector visual y badges de plan
- Configuración con toggles y secciones
- Tema dark mode premium
- Datos demo para funcionar sin backend

---

## Qué falta para publicar

### Semana 1-2: Funcionalidad core

- [ ] **Autenticación**: JWT tokens para la API (login/registro)
- [ ] **Registro de usuario**: Pantalla de onboarding en la app
- [ ] **Conectar app al backend**: Reemplazar `TU_DOMINIO` con URL real
- [ ] **Persistir settings**: Los toggles de la app deben llamar a la API
- [ ] **Desplegar backend**: Railway / Render / DigitalOcean con dominio
- [ ] **Migrar DB**: De SQLite a PostgreSQL para producción
- [ ] **Comprar número Twilio**: Número chileno real (+56) por ~$1/mes

### Semana 3: Pagos

- [ ] **Stripe integration**: Suscripciones mensuales/anuales
- [ ] **In-App Purchase**: RevenueCat para iOS/Android
- [ ] **Paywall**: Pantalla de upgrade cuando intentan usar feature premium
- [ ] **Webhook Stripe**: Actualizar plan del usuario automáticamente

### Semana 4: Pulir para App Store

- [ ] **App Icon**: Diseño profesional 1024x1024
- [ ] **Splash Screen**: Con animación de carga
- [ ] **Screenshots**: 6.5" y 5.5" para la ficha de App Store
- [ ] **TestFlight**: Build de prueba para iOS
- [ ] **Privacy Policy**: Página web con política de privacidad
- [ ] **Terms of Service**: Términos de uso
- [ ] **App Store description**: Texto optimizado para ASO

### Semana 5: Testing y seguridad

- [ ] **Tests unitarios**: Servicios de LLM, filtrado, TTS
- [ ] **Tests de integración**: Webhooks de Twilio end-to-end
- [ ] **Rate limiting**: Proteger API de abuso
- [ ] **Validación de webhooks Twilio**: Verificar firma
- [ ] **Encriptar .env**: No commitear API keys
- [ ] **Monitoring**: Sentry para errores, logs en producción

### Semana 6: Lanzamiento

- [ ] **Apple Developer Account**: $99/año
- [ ] **Google Play Developer**: $25 una vez
- [ ] **Submit a App Store Review**
- [ ] **Submit a Google Play**
- [ ] **Landing page**: Página web de marketing

---

## Arquitectura de producción

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐
│  App Móvil  │────▶│  FastAPI      │────▶│ PostgreSQL│
│  (Expo)     │◀────│  (Railway)    │◀────│ (Supabase)│
└─────────────┘     └──────┬───────┘     └──────────┘
                           │
                    ┌──────▼───────┐
                    │   Twilio     │
                    │ Voice + WA   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼──┐  ┌─────▼──┐  ┌─────▼────┐
        │ OpenAI │  │Eleven  │  │ Stripe   │
        │ (LLM)  │  │Labs    │  │ (Pagos)  │
        └────────┘  │(TTS)   │  └──────────┘
                    └────────┘
```

## Costos estimados mensuales (con 100 usuarios)

| Servicio | Costo |
|----------|-------|
| Twilio número chileno | $1/mes |
| Twilio Voice (minutos) | ~$50/mes |
| Twilio WhatsApp | ~$15/mes |
| OpenAI API | ~$30/mes |
| ElevenLabs (Pro users) | ~$22/mes |
| Railway (hosting) | $5/mes |
| Supabase (DB) | $0 (free tier) |
| Apple Developer | $8.25/mes |
| **Total** | **~$131/mes** |

Con 100 usuarios: 20 Pro ($4.99) + 5 Premium ($12.99) = **$164.75 revenue**

Breakeven: ~80 usuarios pagos.
