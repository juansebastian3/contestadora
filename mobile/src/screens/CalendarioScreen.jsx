/**
 * CalendarioScreen - Integración con Google Calendar y Outlook (Pro/Premium)
 *
 * Permite al usuario:
 * - Conectar/desconectar Google Calendar
 * - Conectar/desconectar Outlook Calendar
 * - Ver si tiene un evento activo ahora
 * - Configurar el modo de calendario (solo reuniones / toda la agenda / manual)
 * - Activar/desactivar la auto-activación por calendario
 */
import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  ActivityIndicator,
  Linking,
  RefreshControl,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";
import api from "../services/api";

// ═══════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ═══════════════════════════════════════════════════════════

export default function CalendarioScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [perfil, setPerfil] = useState(null);
  const [calEstado, setCalEstado] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [perfilData, estadoData] = await Promise.all([
        api.getPerfil(),
        api.getCalendarioEstado().catch(() => null),
      ]);
      setPerfil(perfilData);
      setCalEstado(estadoData);
    } catch (e) {
      console.error("Error cargando datos calendario:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, []);

  const esPro = perfil?.plan === "pro" || perfil?.plan === "premium";

  // ─── Conectar Google Calendar ───────────────────────────
  async function handleConnectGoogle() {
    if (!esPro) {
      Alert.alert(
        "Plan Pro requerido",
        "La integración con calendarios está disponible en el plan Pro y Premium.",
        [{ text: "Entendido" }]
      );
      return;
    }

    setConnecting(true);
    try {
      // Obtener URL de autorización del backend
      const { auth_url } = await api.getGoogleAuthUrl();

      // Abrir en el navegador del dispositivo
      const supported = await Linking.canOpenURL(auth_url);
      if (supported) {
        await Linking.openURL(auth_url);
        // Mostrar instrucción al usuario
        Alert.alert(
          "Autorización en curso",
          "Se abrió tu navegador para conectar Google Calendar. Cuando termines, vuelve a la app y desliza hacia abajo para actualizar.",
          [{ text: "OK" }]
        );
      } else {
        Alert.alert("Error", "No se pudo abrir el navegador.");
      }
    } catch (e) {
      Alert.alert("Error", e.message || "No se pudo iniciar la conexión con Google.");
    } finally {
      setConnecting(false);
    }
  }

  // ─── Desconectar Google Calendar ─────────────────────────
  async function handleDisconnectGoogle() {
    Alert.alert(
      "Desconectar Google Calendar",
      "¿Seguro que quieres desconectar tu calendario de Google?",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Desconectar",
          style: "destructive",
          onPress: async () => {
            try {
              await api.desconectarGoogleCalendar();
              await loadData();
            } catch (e) {
              Alert.alert("Error", e.message);
            }
          },
        },
      ]
    );
  }

  // ─── Desconectar Outlook Calendar ────────────────────────
  async function handleDisconnectOutlook() {
    Alert.alert(
      "Desconectar Outlook Calendar",
      "¿Seguro que quieres desconectar tu calendario de Outlook?",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Desconectar",
          style: "destructive",
          onPress: async () => {
            try {
              await api.desconectarOutlookCalendar();
              await loadData();
            } catch (e) {
              Alert.alert("Error", e.message);
            }
          },
        },
      ]
    );
  }

  // ─── Cambiar auto-activar ────────────────────────────────
  async function toggleAutoActivar(value) {
    try {
      await api.configurarCalendario({ auto_activar: value });
      setCalEstado((prev) => ({ ...prev, auto_activar: value }));
    } catch (e) {
      Alert.alert("Error", e.message);
    }
  }

  // ─── Cambiar modo calendario ─────────────────────────────
  async function cambiarModo(modo) {
    try {
      await api.configurarCalendario({ modo });
      setCalEstado((prev) => ({ ...prev, modo_calendario: modo }));
    } catch (e) {
      Alert.alert("Error", e.message);
    }
  }

  // ═══════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const googleConectado = calEstado?.google_conectado;
  const outlookConectado = calEstado?.outlook_conectado;
  const eventoActual = calEstado?.evento_actual;
  const autoActivar = calEstado?.auto_activar ?? false;
  const modoCalendario = calEstado?.modo_calendario ?? "solo_reuniones";

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>Calendario</Text>
        <Text style={styles.subtitle}>
          Activa la contestadora automáticamente según tu agenda
        </Text>
      </View>

      {/* ═══ Banner Pro ═══ */}
      {!esPro && (
        <View style={styles.proBanner}>
          <Ionicons name="star" size={20} color={colors.accentYellow} />
          <View style={styles.proBannerText}>
            <Text style={styles.proBannerTitle}>Función Pro</Text>
            <Text style={styles.proBannerDesc}>
              Conecta tu calendario para que la contestadora se active sola en reuniones.
            </Text>
          </View>
        </View>
      )}

      {/* ═══ Evento activo ahora ═══ */}
      {eventoActual && (
        <View style={styles.eventoCard}>
          <View style={styles.eventoHeader}>
            <View style={styles.eventoDot} />
            <Text style={styles.eventoLabel}>EN REUNIÓN AHORA</Text>
          </View>
          <Text style={styles.eventoTitulo}>{eventoActual.titulo}</Text>
          <Text style={styles.eventoOrigen}>
            vía {eventoActual.origen === "google" ? "Google Calendar" : "Outlook"}
          </Text>
          <Text style={styles.eventoInfo}>
            La contestadora está activa automáticamente
          </Text>
        </View>
      )}

      {/* ═══ Calendarios conectados ═══ */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>CALENDARIOS</Text>

        {/* Google Calendar */}
        <View style={styles.calCard}>
          <View style={styles.calCardLeft}>
            <View style={[styles.calIcon, { backgroundColor: "#4285F420" }]}>
              <Ionicons name="logo-google" size={22} color="#4285F4" />
            </View>
            <View style={styles.calInfo}>
              <Text style={styles.calName}>Google Calendar</Text>
              <Text style={styles.calStatus}>
                {googleConectado ? "Conectado" : "No conectado"}
              </Text>
            </View>
          </View>
          {googleConectado ? (
            <TouchableOpacity
              style={styles.disconnectBtn}
              onPress={handleDisconnectGoogle}
            >
              <Text style={styles.disconnectText}>Desconectar</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.connectBtn, !esPro && styles.connectBtnDisabled]}
              onPress={handleConnectGoogle}
              disabled={connecting}
            >
              {connecting ? (
                <ActivityIndicator size="small" color="#FFF" />
              ) : (
                <Text style={styles.connectText}>Conectar</Text>
              )}
            </TouchableOpacity>
          )}
        </View>

        {/* Outlook Calendar */}
        <View style={styles.calCard}>
          <View style={styles.calCardLeft}>
            <View style={[styles.calIcon, { backgroundColor: "#0078D420" }]}>
              <Ionicons name="mail" size={22} color="#0078D4" />
            </View>
            <View style={styles.calInfo}>
              <Text style={styles.calName}>Outlook / Office 365</Text>
              <Text style={styles.calStatus}>
                {outlookConectado ? "Conectado" : "Próximamente"}
              </Text>
            </View>
          </View>
          {outlookConectado ? (
            <TouchableOpacity
              style={styles.disconnectBtn}
              onPress={handleDisconnectOutlook}
            >
              <Text style={styles.disconnectText}>Desconectar</Text>
            </TouchableOpacity>
          ) : (
            <View style={[styles.connectBtn, styles.connectBtnDisabled]}>
              <Text style={[styles.connectText, { opacity: 0.5 }]}>Pronto</Text>
            </View>
          )}
        </View>
      </View>

      {/* ═══ Configuración ═══ */}
      {(googleConectado || outlookConectado) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>CONFIGURACIÓN</Text>
          <View style={styles.configCard}>
            {/* Auto-activar */}
            <View style={styles.configRow}>
              <View style={styles.configLeft}>
                <Ionicons name="flash" size={20} color={colors.accentYellow} />
                <View style={styles.configInfo}>
                  <Text style={styles.configLabel}>Auto-activar</Text>
                  <Text style={styles.configDesc}>
                    Activa la contestadora cuando tengas un evento
                  </Text>
                </View>
              </View>
              <Switch
                value={autoActivar}
                onValueChange={toggleAutoActivar}
                trackColor={{ false: colors.bgCardLight, true: colors.primary + "80" }}
                thumbColor={autoActivar ? colors.primary : colors.textMuted}
              />
            </View>

            {/* Separador */}
            <View style={styles.separator} />

            {/* Modo: solo reuniones */}
            <Text style={styles.modoTitle}>¿Cuándo activar?</Text>

            <TouchableOpacity
              style={[
                styles.modoOption,
                modoCalendario === "solo_reuniones" && styles.modoOptionActive,
              ]}
              onPress={() => cambiarModo("solo_reuniones")}
            >
              <View style={styles.modoRadio}>
                {modoCalendario === "solo_reuniones" && <View style={styles.modoRadioInner} />}
              </View>
              <View style={styles.modoInfo}>
                <Text style={styles.modoLabel}>Solo en reuniones</Text>
                <Text style={styles.modoDesc}>
                  Se activa solo cuando tienes una reunión (no eventos de todo el día)
                </Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.modoOption,
                modoCalendario === "siempre_agenda" && styles.modoOptionActive,
              ]}
              onPress={() => cambiarModo("siempre_agenda")}
            >
              <View style={styles.modoRadio}>
                {modoCalendario === "siempre_agenda" && <View style={styles.modoRadioInner} />}
              </View>
              <View style={styles.modoInfo}>
                <Text style={styles.modoLabel}>Cualquier evento</Text>
                <Text style={styles.modoDesc}>
                  Se activa con cualquier evento, incluidos los de todo el día
                </Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.modoOption,
                modoCalendario === "manual" && styles.modoOptionActive,
              ]}
              onPress={() => cambiarModo("manual")}
            >
              <View style={styles.modoRadio}>
                {modoCalendario === "manual" && <View style={styles.modoRadioInner} />}
              </View>
              <View style={styles.modoInfo}>
                <Text style={styles.modoLabel}>Manual</Text>
                <Text style={styles.modoDesc}>
                  No auto-activar. Tú decides cuándo encender la contestadora
                </Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* ═══ Cómo funciona ═══ */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>CÓMO FUNCIONA</Text>
        <View style={styles.howCard}>
          <HowStep
            number="1"
            icon="calendar"
            title="Conecta tu calendario"
            desc="Autoriza acceso de solo lectura a tu Google Calendar o Outlook"
          />
          <HowStep
            number="2"
            icon="call"
            title="Recibes una llamada"
            desc="El sistema revisa si estás en una reunión en ese momento"
          />
          <HowStep
            number="3"
            icon="chatbubbles"
            title="La IA contesta por ti"
            desc="'Juan está en una reunión, deja tu mensaje y te lo paso'"
          />
          <HowStep
            number="4"
            icon="logo-whatsapp"
            title="Recibes el resumen"
            desc="Te llega un WhatsApp con quién llamó y para qué"
            isLast
          />
        </View>
      </View>

      <View style={{ height: 120 }} />
    </ScrollView>
  );
}

