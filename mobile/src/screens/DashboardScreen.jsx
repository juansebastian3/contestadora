/**
 * DashboardScreen - Pantalla principal con estadísticas y últimas llamadas
 */
import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius, getCategoryColor, getPriorityColor } from "../utils/theme";
import api from "../services/api";

const { width } = Dimensions.get("window");

// ─── Datos de demo para previsualización ─────────────────────────
const DEMO_DATA = {
  total_llamadas: 47,
  llamadas_hoy: 5,
  spam_bloqueado: 12,
  llamadas_importantes: 28,
  por_categoria: { Personal: 15, Trabajo: 18, "Trámite": 8, Marketing: 6 },
  por_prioridad: { Alta: 8, Media: 20, Baja: 19 },
  ultimas_llamadas: [
    {
      id: 1, call_sid: "demo1", numero_origen: "+56912345678",
      fecha_inicio: new Date().toISOString(), estado: "finalizada",
      transcripcion: "", categoria: "Trabajo", prioridad: "Alta",
      resumen: "Cliente de proyecto web pidió reunión urgente para revisar avance del sprint.",
      nombre_contacto: "Carolina Méndez", whatsapp_enviado: true,
    },
    {
      id: 2, call_sid: "demo2", numero_origen: "+56987654321",
      fecha_inicio: new Date(Date.now() - 3600000).toISOString(), estado: "finalizada",
      transcripcion: "", categoria: "Personal", prioridad: "Media",
      resumen: "Tu mamá llamó para confirmar el almuerzo del domingo.",
      nombre_contacto: "Mamá", whatsapp_enviado: true,
    },
    {
      id: 3, call_sid: "demo3", numero_origen: "+56900000000",
      fecha_inicio: new Date(Date.now() - 7200000).toISOString(), estado: "finalizada",
      transcripcion: "", categoria: "Marketing", prioridad: "Baja",
      resumen: "Llamada de telemarketing ofreciendo plan de internet. Dora lo despacho.",
      nombre_contacto: null, whatsapp_enviado: true,
    },
    {
      id: 4, call_sid: "demo4", numero_origen: "+56911111111",
      fecha_inicio: new Date(Date.now() - 14400000).toISOString(), estado: "finalizada",
      transcripcion: "", categoria: "Trámite", prioridad: "Alta",
      resumen: "Isapre llamó por documentación pendiente. Plazo hasta el viernes.",
      nombre_contacto: "Isapre Cruz Blanca", whatsapp_enviado: true,
    },
  ],
};

