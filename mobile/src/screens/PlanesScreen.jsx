/**
 * PlanesScreen - Tabla comparativa de planes y suscripcion
 */
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";
import api from "../services/api";

// ─── Datos de planes ─────────────────────────────────────
const PLANES = [
  {
    key: "free",
    nombre: "Prueba gratis",
    subtitulo: null,
    precio: "$0 / 7 dias",
    color: colors.accentGreen,
    descripcion: "Experimenta el plan Adulto completo durante 7 dias. Sin tarjeta.",
  },
  {
    key: "basico",
    nombre: "Basico",
    subtitulo: "Estudiante",
    precio: "$4.99/mes",
    color: colors.textSecondary,
    descripcion:
      "Recibes unas 3 llamadas de desconocidos al dia y no quieres distraerte mientras estudias o trabajas.",
  },
  {
    key: "pro",
    nombre: "Pro",
    subtitulo: "Adulto",
    precio: "$5.99/mes",
    color: colors.primary,
    destacado: true,
    descripcion:
      "Te llaman bastante para ofrecerte cosas que no necesitas, pero tienes miedo de perder una llamada importante.",
  },
  {
    key: "premium",
    nombre: "Premium",
    subtitulo: "Ejecutivo",
    precio: "$9.99/mes",
    color: colors.accent,
    descripcion:
      "Tienes tramites, clientes y reuniones. Necesitas un secretario digital que filtre, envie recados y agende.",
  },
];

// ─── Features de la tabla comparativa ─────────────────────
const CHECK = { value: true };
const CROSS = { value: false };
const TEXT = (t) => ({ value: t });

const FEATURES = [
  { label: "Precio",                     free: TEXT("$0/7d"), basico: TEXT("$4.99"),  pro: TEXT("$5.99"),  premium: TEXT("$9.99") },
  { label: "Llamadas/mes",               free: TEXT("300"),   basico: TEXT("100"),    pro: TEXT("300"),    premium: TEXT("Ilimitadas") },
  { label: "Numero propio",              free: TEXT("Temp."), basico: CHECK,          pro: CHECK,          premium: CHECK },
  { label: "IA contesta y transcribe",   free: CHECK,         basico: CHECK,          pro: CHECK,          premium: CHECK },
  { label: "Analisis IA + WhatsApp",     free: CHECK,         basico: CHECK,          pro: CHECK,          premium: CHECK },
  { label: "Tu voz como saludo",         free: CHECK,         basico: CROSS,          pro: CHECK,          premium: CHECK },
  { label: "Modo Luna (no molestar)",    free: CHECK,         basico: CROSS,          pro: CHECK,          premium: CHECK },
  { label: "Prompt personalizado",       free: CHECK,         basico: CROSS,          pro: CHECK,          premium: CHECK },
  { label: "Calendario integrado",       free: CROSS,         basico: CROSS,          pro: CHECK,          premium: CHECK },
  { label: "IA conversa (agente)",       free: CROSS,         basico: CROSS,          pro: CROSS,          premium: CHECK },
  { label: "Voces premium + soporte",    free: CROSS,         basico: CROSS,          pro: CROSS,          premium: CHECK },
];

// ─── Componente de celda ─────────────────────────────────
function CellValue({ data, highlight }) {
  if (typeof data.value === "string") {
    return (
      <Text style={[styles.cellText, highlight && { color: colors.primary, fontWeight: "700" }]}>
        {data.value}
      </Text>
    );
  }
  if (data.value === true) {
    return <Ionicons name="checkmark-circle" size={18} color={colors.accentGreen} />;
  }
  return <Ionicons name="close-circle" size={18} color={colors.textMuted + "60"} />;
}