// ═══════════════════════════════════════════════════════════
// COMPONENTE: Paso del "cómo funciona"
// ═══════════════════════════════════════════════════════════

function HowStep({ number, icon, title, desc, isLast }) {
  return (
    <View style={styles.howStep}>
      <View style={styles.howStepLeft}>
        <View style={styles.howStepNumber}>
          <Text style={styles.howStepNumberText}>{number}</Text>
        </View>
        {!isLast && <View style={styles.howStepLine} />}
      </View>
      <View style={styles.howStepContent}>
        <View style={styles.howStepIcon}>
          <Ionicons name={icon} size={18} color={colors.primary} />
        </View>
        <View style={styles.howStepText}>
          <Text style={styles.howStepTitle}>{title}</Text>
          <Text style={styles.howStepDesc}>{desc}</Text>
        </View>
      </View>
    </View>
  );
}

// ═══════════════════════════════════════════════════════════
// ESTILOS
// ═══════════════════════════════════════════════════════════

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  loadingContainer: {
    flex: 1, backgroundColor: colors.bg,
    justifyContent: "center", alignItems: "center",
  },

  header: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl + 20,
    paddingBottom: spacing.md,
  },
  title: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  subtitle: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: 4 },

  // Pro banner
  proBanner: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: colors.accentYellow + "15",
    marginHorizontal: spacing.lg, borderRadius: borderRadius.lg,
    padding: spacing.md, marginBottom: spacing.md,
    borderWidth: 1, borderColor: colors.accentYellow + "30",
  },
  proBannerText: { marginLeft: spacing.sm, flex: 1 },
  proBannerTitle: { fontSize: fontSize.md, fontWeight: "700", color: colors.accentYellow },
  proBannerDesc: { fontSize: fontSize.xs, color: colors.textSecondary, marginTop: 2 },

  // Evento activo
  eventoCard: {
    backgroundColor: colors.accentGreen + "12",
    marginHorizontal: spacing.lg, borderRadius: borderRadius.lg,
    padding: spacing.md, marginBottom: spacing.md,
    borderWidth: 1, borderColor: colors.accentGreen + "30",
  },
  eventoHeader: { flexDirection: "row", alignItems: "center", marginBottom: 6 },
  eventoDot: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: colors.accentGreen, marginRight: 6,
  },
  eventoLabel: {
    fontSize: fontSize.xs, fontWeight: "700",
    color: colors.accentGreen, letterSpacing: 0.5,
  },
  eventoTitulo: { fontSize: fontSize.lg, fontWeight: "600", color: colors.textPrimary },
  eventoOrigen: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
  eventoInfo: { fontSize: fontSize.sm, color: colors.accentGreen, marginTop: 6, fontWeight: "500" },

  // Section
  section: { marginHorizontal: spacing.lg, marginTop: spacing.lg },
  sectionTitle: {
    fontSize: fontSize.xs, fontWeight: "600", color: colors.textMuted,
    marginBottom: spacing.sm, textTransform: "uppercase", letterSpacing: 1,
  },

  // Calendar cards
  calCard: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg,
    padding: spacing.md, marginBottom: spacing.sm,
  },
  calCardLeft: { flexDirection: "row", alignItems: "center", flex: 1 },
  calIcon: {
    width: 44, height: 44, borderRadius: borderRadius.md,
    justifyContent: "center", alignItems: "center", marginRight: spacing.sm,
  },
  calInfo: { flex: 1 },
  calName: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary },
  calStatus: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },

  connectBtn: {
    backgroundColor: colors.primary, paddingHorizontal: 16, paddingVertical: 8,
    borderRadius: borderRadius.full, minWidth: 90, alignItems: "center",
  },
  connectBtnDisabled: { backgroundColor: colors.bgCardLight },
  connectText: { color: "#FFF", fontWeight: "600", fontSize: fontSize.sm },

  disconnectBtn: {
    backgroundColor: colors.accentRed + "15", paddingHorizontal: 14, paddingVertical: 8,
    borderRadius: borderRadius.full,
  },
  disconnectText: { color: colors.accentRed, fontWeight: "600", fontSize: fontSize.sm },

  // Config
  configCard: {
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg,
    padding: spacing.md,
  },
  configRow: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
  },
  configLeft: { flexDirection: "row", alignItems: "center", flex: 1, marginRight: spacing.md },
  configInfo: { marginLeft: spacing.sm, flex: 1 },
  configLabel: { fontSize: fontSize.md, fontWeight: "500", color: colors.textPrimary },
  configDesc: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },

  separator: {
    height: 1, backgroundColor: colors.border,
    marginVertical: spacing.md,
  },

  // Modo selector
  modoTitle: {
    fontSize: fontSize.sm, fontWeight: "600", color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  modoOption: {
    flexDirection: "row", alignItems: "flex-start",
    padding: spacing.sm, borderRadius: borderRadius.md,
    marginBottom: spacing.xs,
  },
  modoOptionActive: { backgroundColor: colors.primary + "12" },
  modoRadio: {
    width: 20, height: 20, borderRadius: 10, borderWidth: 2,
    borderColor: colors.primary, justifyContent: "center", alignItems: "center",
    marginTop: 2, marginRight: spacing.sm,
  },
  modoRadioInner: {
    width: 10, height: 10, borderRadius: 5, backgroundColor: colors.primary,
  },
  modoInfo: { flex: 1 },
  modoLabel: { fontSize: fontSize.md, fontWeight: "500", color: colors.textPrimary },
  modoDesc: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },

  // How it works
  howCard: {
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg,
    padding: spacing.md,
  },
  howStep: { flexDirection: "row", marginBottom: 4 },
  howStepLeft: { alignItems: "center", width: 30, marginRight: spacing.sm },
  howStepNumber: {
    width: 24, height: 24, borderRadius: 12,
    backgroundColor: colors.primary + "25", justifyContent: "center", alignItems: "center",
  },
  howStepNumberText: { fontSize: fontSize.xs, fontWeight: "700", color: colors.primary },
  howStepLine: {
    width: 2, flex: 1, backgroundColor: colors.primary + "20",
    marginVertical: 4,
  },
  howStepContent: {
    flexDirection: "row", alignItems: "flex-start", flex: 1,
    paddingBottom: spacing.md,
  },
  howStepIcon: {
    width: 32, height: 32, borderRadius: borderRadius.sm,
    backgroundColor: colors.primary + "12", justifyContent: "center",
    alignItems: "center", marginRight: spacing.sm,
  },
  howStepText: { flex: 1 },
  howStepTitle: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary },
  howStepDesc: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
});