export default function DashboardScreen({ navigation }) {
  const [data, setData] = useState(DEMO_DATA);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [isDemo, setIsDemo] = useState(true);
  const [userName, setUserName] = useState("Usuario");

  const fetchData = useCallback(async () => {
    try {
      // Cargar perfil para nombre
      const perfil = await api.getSavedProfile();
      if (perfil?.nombre) setUserName(perfil.nombre.split(" ")[0]);

      const result = await api.getDashboard();
      setData(result);
      setIsDemo(false);
    } catch (e) {
      // Usar datos demo si el backend no está disponible
      setData(DEMO_DATA);
      setIsDemo(true);
    }
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, []);

  const statCards = [
    { label: "Total", value: data.total_llamadas, icon: "call", color: colors.primary },
    { label: "Hoy", value: data.llamadas_hoy, icon: "today", color: colors.accent },
    { label: "Spam", value: data.spam_bloqueado, icon: "shield-checkmark", color: colors.accentRed },
    { label: "Importantes", value: data.llamadas_importantes, icon: "star", color: colors.accentGreen },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hola, {userName}</Text>
          <Text style={styles.subtitle}>
            {isDemo ? "Vista previa" : "Dora esta filtrando tus llamadas"}
          </Text>
        </View>
        <View style={styles.statusDot}>
          <View style={[styles.dot, { backgroundColor: isDemo ? colors.accentYellow : colors.accentGreen }]} />
          <Text style={styles.statusText}>{isDemo ? "Demo" : "Activo"}</Text>
        </View>
      </View>

      {/* Stat Cards */}
      <View style={styles.statsGrid}>
        {statCards.map((stat, i) => (
          <View key={i} style={styles.statCard}>
            <View style={[styles.statIcon, { backgroundColor: stat.color + "20" }]}>
              <Ionicons name={stat.icon} size={20} color={stat.color} />
            </View>
            <Text style={styles.statValue}>{stat.value}</Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      {/* Distribución por categoría */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Distribución</Text>
        <View style={styles.barContainer}>
          {Object.entries(data.por_categoria).map(([cat, count]) => {
            const total = Object.values(data.por_categoria).reduce((a, b) => a + b, 0);
            const pct = total > 0 ? (count / total) * 100 : 0;
            return (
              <View key={cat} style={styles.barRow}>
                <View style={styles.barLabel}>
                  <View style={[styles.barDot, { backgroundColor: getCategoryColor(cat) }]} />
                  <Text style={styles.barText}>{cat}</Text>
                </View>
                <View style={styles.barTrack}>
                  <View
                    style={[styles.barFill, {
                      width: `${pct}%`,
                      backgroundColor: getCategoryColor(cat),
                    }]}
                  />
                </View>
                <Text style={styles.barCount}>{count}</Text>
              </View>
            );
          })}
        </View>
      </View>

      {/* Últimas llamadas */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Últimas llamadas</Text>
          <TouchableOpacity onPress={() => navigation?.navigate("Historial")}>
            <Text style={styles.seeAll}>Ver todo</Text>
          </TouchableOpacity>
        </View>
        {data.ultimas_llamadas.slice(0, 5).map((llamada) => (
          <TouchableOpacity
            key={llamada.id}
            style={styles.callCard}
            onPress={() => navigation?.navigate("Historial", { llamadaId: llamada.id })}
            activeOpacity={0.7}
          >
            <View style={styles.callLeft}>
              <View style={[styles.callAvatar, { backgroundColor: getCategoryColor(llamada.categoria) + "30" }]}>
                <Ionicons
                  name={
                    llamada.categoria === "Trabajo" ? "briefcase" :
                    llamada.categoria === "Personal" ? "person" :
                    llamada.categoria === "Marketing" ? "megaphone" : "document-text"
                  }
                  size={18}
                  color={getCategoryColor(llamada.categoria)}
                />
              </View>
              <View style={styles.callInfo}>
                <Text style={styles.callName} numberOfLines={1}>
                  {llamada.nombre_contacto || llamada.numero_origen}
                </Text>
                <Text style={styles.callSummary} numberOfLines={2}>
                  {llamada.resumen}
                </Text>
              </View>
            </View>
            <View style={styles.callRight}>
              <View style={[styles.priorityBadge, { backgroundColor: getPriorityColor(llamada.prioridad) + "20" }]}>
                <Text style={[styles.priorityText, { color: getPriorityColor(llamada.prioridad) }]}>
                  {llamada.prioridad}
                </Text>
              </View>
              <Text style={styles.callTime}>
                {new Date(llamada.fecha_inicio).toLocaleTimeString("es-CL", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingHorizontal: spacing.lg, paddingTop: spacing.xxl + 20, paddingBottom: spacing.md,
  },
  greeting: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  subtitle: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: 2 },
  statusDot: { flexDirection: "row", alignItems: "center", backgroundColor: colors.bgCard, paddingHorizontal: 12, paddingVertical: 6, borderRadius: borderRadius.full },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  statusText: { fontSize: fontSize.xs, color: colors.textSecondary },
  statsGrid: {
    flexDirection: "row", flexWrap: "wrap", paddingHorizontal: spacing.md,
    gap: spacing.sm, marginBottom: spacing.md,
  },
  statCard: {
    width: (width - spacing.md * 2 - spacing.sm) / 2 - 1,
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg,
    padding: spacing.md, alignItems: "flex-start",
  },
  statIcon: { width: 36, height: 36, borderRadius: borderRadius.sm, justifyContent: "center", alignItems: "center", marginBottom: spacing.sm },
  statValue: { fontSize: fontSize.xxl, fontWeight: "800", color: colors.textPrimary },
  statLabel: { fontSize: fontSize.xs, color: colors.textSecondary, marginTop: 2 },
  section: { paddingHorizontal: spacing.lg, marginTop: spacing.lg },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  sectionTitle: { fontSize: fontSize.lg, fontWeight: "700", color: colors.textPrimary, marginBottom: spacing.md },
  seeAll: { fontSize: fontSize.sm, color: colors.primary },
  barContainer: { gap: spacing.sm },
  barRow: { flexDirection: "row", alignItems: "center" },
  barLabel: { flexDirection: "row", alignItems: "center", width: 90 },
  barDot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  barText: { fontSize: fontSize.sm, color: colors.textSecondary },
  barTrack: { flex: 1, height: 8, backgroundColor: colors.bgCardLight, borderRadius: 4, overflow: "hidden", marginHorizontal: spacing.sm },
  barFill: { height: "100%", borderRadius: 4 },
  barCount: { fontSize: fontSize.sm, fontWeight: "600", color: colors.textPrimary, width: 28, textAlign: "right" },
  callCard: {
    flexDirection: "row", justifyContent: "space-between",
    backgroundColor: colors.bgCard, borderRadius: borderRadius.md,
    padding: spacing.md, marginBottom: spacing.sm,
  },
  callLeft: { flexDirection: "row", flex: 1, marginRight: spacing.sm },
  callAvatar: { width: 40, height: 40, borderRadius: borderRadius.sm, justifyContent: "center", alignItems: "center", marginRight: spacing.sm },
  callInfo: { flex: 1 },
  callName: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary },
  callSummary: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: 2, lineHeight: 18 },
  callRight: { alignItems: "flex-end" },
  priorityBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: borderRadius.full },
  priorityText: { fontSize: fontSize.xs, fontWeight: "600" },
  callTime: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 4 },
});
