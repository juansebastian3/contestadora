/**
 * LegalScreen - Terminos de Servicio y Politica de Privacidad
 * Muestra documentos legales en formato scrolleable.
 * Se accede desde ConfigScreen y desde RegistroScreen.
 */
import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";

// ─── Contenido legal ──────────────────────────────────────
const TERMINOS = {
  titulo: "Terminos de Servicio",
  ultimaActualizacion: "12 de marzo de 2026",
  secciones: [
    {
      titulo: "1. Aceptacion de los terminos",
      contenido:
        "Al crear una cuenta y utilizar ContestaDora, aceptas estos Terminos de Servicio en su totalidad. Si no estas de acuerdo con alguna parte, no debes usar el servicio. Nos reservamos el derecho de modificar estos terminos con previo aviso de 30 dias.",
    },
    {
      titulo: "2. Descripcion del servicio",
      contenido:
        "ContestaDora es un servicio de asistencia telefonica basado en inteligencia artificial que filtra, contesta y transcribe llamadas en tu nombre. El servicio incluye: recepcion de llamadas desviadas, transcripcion automatica, resumen por WhatsApp, y gestion de agenda segun tu plan contratado.",
    },
    {
      titulo: "3. Planes y pagos",
      contenido:
        "Ofrecemos planes Gratis, Pro ($4.99/mes) y Premium ($9.99/mes). Los pagos se procesan a traves de MercadoPago. Puedes cancelar tu suscripcion en cualquier momento. Al cancelar, mantendras acceso hasta el final del periodo facturado. No ofrecemos reembolsos parciales por periodos no utilizados.",
    },
    {
      titulo: "4. Uso del numero telefonico",
      contenido:
        "Al suscribirte a un plan de pago, se te asigna un numero de telefono virtual. Este numero es propiedad de ContestaDora y se te presta mientras mantengas tu suscripcion activa. Si cancelas, el numero puede ser reasignado despues de 30 dias de inactividad.",
    },
    {
      titulo: "5. Grabacion y transcripcion de llamadas",
      contenido:
        "Al utilizar el servicio, las llamadas recibidas por tu asistente seran procesadas por inteligencia artificial para generar transcripciones y resumenes. Es tu responsabilidad informar a terceros que las llamadas pueden ser grabadas y transcritas, segun la legislacion aplicable en tu jurisdiccion.",
    },
    {
      titulo: "6. Conducta del usuario",
      contenido:
        "Te comprometes a no usar el servicio para actividades ilegales, fraudulentas, acoso, spam, o cualquier proposito que viole los derechos de terceros. Nos reservamos el derecho de suspender cuentas que incumplan estas condiciones.",
    },
    {
      titulo: "7. Disponibilidad del servicio",
      contenido:
        "Nos esforzamos por mantener el servicio disponible 24/7, pero no garantizamos disponibilidad ininterrumpida. Pueden ocurrir interrupciones por mantenimiento, actualizaciones o circunstancias fuera de nuestro control. No somos responsables por llamadas perdidas durante periodos de inactividad.",
    },
    {
      titulo: "8. Limitacion de responsabilidad",
      contenido:
        "ContestaDora se ofrece \"tal cual\". No garantizamos la exactitud de las transcripciones ni la precision de la clasificacion por IA. El servicio no sustituye la atencion humana directa. No somos responsables por danos indirectos derivados del uso del servicio.",
    },
    {
      titulo: "9. Cancelacion",
      contenido:
        "Puedes cancelar tu cuenta en cualquier momento desde la aplicacion. Al cancelar: tus datos se conservan por 90 dias por si deseas reactivar la cuenta, transcurrido ese plazo se eliminan permanentemente. El desvio de llamadas debe ser desactivado manualmente desde tu telefono usando el codigo ##002#.",
    },
    {
      titulo: "10. Contacto",
      contenido:
        "Para consultas sobre estos terminos, escribe a soporte@filtrollamadas.com. Intentaremos responder en un plazo de 48 horas habiles.",
    },
  ],
};

