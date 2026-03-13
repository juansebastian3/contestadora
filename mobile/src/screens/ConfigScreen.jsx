/**
 * ConfigScreen - Configuracion, numero Twilio y guia de desvio de llamadas
 */
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Platform,
  Linking,
  Clipboard,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";
import api from "../services/api";

// ─── Codigos GSM estandar de desvio ─────────────────────
const CODIGOS_DESVIO = [
  {
    key: "no_contesta",
    titulo: "Si no contesto",
    descripcion: "Desvia cuando no contestas despues de ~20 segundos. El mas recomendado.",
    codigoActivar: (num) => `**61*${num}#`,
    codigoDesactivar: "##61#",
    recomendado: true,
  },
  {
    key: "sin_senal",
    titulo: "Sin senal / apagado",
    descripcion: "Desvia cuando tu celular esta apagado o sin cobertura.",
    codigoActivar: (num) => `**62*${num}#`,
    codigoDesactivar: "##62#",
    recomendado: true,
  },
  {
    key: "ocupado",
    titulo: "Linea ocupada",
    descripcion: "Desvia cuando estas en otra llamada.",
    codigoActivar: (num) => `**67*${num}#`,
    codigoDesactivar: "##67#",
    recomendado: false,
  },
];

export default function ConfigScreen({ navigation }) {
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);
  const [guiaAbierta, setGuiaAbierta] = useState(false);
  const [settings, setSettings] = useState({
    notifWhatsapp: true,
    notifPush: true,
    notifSoloImportantes: false,
  });

  useEffect(() => {
    loadPerfil();
  }, []);

  async function loadPerfil() {
    try {
      const data = await api.getPerfil();
      setPerfil(data);
      setSettings({
        notifWhatsapp: data.notificaciones?.whatsapp ?? true,
        notifPush: data.notificaciones?.push ?? true,
        notifSoloImportantes: data.notificaciones?.solo_importantes ?? false,
      });
    } catch (e) {
      const saved = await api.getSavedProfile();
      if (saved) setPerfil(saved);
    } finally {
      setLoading(false);
    }
  }

  async function toggleSetting(key, configKey) {
    const newValue = !settings[key];
    setSettings((s) => ({ ...s, [key]: newValue }));
    try {
      await api.updateConfig(configKey, String(newValue));
    } catch (e) {
      setSettings((s) => ({ ...s, [key]: !newValue }));
    }
  }

  async function handleLogout() {
    Alert.alert(
      "Cerrar sesion",
      "Seguro que quieres cerrar sesion?",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Cerrar sesion",
          style: "destructive",
          onPress: async () => {
            await api.logout();
          },
        },
      ]
    );
  }

  // ─── Abrir marcador con codigo GSM ──────────────────────
  function abrirMarcador(codigo) {
    const url = `tel:${encodeURIComponent(codigo)}`;
    Linking.canOpenURL(url).then((supported) => {
      if (supported) {
        Linking.openURL(url);
      } else {
        Alert.alert("No disponible", "No se puede abrir el marcador en este dispositivo.");
      }
    });
  }

  function copiarCodigo(codigo) {
    Clipboard.setString(codigo);
    Alert.alert("Copiado", `Codigo copiado: ${codigo}`);
  }

  function cancelarTodosDesvios() {
    Alert.alert(
      "Cancelar desvios",
      "Esto desactivara todos los desvios de llamadas. Tu asistente dejara de recibir llamadas.",
      [
        { text: "No, mantener", style: "cancel" },
        {
          text: "Si, cancelar desvios",
          style: "destructive",
          onPress: () => abrirMarcador("##002#"),
        },
      ]
    );
  }

  // ─── Componentes auxiliares ─────────────────────────────
  const Section = ({ title, children }) => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionCard}>{children}</View>
    </View>
  );

  const SettingRow = ({ icon, label, description, switchKey, configKey, onPress }) => (
    <TouchableOpacity
      style={styles.settingRow}
      activeOpacity={switchKey ? 1 : 0.7}
      onPress={onPress}
      disabled={!!switchKey}
    >
      <View style={styles.settingLeft}>
        <View style={styles.settingIcon}>
          <Ionicons name={icon} size={20} color={colors.primary} />
        </View>
        <View style={styles.settingInfo}>
          <Text style={styles.settingLabel}>{label}</Text>
          {description && <Text style={styles.settingDesc}>{description}</Text>}
        </View>
      </View>
      {switchKey ? (
        <Switch
          value={settings[switchKey]}
          onValueChange={() => toggleSetting(switchKey, configKey)}
          trackColor={{ false: colors.bgCardLight, true: colors.primary + "80" }}
          thumbColor={settings[switchKey] ? colors.primary : colors.textMuted}
        />
      ) : (
        <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
      )}
    </TouchableOpacity>
  );

  const modoTexto = {
    desconocidos: "Solo desconocidos",
    luna: "Luna (todas las llamadas)",
    desactivado: "Desactivado",
  };

  const numeroTwilio = perfil?.telefono_twilio;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Configuracion</Text>
      </View>

      {/* Estado del sistema */}
      <View style={styles.statusCard}>
        <View style={styles.statusRow}>
          <View style={[styles.statusDot, { backgroundColor: colors.accentGreen }]} />
          <Text style={styles.statusLabel}>Sistema activo</Text>
        </View>
        <Text style={styles.statusVersion}>v1.0.0</Text>
      </View>

      {/* Info del perfil */}
      {perfil && (
        <View style={styles.profileCard}>
          <View style={styles.profileAvatar}>
            <Ionicons name="person" size={28} color={colors.primary} />
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{perfil.nombre}</Text>
            <Text style={styles.profileEmail}>{perfil.email}</Text>
            <TouchableOpacity
              style={styles.planBadge}
              onPress={() => navigation.navigate("Planes")}
              activeOpacity={0.7}
            >
              <Text style={styles.planText}>
                {({ free: "Trial Gratis", basico: "Estudiante", pro: "Adulto", premium: "Ejecutivo" })[perfil.plan] || "Plan Free"}
              </Text>
              <Ionicons name="chevron-forward" size={12} color={colors.primary} style={{ marginLeft: 4 }} />
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* ═══ NUMERO TWILIO + GUIA DE DESVIO ═══ */}
      {perfil && (
        <View style={styles.twilioCard}>
          <View style={styles.twilioHeader}>
            <Ionicons name="call" size={22} color={numeroTwilio ? colors.accentGreen : colors.textMuted} />
            <Text style={styles.twilioTitle}>Tu numero de asistente</Text>
          </View>

          {numeroTwilio ? (
            <>
              <Text style={styles.twilioNumber}>{numeroTwilio}</Text>

              {/* Boton para abrir guia */}
              <TouchableOpacity
                style={styles.guiaButton}
                onPress={() => setGuiaAbierta(!guiaAbierta)}
                activeOpacity={0.7}
              >
                <Ionicons name={guiaAbierta ? "chevron-up" : "chevron-down"} size={18} color={colors.primary} />
                <Text style={styles.guiaButtonText}>
                  {guiaAbierta ? "Ocultar guia de configuracion" : "Como configuro el desvio de llamadas?"}
                </Text>
              </TouchableOpacity>

              {/* GUIA EXPANDIBLE */}
              {guiaAbierta && (
                <View style={styles.guiaContainer}>
                  {/* Mensaje de tranquilidad */}
                  <View style={styles.tranquiloCard}>
                    <Text style={styles.tranquiloText}>
                      Tranquilo, activar y desactivar el desvio es igual de facil. Si en algun momento quieres dejar de usarlo, un solo codigo lo quita al instante.
                    </Text>
                  </View>

                  {/* Explicacion */}
                  <View style={styles.guiaIntro}>
                    <Ionicons name="information-circle" size={20} color={colors.primary} />
                    <Text style={styles.guiaIntroText}>
                      Debes marcar estos codigos en el teclado de tu telefono (como si fueras a llamar). Tu operador confirmara que el desvio quedo activo.
                    </Text>
                  </View>

                  {/* Paso a paso */}
                  <View style={styles.pasosContainer}>
                    <View style={styles.paso}>
                      <View style={styles.pasoNumero}><Text style={styles.pasoNumeroText}>1</Text></View>
                      <Text style={styles.pasoText}>Abre la app <Text style={styles.bold}>Telefono</Text> de tu celular</Text>
                    </View>
                    <View style={styles.paso}>
                      <View style={styles.pasoNumero}><Text style={styles.pasoNumeroText}>2</Text></View>
                      <Text style={styles.pasoText}>Ve al <Text style={styles.bold}>teclado numerico</Text> (donde marcas numeros)</Text>
                    </View>
                    <View style={styles.paso}>
                      <View style={styles.pasoNumero}><Text style={styles.pasoNumeroText}>3</Text></View>
                      <Text style={styles.pasoText}>Marca el codigo que quieras activar y presiona <Text style={styles.bold}>Llamar</Text></Text>
                    </View>
                  </View>

                  {/* Codigos disponibles */}
                  <Text style={styles.guiaSeccionTitulo}>Elige que tipo de desvio activar:</Text>

                  {CODIGOS_DESVIO.map((desvio) => {
                    const codigo = desvio.codigoActivar(numeroTwilio);
                    return (
                      <View key={desvio.key} style={[styles.desvioCard, desvio.recomendado && styles.desvioCardRecomendado]}>
                        <View style={styles.desvioHeader}>
                          <Text style={styles.desvioTitulo}>{desvio.titulo}</Text>
                          {desvio.recomendado && (
                            <View style={styles.recomendadoBadge}>
                              <Text style={styles.recomendadoText}>Recomendado</Text>
                            </View>
                          )}
                        </View>
                        <Text style={styles.desvioDesc}>{desvio.descripcion}</Text>

                        {/* Codigo a marcar */}
                        <View style={styles.codigoContainer}>
                          <Text style={styles.codigoText}>{codigo}</Text>
                          <TouchableOpacity onPress={() => copiarCodigo(codigo)} style={styles.copiarBtn}>
                            <Ionicons name="copy-outline" size={16} color={colors.primary} />
                          </TouchableOpacity>
                        </View>

                        {/* Botones de accion */}
                        <View style={styles.desvioActions}>
                          <TouchableOpacity
                            style={styles.activarBtn}
                            onPress={() => abrirMarcador(codigo)}
                          >
                            <Ionicons name="call-outline" size={16} color="#fff" />
                            <Text style={styles.activarBtnText}>Activar</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={styles.desactivarBtn}
                            onPress={() => abrirMarcador(desvio.codigoDesactivar)}
                          >
                            <Text style={styles.desactivarBtnText}>Desactivar</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    );
                  })}

                  {/* Tip de plataforma */}
                  <View style={styles.tipCard}>
                    <Ionicons name={Platform.OS === "ios" ? "logo-apple" : "logo-android"} size={18} color={colors.accent} />
                    <Text style={styles.tipText}>
                      {Platform.OS === "ios"
                        ? 'En iPhone, el menu Ajustes > Telefono > Desvio solo controla desvio de TODAS las llamadas. Para desvio condicional (si no contestas) debes usar estos codigos GSM.'
                        : 'En Android tambien puedes ir a Telefono > Ajustes > Desvio de llamadas > Desviar si no hay respuesta, y poner tu numero de asistente ahi directamente.'}
                    </Text>
                  </View>

                  {/* Nota sobre calendario */}
                  <View style={styles.calendarNote}>
                    <Ionicons name="calendar-outline" size={16} color={colors.primary} />
                    <Text style={styles.calendarNoteText}>
                      Con el plan Ejecutivo, Dora se convierte en tu AgendaDora: consulta tu calendario automaticamente. Si estas en reunion, le avisa al llamante y ofrece agendar una devolucion.
                    </Text>
                  </View>

                  {/* ═══ OFFBOARDING: como quitar el desvio ═══ */}
                  <View style={styles.offboardingCard}>
                    <View style={styles.offboardingHeader}>
                      <Ionicons name="shield-checkmark" size={20} color={colors.accentGreen} />
                      <Text style={styles.offboardingTitle}>Quieres desactivarlo? Es igual de facil</Text>
                    </View>
                    <Text style={styles.offboardingDesc}>
                      Si en algun momento quieres dejar de usar ContestaDora, simplemente marca este codigo en tu teclado y listo. Tus llamadas volveran a la normalidad al instante. Dora te va a extranar.
                    </Text>

                    <View style={styles.offboardingCodeContainer}>
                      <View style={styles.offboardingCodeBox}>
                        <Text style={styles.offboardingCodeLabel}>Cancelar todos los desvios</Text>
                        <Text style={styles.offboardingCode}>##002#</Text>
                      </View>
                      <View style={styles.offboardingActions}>
                        <TouchableOpacity
                          style={styles.offboardingCallBtn}
                          onPress={() => abrirMarcador("##002#")}
                        >
                          <Ionicons name="call-outline" size={16} color={colors.accentRed} />
                          <Text style={styles.offboardingCallText}>Marcar</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={styles.offboardingCopyBtn}
                          onPress={() => copiarCodigo("##002#")}
                        >
                          <Ionicons name="copy-outline" size={14} color={colors.textMuted} />
                        </TouchableOpacity>
                      </View>
                    </View>

                    <Text style={styles.offboardingNote}>
                      Tambien puedes desactivar cada tipo por separado usando el boton "Desactivar" de arriba. No se borra tu cuenta ni tus datos.
                    </Text>
                  </View>
                </View>
              )}
            </>
          ) : (
            <Text style={styles.twilioDesc}>
              {perfil.plan === "free"
                ? "Suscribete a un plan Basico o superior para recibir tu numero de asistente dedicado."
                : "Tu numero sera asignado automaticamente. Si no lo ves, reinicia la app."}
            </Text>
          )}
        </View>
      )}

      <Section title="Filtrado">
        <SettingRow
          icon="shield-checkmark"
          label="Modo de filtrado"
          description={modoTexto[perfil?.modo_filtrado] || "Cargando..."}
          onPress={() => {}}
        />
        <SettingRow
          icon="moon"
          label="Horario Luna"
          description={
            perfil?.horario_luna?.inicio
              ? `${perfil.horario_luna.inicio} - ${perfil.horario_luna.fin}`
              : "No configurado"
          }
          onPress={() => {}}
        />
      </Section>

      <Section title="Notificaciones">
        <SettingRow
          icon="logo-whatsapp"
          label="WhatsApp"
          description="Resumen al finalizar cada llamada"
          switchKey="notifWhatsapp"
          configKey="notif_whatsapp"
        />
        <SettingRow
          icon="notifications"
          label="Push notifications"
          description="Alertas de llamadas importantes"
          switchKey="notifPush"
          configKey="notif_push"
        />
        <SettingRow
          icon="star"
          label="Solo importantes"
          description="Notificar solo prioridad Alta/Media"
          switchKey="notifSoloImportantes"
          configKey="notif_solo_importantes"
        />
      </Section>

      <Section title="Soporte">
        <SettingRow icon="help-circle" label="Ayuda" onPress={() => {}} />
        <SettingRow icon="document-text" label="Terminos y privacidad" onPress={() => navigation.navigate("Legal")} />
      </Section>

      {/* Cerrar sesion */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={20} color={colors.accentRed} />
        <Text style={styles.logoutText}>Cerrar sesion</Text>
      </TouchableOpacity>

      <View style={{ height: 120 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.xxl + 20, paddingBottom: spacing.md },
  title: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  statusCard: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    backgroundColor: colors.bgCard, marginHorizontal: spacing.lg,
    borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: spacing.md,
  },
  statusRow: { flexDirection: "row", alignItems: "center" },
  statusDot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  statusLabel: { fontSize: fontSize.md, fontWeight: "600", color: colors.accentGreen },
  statusVersion: { fontSize: fontSize.xs, color: colors.textMuted },

  profileCard: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: colors.bgCard, marginHorizontal: spacing.lg,
    borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: spacing.md,
  },
  profileAvatar: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: colors.primary + "20",
    justifyContent: "center", alignItems: "center", marginRight: spacing.md,
  },
  profileInfo: { flex: 1 },
  profileName: { fontSize: fontSize.lg, fontWeight: "700", color: colors.textPrimary },
  profileEmail: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: 2 },
  planBadge: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: colors.primary + "25", paddingHorizontal: 10, paddingVertical: 3,
    borderRadius: borderRadius.full, alignSelf: "flex-start", marginTop: 6,
  },
  planText: { fontSize: fontSize.xs, fontWeight: "700", color: colors.primary },

  section: { marginHorizontal: spacing.lg, marginTop: spacing.lg },
  sectionTitle: { fontSize: fontSize.sm, fontWeight: "600", color: colors.textMuted, marginBottom: spacing.sm, textTransform: "uppercase", letterSpacing: 1 },
  sectionCard: { backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, overflow: "hidden" },
  settingRow: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    padding: spacing.md, borderBottomWidth: 0.5, borderBottomColor: colors.border,
  },
  settingLeft: { flexDirection: "row", alignItems: "center", flex: 1, marginRight: spacing.md },
  settingIcon: { width: 36, height: 36, borderRadius: borderRadius.sm, backgroundColor: colors.primary + "15", justifyContent: "center", alignItems: "center", marginRight: spacing.sm },
  settingInfo: { flex: 1 },
  settingLabel: { fontSize: fontSize.md, fontWeight: "500", color: colors.textPrimary },
  settingDesc: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },

  // ─── Twilio Card ───────────────────────────────────
  twilioCard: {
    backgroundColor: colors.bgCard, marginHorizontal: spacing.lg,
    borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: spacing.md,
    borderWidth: 1, borderColor: colors.primary + "30",
  },
  twilioHeader: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  twilioTitle: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary, marginLeft: 10 },
  twilioNumber: { fontSize: fontSize.xl, fontWeight: "800", color: colors.accentGreen, marginBottom: 8, letterSpacing: 1 },
  twilioDesc: { fontSize: fontSize.sm, color: colors.textSecondary, lineHeight: 18 },

  // ─── Guia de desvio ────────────────────────────────
  guiaButton: { flexDirection: "row", alignItems: "center", paddingVertical: 10, gap: 6 },
  guiaButtonText: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },

  guiaContainer: { marginTop: 8 },

  guiaIntro: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    backgroundColor: colors.primary + "10", borderRadius: borderRadius.md,
    padding: 12, marginBottom: 16,
  },
  guiaIntroText: { color: colors.textSecondary, fontSize: fontSize.sm, lineHeight: 20, flex: 1 },

  pasosContainer: { marginBottom: 16 },
  paso: { flexDirection: "row", alignItems: "center", marginBottom: 10, gap: 10 },
  pasoNumero: {
    width: 26, height: 26, borderRadius: 13,
    backgroundColor: colors.primary, justifyContent: "center", alignItems: "center",
  },
  pasoNumeroText: { color: "#fff", fontSize: fontSize.sm, fontWeight: "700" },
  pasoText: { color: colors.textSecondary, fontSize: fontSize.sm, flex: 1, lineHeight: 18 },
  bold: { fontWeight: "700", color: colors.textPrimary },

  guiaSeccionTitulo: { color: colors.textPrimary, fontSize: fontSize.md, fontWeight: "700", marginBottom: 10 },

  desvioCard: {
    backgroundColor: colors.bg, borderRadius: borderRadius.md,
    padding: 14, marginBottom: 10, borderWidth: 1, borderColor: colors.border,
  },
  desvioCardRecomendado: { borderColor: colors.primary + "50" },
  desvioHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 4 },
  desvioTitulo: { color: colors.textPrimary, fontSize: fontSize.md, fontWeight: "600" },
  recomendadoBadge: { backgroundColor: colors.accentGreen + "20", paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  recomendadoText: { color: colors.accentGreen, fontSize: fontSize.xs, fontWeight: "600" },
  desvioDesc: { color: colors.textMuted, fontSize: fontSize.xs, lineHeight: 16, marginBottom: 10 },

  codigoContainer: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    backgroundColor: "#0f172a", borderRadius: borderRadius.sm, padding: 10, marginBottom: 10,
  },
  codigoText: { color: colors.accentGreen, fontSize: fontSize.md, fontWeight: "700", fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace", letterSpacing: 0.5 },
  copiarBtn: { padding: 4 },

  desvioActions: { flexDirection: "row", gap: 8 },
  activarBtn: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    backgroundColor: colors.primary, borderRadius: borderRadius.sm, paddingVertical: 10,
  },
  activarBtnText: { color: "#fff", fontSize: fontSize.sm, fontWeight: "600" },
  desactivarBtn: {
    flex: 1, alignItems: "center", justifyContent: "center",
    backgroundColor: colors.bgCardLight, borderRadius: borderRadius.sm, paddingVertical: 10,
  },
  desactivarBtnText: { color: colors.textMuted, fontSize: fontSize.sm, fontWeight: "500" },

  tipCard: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    backgroundColor: colors.accent + "10", borderRadius: borderRadius.md,
    padding: 12, marginTop: 6, marginBottom: 10,
  },
  tipText: { color: colors.textSecondary, fontSize: fontSize.xs, lineHeight: 18, flex: 1 },

  calendarNote: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    backgroundColor: colors.primary + "08", borderRadius: borderRadius.md,
    padding: 12, borderWidth: 1, borderColor: colors.primary + "15",
    marginTop: 6,
  },
  calendarNoteText: { color: colors.textSecondary, fontSize: fontSize.xs, lineHeight: 18, flex: 1 },

  tranquiloCard: {
    backgroundColor: colors.accentGreen + "10", borderRadius: borderRadius.md,
    padding: 12, marginBottom: 16, borderWidth: 1, borderColor: colors.accentGreen + "20",
  },
  tranquiloText: { color: colors.accentGreen, fontSize: fontSize.sm, lineHeight: 20, textAlign: "center", fontWeight: "500" },

  offboardingCard: {
    backgroundColor: colors.bg, borderRadius: borderRadius.md,
    padding: 16, marginTop: 16, borderWidth: 1, borderColor: colors.accentGreen + "25",
  },
  offboardingHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 },
  offboardingTitle: { color: colors.textPrimary, fontSize: fontSize.md, fontWeight: "700", flex: 1 },
  offboardingDesc: { color: colors.textSecondary, fontSize: fontSize.sm, lineHeight: 20, marginBottom: 14 },
  offboardingCodeContainer: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    backgroundColor: "#0f172a", borderRadius: borderRadius.sm, padding: 12, marginBottom: 12,
  },
  offboardingCodeBox: { flex: 1 },
  offboardingCodeLabel: { color: colors.textMuted, fontSize: fontSize.xs, marginBottom: 2 },
  offboardingCode: { color: colors.accentRed, fontSize: fontSize.lg, fontWeight: "800", fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace" },
  offboardingActions: { flexDirection: "row", alignItems: "center", gap: 8 },
  offboardingCallBtn: {
    flexDirection: "row", alignItems: "center", gap: 4,
    backgroundColor: colors.accentRed + "15", borderRadius: borderRadius.sm,
    paddingVertical: 8, paddingHorizontal: 14,
  },
  offboardingCallText: { color: colors.accentRed, fontSize: fontSize.sm, fontWeight: "600" },
  offboardingCopyBtn: { padding: 8 },
  offboardingNote: { color: colors.textMuted, fontSize: fontSize.xs, lineHeight: 16 },

  // ─── Otros ─────────────────────────────────────────
  logoutButton: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    marginHorizontal: spacing.lg, marginTop: spacing.xl,
    backgroundColor: colors.accentRed + "15", borderRadius: borderRadius.lg,
    padding: spacing.md,
  },
  logoutText: { color: colors.accentRed, fontSize: fontSize.md, fontWeight: "600", marginLeft: spacing.sm },
});
