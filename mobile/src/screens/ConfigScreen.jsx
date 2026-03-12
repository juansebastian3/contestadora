/**
 * ConfigScreen - Configuración y estado del sistema (conectada al backend)
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
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";
import api from "../services/api";

export default function ConfigScreen() {
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);
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
      // Cargar perfil guardado localmente como fallback
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
      // Revertir si falla
      setSettings((s) => ({ ...s, [key]: !newValue }));
    }
  }

  async function handleLogout() {
    Alert.alert(
      "Cerrar sesión",
      "¿Seguro que quieres cerrar sesión?",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Cerrar sesión",
          style: "destructive",
          onPress: async () => {
            await api.logout();
            // La app detectará que no hay token y mostrará login
            // Forzar un re-render navegando (en producción usarías un context global)
            // Por ahora el flujo de App.jsx maneja esto
          },
        },
      ]
    );
  }

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

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Configuración</Text>
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
            <View style={styles.planBadge}>
              <Text style={styles.planText}>Plan {(perfil.plan || "free").toUpperCase()}</Text>
            </View>
          </View>
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
        <SettingRow icon="document-text" label="Términos y privacidad" onPress={() => {}} />
      </Section>

      {/* Cerrar sesión */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out-outline" size={20} color={colors.accentRed} />
        <Text style={styles.logoutText}>Cerrar sesión</Text>
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

  logoutButton: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    marginHorizontal: spacing.lg, marginTop: spacing.xl,
    backgroundColor: colors.accentRed + "15", borderRadius: borderRadius.lg,
    padding: spacing.md,
  },
  logoutText: { color: colors.accentRed, fontSize: fontSize.md, fontWeight: "600", marginLeft: spacing.sm },
});