const PRIVACIDAD = {
  titulo: "Politica de Privacidad",
  ultimaActualizacion: "12 de marzo de 2026",
  secciones: [
    {
      titulo: "1. Informacion que recopilamos",
      contenido:
        "Recopilamos la informacion que proporcionas al registrarte (nombre, email, telefono), las grabaciones de audio de las llamadas que recibe tu asistente, las transcripciones generadas, y datos de uso basicos (frecuencia de uso, plan contratado). No recopilamos informacion financiera directamente; los pagos son procesados por MercadoPago.",
    },
    {
      titulo: "2. Como usamos tu informacion",
      contenido:
        "Usamos tu informacion para: operar el servicio de asistencia telefonica, generar transcripciones y resumenes de llamadas, enviar notificaciones por WhatsApp, mejorar la calidad de la IA, y comunicarte cambios en el servicio. No vendemos tu informacion personal a terceros bajo ninguna circunstancia.",
    },
    {
      titulo: "3. Almacenamiento y seguridad",
      contenido:
        "Tus datos se almacenan en servidores seguros con cifrado en transito (TLS) y en reposo. Los audios de llamadas se almacenan por un maximo de 90 dias y luego se eliminan automaticamente. Las transcripciones de texto se conservan mientras mantengas tu cuenta activa.",
    },
    {
      titulo: "4. Servicios de terceros",
      contenido:
        "Utilizamos los siguientes servicios de terceros: Twilio (telefonia), Amazon Polly (sintesis de voz), OpenAI (procesamiento de lenguaje), MercadoPago (pagos), y WhatsApp Business API (notificaciones). Cada uno de estos servicios opera bajo sus propias politicas de privacidad.",
    },
    {
      titulo: "5. Tus derechos",
      contenido:
        "Tienes derecho a: acceder a tu informacion personal, solicitar la correccion de datos inexactos, solicitar la eliminacion de tu cuenta y datos, exportar tus transcripciones, y revocar el consentimiento para el procesamiento de tus datos en cualquier momento.",
    },
    {
      titulo: "6. Consentimiento para grabacion",
      contenido:
        "Al usar ContestaDora, consientes que las llamadas dirigidas a tu asistente sean grabadas y procesadas. Es tu responsabilidad cumplir con las leyes locales de grabacion de llamadas, que pueden requerir consentimiento de todas las partes involucradas.",
    },
    {
      titulo: "7. Cookies y seguimiento",
      contenido:
        "La aplicacion movil no utiliza cookies. Recopilamos datos anonimos de uso para mejorar el servicio. No realizamos seguimiento publicitario ni compartimos datos de uso con redes publicitarias.",
    },
    {
      titulo: "8. Menores de edad",
      contenido:
        "ContestaDora no esta dirigido a menores de 18 anos. No recopilamos conscientemente informacion de menores. Si descubrimos que un menor ha creado una cuenta, la eliminaremos.",
    },
    {
      titulo: "9. Cambios en esta politica",
      contenido:
        "Podemos actualizar esta politica periodicamente. Te notificaremos de cambios significativos a traves de la aplicacion o por email con al menos 15 dias de anticipacion.",
    },
    {
      titulo: "10. Contacto",
      contenido:
        "Para ejercer tus derechos de privacidad o realizar consultas, escribe a privacidad@filtrollamadas.com.",
    },
  ],
};

export default function LegalScreen({ navigation, route }) {
  const initialTab = route?.params?.tab || "terminos";
  const [activeTab, setActiveTab] = useState(initialTab);

  const doc = activeTab === "terminos" ? TERMINOS : PRIVACIDAD;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Legal</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabsContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === "terminos" && styles.tabActive]}
          onPress={() => setActiveTab("terminos")}
        >
          <Text style={[styles.tabText, activeTab === "terminos" && styles.tabTextActive]}>
            Terminos
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === "privacidad" && styles.tabActive]}
          onPress={() => setActiveTab("privacidad")}
        >
          <Text style={[styles.tabText, activeTab === "privacidad" && styles.tabTextActive]}>
            Privacidad
          </Text>
        </TouchableOpacity>
      </View>

      {/* Contenido */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.docTitulo}>{doc.titulo}</Text>
        <Text style={styles.docFecha}>Ultima actualizacion: {doc.ultimaActualizacion}</Text>

        {doc.secciones.map((seccion, i) => (
          <View key={i} style={styles.seccion}>
            <Text style={styles.seccionTitulo}>{seccion.titulo}</Text>
            <Text style={styles.seccionContenido}>{seccion.contenido}</Text>
          </View>
        ))}

        <View style={styles.contactCard}>
          <Ionicons name="mail-outline" size={18} color={colors.primary} />
          <Text style={styles.contactText}>
            Dudas? Escribe a soporte@filtrollamadas.com
          </Text>
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },

  // Header
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingTop: spacing.xxl + 10,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    gap: spacing.md,
  },
  backBtn: {
    padding: 4,
  },
  headerTitle: {
    fontSize: fontSize.xl,
    fontWeight: "700",
    color: colors.textPrimary,
  },

  // Tabs
  tabsContainer: {
    flexDirection: "row",
    marginHorizontal: spacing.lg,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: 4,
    marginBottom: spacing.md,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    borderRadius: borderRadius.sm,
  },
  tabActive: {
    backgroundColor: colors.primary,
  },
  tabText: {
    color: colors.textMuted,
    fontSize: fontSize.md,
    fontWeight: "600",
  },
  tabTextActive: {
    color: "#fff",
  },

  // Contenido
  content: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  docTitulo: {
    fontSize: fontSize.xl,
    fontWeight: "800",
    color: colors.textPrimary,
    marginBottom: 4,
  },
  docFecha: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginBottom: spacing.lg,
  },

  seccion: {
    marginBottom: spacing.lg,
  },
  seccionTitulo: {
    fontSize: fontSize.md,
    fontWeight: "700",
    color: colors.textPrimary,
    marginBottom: 6,
  },
  seccionContenido: {
    fontSize: fontSize.sm,
    color: colors.textSecondary,
    lineHeight: 22,
  },

  contactCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  contactText: {
    color: colors.textSecondary,
    fontSize: fontSize.sm,
    flex: 1,
  },
});