export default function PlanesScreen({ navigation }) {
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPerfil();
  }, []);

  async function loadPerfil() {
    try {
      const data = await api.getPerfil();
      setPerfil(data);
    } catch (e) {
      // fallback
    } finally {
      setLoading(false);
    }
  }

  const planActual = perfil?.plan || "free";
  const trial = perfil?.trial;

  function abrirSuscripcion() {
    // Abrir la web de suscripcion en el navegador
    const base = api.getBaseUrl ? api.getBaseUrl() : "";
    if (base) {
      Linking.openURL(`${base}/suscripcion`);
    }
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Planes</Text>
      </View>

      {/* Banner de trial */}
      {trial && trial.trial_activo && (
        <View style={styles.trialBanner}>
          <Ionicons name="time-outline" size={20} color={colors.accentGreen} />
          <View style={{ flex: 1, marginLeft: 10 }}>
            <Text style={styles.trialTitle}>Trial activo</Text>
            <Text style={styles.trialSubtitle}>
              Te quedan {trial.dias_restantes} dia{trial.dias_restantes !== 1 ? "s" : ""} de experiencia Pro completa
            </Text>
          </View>
        </View>
      )}

      {trial && trial.trial_expirado && planActual === "free" && (
        <View style={[styles.trialBanner, { borderColor: colors.accentRed + "40" }]}>
          <Ionicons name="alert-circle-outline" size={20} color={colors.accentRed} />
          <View style={{ flex: 1, marginLeft: 10 }}>
            <Text style={[styles.trialTitle, { color: colors.accentRed }]}>Trial finalizado</Text>
            <Text style={styles.trialSubtitle}>
              Elige un plan para que Dora siga contestando por ti
            </Text>
          </View>
        </View>
      )}

      {/* Cards de planes */}
      {PLANES.map((plan) => {
        const esActual = plan.key === planActual;
        const esTrial = plan.key === "free" && trial?.trial_activo;
        return (
          <View
            key={plan.key}
            style={[
              styles.planCard,
              plan.destacado && styles.planCardDestacado,
              esActual && styles.planCardActual,
            ]}
          >
            <View style={styles.planHeader}>
              <View style={{ flex: 1 }}>
                <View style={styles.planNameRow}>
                  <Text style={[styles.planNombre, { color: plan.color }]}>{plan.nombre}</Text>
                  {esActual && (
                    <View style={styles.actualBadge}>
                      <Text style={styles.actualBadgeText}>{esTrial ? "Trial" : "Actual"}</Text>
                    </View>
                  )}
                </View>
                {plan.subtitulo && (
                  <Text style={styles.planSubtitulo}>{plan.subtitulo}</Text>
                )}
              </View>
              <Text style={[styles.planPrecio, { color: plan.color }]}>{plan.precio}</Text>
            </View>
            <Text style={styles.planDescripcion}>{plan.descripcion}</Text>
          </View>
        );
      })}

      {/* Boton de suscripcion */}
      {planActual === "free" && (
        <TouchableOpacity style={styles.suscribirBtn} onPress={abrirSuscripcion} activeOpacity={0.8}>
          <Text style={styles.suscribirText}>Elegir plan</Text>
          <Ionicons name="arrow-forward" size={18} color="#fff" />
        </TouchableOpacity>
      )}

      {/* TABLA COMPARATIVA */}
      <View style={styles.tablaContainer}>
        <Text style={styles.tablaTitle}>Compara los planes en detalle</Text>

        {/* Header de columnas */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View>
            <View style={styles.tablaHeaderRow}>
              <View style={styles.tablaLabelCol} />
              <View style={styles.tablaCol}>
                <Text style={[styles.tablaHeaderText, { color: colors.accentGreen }]}>Prueba</Text>
              </View>
              <View style={styles.tablaCol}>
                <Text style={styles.tablaHeaderText}>Estudiante</Text>
              </View>
              <View style={[styles.tablaCol, styles.tablaColDestacado]}>
                <Text style={[styles.tablaHeaderText, { color: colors.primary }]}>Adulto</Text>
              </View>
              <View style={styles.tablaCol}>
                <Text style={[styles.tablaHeaderText, { color: colors.accent }]}>Ejecutivo</Text>
              </View>
            </View>

            {/* Filas */}
            {FEATURES.map((feat, i) => (
              <View key={i} style={[styles.tablaRow, i % 2 === 0 && styles.tablaRowAlt]}>
                <View style={styles.tablaLabelCol}>
                  <Text style={styles.tablaLabel}>{feat.label}</Text>
                </View>
                <View style={styles.tablaCol}>
                  <CellValue data={feat.free} />
                </View>
                <View style={styles.tablaCol}>
                  <CellValue data={feat.basico} />
                </View>
                <View style={[styles.tablaCol, styles.tablaColDestacado]}>
                  <CellValue data={feat.pro} highlight />
                </View>
                <View style={styles.tablaCol}>
                  <CellValue data={feat.premium} />
                </View>
              </View>
            ))}
          </View>
        </ScrollView>
      </View>

      <View style={{ height: 120 }} />
    </ScrollView>
  );
}

