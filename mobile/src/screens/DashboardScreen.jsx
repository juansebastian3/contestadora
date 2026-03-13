/**
 * DashboardScreen - Pantalla principal con estadísticas y últimas llamadas
 *
 * Conectada al backend real. Si no hay llamadas aún, muestra un
 * estado vacío amigable en vez de datos fake.
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
  Image,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius, getCategoryColor, getPriorityColor } from "../utils/theme";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";

const { width } = Dimensions.get("window");

// Estado vacío cuando no hay datos aún
const EMPTY_DATA = {
  total_llamadas: 0,
  llamadas_hoy: 0,
  spam_bloqueado: 0,
  llamadas_importantes: 0,
  por_categoria: {},
  por_prioridad: {},
  ultimas_llamadas: [],
};

export default function DashboardScreen({ navigation }) {
  const { user, logout } = useAuth();
  const [data, setData] = useState(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const userName = user?.nombre?.split(" ")[0] || "Usuario";

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const result = await api.getDashboard();
      setData(result);
    } catch (e) {
      if (e.message?.includes("401") || e.message?.includes("Token")) {
        // Token expirado sin refresh posible → logout
        await logout();
        return;
      }
      setError(e.message || "No se pudieron cargar los datos");
      setData(EMPTY_DATA);
    } finally {
      setLoading(false);
    }
  }, [logout]);

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

  const hasLlamadas = data.ultimas_llamadas.length > 0;
  const hasCategorias = Object.keys(data.por_categoria).length > 0;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Cargando tu dashboard...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={{flexDirection: "row", alignItems: "center"}}>
          <Image source={require("../../assets/icon.png")} style={styles.headerLogo} resizeMode="contain" />
          <View>
            <Text style={styles.greeting}>Hola, {userName}</Text>
            <Text style={styles.subtitle}>Dora esta filtrando tus llamadas</Text>
          </View>
        </View>
        <View style={styles.statusDot}>
          <View style={[styles.dot, { backgroundColor: error ? colors.accentRed : colors.accentGreen }]} />
          <Text style={styles.statusText}>{error ? "Error" : "Activo"}</Text>
        </View>
      </View>

      {/* Error banner */}
      {error && (
        <TouchableOpacity style={styles.errorBanner} onPress={onRefresh} activeOpacity={0.7}>
          <Ionicons name="alert-circle" size={18} color={colors.accentRed} />
          <Text style={styles.errorText}>{error}</Text>
          <Text style={styles.errorRetry}>Reintentar</Text>
        </TouchableOpacity>
      )}

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
      {hasCategorias && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Distribucion</Text>
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
      )}

      {/* Últimas llamadas o estado vacío */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Ultimas llamadas</Text>
          {hasLlamadas && (
            <TouchableOpacity onPress={() => navigation?.navigate("Historial")}>
              <Text style={styles.seeAll}>Ver todo</Text>
            </TouchableOpacity>
          )}
        </View>

        {hasLlamadas ? (
          data.ultimas_llamadas.slice(0, 5).map((llamada) => (
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
          ))
        ) : (
          <View style={styles.emptyState}>
            <View style={styles.emptyIcon}>
              <Ionicons name="call-outline" size={40} color={colors.primary + "60"} />
            </View>
            <Text style={styles.emptyTitle}>Aun no hay llamadas</Text>
            <Text style={styles.emptyDesc}>
              Cuando alguien te llame y no contestes, Dora atendera y veras el resumen aqui.
            </Text>
            <TouchableOpacity
              style={styles.emptyButton}
              onPress={() => navigation?.navigate("Config")}
              activeOpacity={0.7}
            >
              <Ionicons name="settings-outline" size={16} color={colors.primary} />
              <Text style={styles.emptyButtonText}>Configurar desvio de llamadas</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  loadingContainer: { flex: 1, backgroundColor: colors.bg, justifyContent: "center", alignItems: "center" },
  loadingText: { color: colors.textMuted, marginTop: spacing.md, fontSize: fontSize.sm },
  header: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingHorizontal: spacing.lg, paddingTop: spacing.xxl + 20, paddingBottom: spacing.md,
  },
  headerLogo: { width: 40, height: 40, borderRadius: 10, marginRight: spacing.sm },
  greeting: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  subtitle: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: 2 },
  statusDot: { flexDirection: "row", alignItems: "center", backgroundColor: colors.bgCard, paddingHorizontal: 12, paddingVertical: 6, borderRadius: borderRadius.full },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 6 },
  statusText: { fontSize: fontSize.xs, color: colors.textSecondary },

  errorBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    backgroundColor: colors.accentRed + "15", marginHorizontal: spacing.lg,
    borderRadius: borderRadius.md, padding: spacing.md, marginBottom: spacing.sm,
  },
  errorText: { flex: 1, color: colors.accentRed, fontSize: fontSize.sm },
  errorRetry: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },

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

  emptyState: {
    alignItems: "center", paddingVertical: spacing.xl,
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, padding: spacing.lg,
  },
  emptyIcon: {
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: colors.primary + "10",
    justifyContent: "center", alignItems: "center", marginBottom: spacing.md,
  },
  emptyTitle: { fontSize: fontSize.lg, fontWeight: "700", color: colors.textPrimary, marginBottom: spacing.sm },
  emptyDesc: { fontSize: fontSize.sm, color: colors.textMuted, textAlign: "center", lineHeight: 20, marginBottom: spacing.lg, paddingHorizontal: spacing.md },
  emptyButton: {
    flexDirection: "row", alignItems: "center", gap: 8,
    backgroundColor: colors.primary + "15", borderRadius: borderRadius.md,
    paddingVertical: 12, paddingHorizontal: 20,
  },
  emptyButtonText: { color: colors.primary, fontSize: fontSize.sm, fontWeight: "600" },
});
