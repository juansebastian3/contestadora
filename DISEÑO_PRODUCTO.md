# FiltroLlamadas — Diseño de Producto

## Cómo funciona el desvío de llamadas

El usuario configura en su celular el **desvío de llamadas cuando no contesta** hacia su número Twilio.

- iPhone: Ajustes > Teléfono > Desvío de llamadas, o código del operador `*61*+1XXXXXXXXXX#`
- Android: Teléfono > Ajustes > Desvío de llamadas > Cuando no contesto

**Flujo real:**
1. Alguien llama al usuario
2. El usuario ve quién llama en su pantalla
3. Si no quiere/puede contestar → no contesta o rechaza
4. La llamada se desvía automáticamente al número Twilio
5. Twilio ejecuta el webhook → la IA contesta como contestadora
6. El usuario recibe un WhatsApp con el resumen del recado

**Modos de activación:**
- **Manual**: El usuario simplemente no contesta (siempre funciona)
- **Luna**: Desvío automático activo en horario nocturno/reuniones
- **Calendario**: Desvío automático cuando el usuario tiene un evento en Google Calendar u Outlook

---

## Mapa de Empatía

### El Usuario (dueño del número)

**¿Qué piensa y siente?**
- "Estoy harto de contestar llamadas de desconocidos que interrumpen mi día"
- "No quiero perderme una llamada importante por estar ocupado"
- "Quiero que si alguien llama, al menos pueda dejar un recado y yo decidir si devolver"
- "El buzón de voz del operador es genérico y nadie deja mensajes ahí"

**¿Qué ve?**
- Llamadas perdidas de números que no conoce
- Interrupciones constantes durante reuniones o tiempo personal
- Su calendario lleno de reuniones donde no puede contestar

**¿Qué escucha?**
- "¿Por qué no me contestaste?" de gente que necesitaba algo urgente
- "Te llamé y nadie contestó" — porque el buzón genérico no genera confianza

**¿Qué dice y hace?**
- Rechaza llamadas de desconocidos
- Revisa llamadas perdidas pero no devuelve porque no sabe qué querían
- Configura "no molestar" en horarios puntuales

**Dolor principal:** Perder información valiosa de llamadas que no contesta. No saber si era importante o spam.

**Ganancia principal:** Recibir un resumen inteligente de cada llamada con quién llamó, para qué, y qué tan urgente era — sin tener que contestar.

### El Llamante (quien llama al usuario)

**¿Qué piensa y siente?**
- "Necesito hablar con esta persona pero no contesta"
- "El buzón de voz es impersonal y no sé si me van a devolver la llamada"
- "No me gusta hablar con robots que suenan artificiales"

**¿Qué ve?**
- El teléfono suena y suena, luego salta al buzón genérico
- O peor: un robot con voz de lata que dice "deje su mensaje después del tono"

**¿Qué escucha?**
- Con buzón normal: "El número al que usted marcó no está disponible..." (genérico, frío)
- Con FiltroLlamadas + audio grabado: La voz REAL del dueño diciendo su propio mensaje personalizado

**¿Qué dice y hace?**
- Con buzón normal: Cuelga sin dejar mensaje el 70% de las veces
- Con FiltroLlamadas: Escucha la grabación personal, siente que la persona es real, deja su recado

**Dolor principal:** No saber si el mensaje llega. Sentir que habla con una máquina.

**Ganancia principal:** Escuchar la voz real de la persona, sentir que su mensaje será recibido y resumido de manera inteligente.

---

## ¿Por qué la grabación personal cambia todo?

La diferencia clave entre un buzón de voz del operador y FiltroLlamadas es la **grabación personal**:

| Aspecto | Buzón del operador | FiltroLlamadas |
|---------|-------------------|----------------|
| Saludo | "El número no está disponible" | Tu propia voz: "Hola, soy Juan, no puedo atender..." |
| Confianza del llamante | Baja — ¿me van a devolver? | Alta — suena personal, no corporativo |
| Tasa de recados dejados | ~30% | ~80% (estimado por voz personalizada) |
| Qué recibe el dueño | Notificación de buzón de voz | WhatsApp con resumen IA: quién, para qué, urgencia |
| Acción del dueño | Escuchar audio largo del buzón | Leer 2 líneas en WhatsApp y decidir si devolver |

---

## Integración con Calendarios

### Lógica de activación automática

El usuario conecta su Google Calendar y/o Outlook Calendar. El sistema revisa periódicamente:

1. **¿Tiene evento ahora?** → Activar modo contestadora automáticamente
2. **¿Evento terminó?** → Desactivar modo contestadora
3. **Eventos "privados" o "ocupado"** → Activar siempre
4. **Eventos "libre" o "tentativo"** → No activar (el usuario puede contestar)

### Calendarios soportados (Pro+)
- Google Calendar (OAuth2 con scope calendar.readonly)
- Microsoft Outlook/365 (OAuth2 con scope Calendars.Read)

### Modos combinados
- **Solo calendario**: Desvía solo cuando hay evento
- **Calendario + Luna**: Desvía en eventos Y en horario nocturno
- **Luna manual**: Desvía siempre (usuario lo activa/desactiva manualmente)