const COL_WIDTH = 72;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl + 20,
    paddingBottom: spacing.md,
  },
  backBtn: { marginRight: spacing.md },
  title: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },

  // Trial banner
  trialBanner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.bgCard,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.accentGreen + "40",
  },
  trialTitle: { fontSize: fontSize.md, fontWeight: "700", color: colors.accentGreen },
  trialSubtitle: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },

  // Plan cards
  planCard: {
    backgroundColor: colors.bgCard,
    marginHorizontal: spacing.lg,
    marginBottom: spacing.sm,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  planCardDestacado: {
    borderColor: colors.primary + "60",
    borderWidth: 1.5,
  },
  planCardActual: {
    borderColor: colors.accentGreen + "60",
  },
  planHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 6,
  },
  planNameRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  planNombre: { fontSize: fontSize.lg, fontWeight: "700" },
  planSubtitulo: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: 2 },
  planPrecio: { fontSize: fontSize.md, fontWeight: "700" },
  planDescripcion: { fontSize: fontSize.xs, color: colors.textSecondary, lineHeight: 17 },
  actualBadge: {
    backgroundColor: colors.accentGreen + "20",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  actualBadgeText: { fontSize: fontSize.xs, color: colors.accentGreen, fontWeight: "600" },

  // Suscribir
  suscribirBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: colors.primary,
    marginHorizontal: spacing.lg,
    marginTop: spacing.sm,
    borderRadius: borderRadius.lg,
    paddingVertical: 14,
  },
  suscribirText: { color: "#fff", fontSize: fontSize.md, fontWeight: "700" },

  // Tabla comparativa
  tablaContainer: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.xl,
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    overflow: "hidden",
  },
  tablaTitle: {
    fontSize: fontSize.md,
    fontWeight: "700",
    color: colors.textPrimary,
    textAlign: "center",
    marginBottom: spacing.md,
  },
  tablaHeaderRow: {
    flexDirection: "row",
    borderBottomWidth: 2,
    borderBottomColor: colors.primary,
    paddingBottom: 8,
    marginBottom: 4,
  },
  tablaRow: {
    flexDirection: "row",
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: colors.border,
  },
  tablaRowAlt: {
    backgroundColor: colors.bg + "60",
  },
  tablaLabelCol: {
    width: 130,
    justifyContent: "center",
    paddingRight: 8,
  },
  tablaCol: {
    width: COL_WIDTH,
    alignItems: "center",
    justifyContent: "center",
  },
  tablaColDestacado: {
    backgroundColor: colors.primary + "08",
    borderRadius: 4,
  },
  tablaHeaderText: {
    fontSize: fontSize.xs,
    fontWeight: "700",
    color: colors.textPrimary,
    textAlign: "center",
  },
  tablaLabel: {
    fontSize: fontSize.xs,
    color: colors.textSecondary,
  },
  cellText: {
    fontSize: fontSize.xs,
    color: colors.textSecondary,
    textAlign: "center",
  },
});
