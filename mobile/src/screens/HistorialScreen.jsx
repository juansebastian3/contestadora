/**
 * HistorialScreen - Lista filtrable de todas las llamadas
 */
import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Modal,
  ScrollView,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius, getCategoryColor, getPriorityColor } from "../utils/theme";
import api from "../services/api";

const FILTROS_CATEGORIA = ["Todas", "Personal", "Trabajo", "Trámite", "Marketing"];
const FILTROS_PRIORIDAD = ["Todas", "Alta", "Media", "Baja"];

// Datos demo
const DEMO_LLAMADAS = [
  { id: 1, numero_origen: "+56912345678", fecha_inicio: new Date().toISOString(), estado: "finalizada", categoria: "Trabajo", prioridad: "Alta", resumen: "Cliente pidió reunión urgente para sprint review.", nombre_contacto: "Carolina Méndez", whatsapp_enviado: true, transcripcion: "[Llamante]: Hola, soy Carolina Méndez, necesito hablar con Juan Sebastián urgente.\n[Sofía]: Hola Carolina, Juan Sebastián no está disponible en este momento. ¿Puedo ayudarte?\n[Llamante]: Necesitamos una reunión urgente para revisar el sprint.\n[Sofía]: Entendido, le transmitiré tu mensaje. ¿Cuándo te vendría bien?" },
  { id: 2, numero_origen: "+56987654321", fecha_inicio: new Date(Date.now() - 3600000).toISOString(), estado: "finalizada", categoria: "Personal", prioridad: "Media", resumen: "Tu mamá confirmó almuerzo del domingo a la 1pm.", nombre_contacto: "Mamá", whatsapp_enviado: true, transcripcion: "[Llamante]: Hola Sofía, soy la mamá de Sebastián.\n[Sofía]: Hola señora, ¿cómo está?\n[Llamante]: Bien gracias, dile al Sebastián que el almuerzo del domingo es a la 1." },
  { id: 3, numero_origen: "+56900000000", fecha_inicio: new Date(Date.now() - 7200000).toISOString(), estado: "finalizada", categoria: "Marketing", prioridad: "Baja", resumen: "Telemarketing plan de internet. Despachado por Sofía.", nombre_contacto: null, whatsapp_enviado: true, transcripcion: "[Llamante]: Buenos días, le llamo de MegaNet con una oferta especial...\n[Sofía]: Gracias por llamar, pero Juan Sebastián no está interesado. Que tenga buen día." },
  { id: 4, numero_origen: "+56911111111", fecha_inicio: new Date(Date.now() - 14400000).toISOString(), estado: "finalizada", categoria: "Trámite", prioridad: "Alta", resumen: "Isapre requiere documentación. Plazo viernes.", nombre_contacto: "Isapre Cruz Blanca", whatsapp_enviado: true, transcripcion: "[Llamante]: Hola, llamo de Isapre Cruz Blanca, necesitamos documentación pendiente.\n[Sofía]: Entendido, ¿cuál es el plazo?\n[Llamante]: Hasta el viernes de esta semana." },
  { id: 5, numero_origen: "+56922222222", fecha_inicio: new Date(Date.now() - 28800000).toISOString(), estado: "finalizada", categoria: "Trabajo", prioridad: "Media", resumen: "Colega preguntó por el informe mensual.", nombre_contacto: "Pedro Soto", whatsapp_enviado: true, transcripcion: "" },
];

export default function HistorialScreen() {
  const [llamadas, setLlamadas] = useState(DEMO_LLAMADAS);
  const [filtroCategoria, setFiltroCategoria] = useState("Todas");
  const [filtroPrioridad, setFiltroPrioridad] = useState("Todas");
  const [refreshing, setRefreshing] = useState(false);
  const [selectedLlamada, setSelectedLlamada] = useState(null);

  const fetchLlamadas = useCallback(async () => {
    try {
      const params = {};
      if (filtroCategoria !== "Todas") params.categoria = filtroCategoria;
      if (filtroPrioridad !== "Todas") params.prioridad = filtroPrioridad;
      const result = await api.getLlamadas(params);
      setLlamadas(result);
    } catch (e) {
      setLlamadas(DEMO_LLAMADAS);
    }
  }, [filtroCategoria, filtroPrioridad]);

  useEffect(() => { fetchLlamadas(); }, [filtroCategoria, filtroPrioridad]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchLlamadas();
    setRefreshing(false);
  };

  const filtered = llamadas.filter((ll) => {
    if (filtroCategoria !== "Todas" && ll.categoria !== filtroCategoria) return false;
    if (filtroPrioridad !== "Todas" && ll.prioridad !== filtroPrioridad) return false;
    return true;
  });

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      activeOpacity={0.7}
      onPress={() => setSelectedLlamada(item)}
    >
      <View style={styles.cardHeader}>
        <View style={[styles.avatar, { backgroundColor: getCategoryColor(item.categoria) + "25" }]}>
          <Ionicons
            name={
              item.categoria === "Trabajo" ? "briefcase" :
              item.categoria === "Personal" ? "person" :
              item.categoria === "Marketing" ? "megaphone" : "document-text"
            }
            size={20}
            color={getCategoryColor(item.categoria)}
          />
        </View>
        <View style={styles.cardInfo}>
          <Text style={styles.cardName}>{item.nombre_contacto || item.numero_origen}</Text>
          <Text style={styles.cardTime}>
            {new Date(item.fecha_inicio).toLocaleDateString("es-CL", {
              day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
            })}
          </Text>
        </View>
        <View style={{ alignItems: "flex-end" }}>
          <View style={[styles.badge, { backgroundColor: getCategoryColor(item.categoria) + "20" }]}>
            <Text style={[styles.badgeText, { color: getCategoryColor(item.categoria) }]}>{item.categoria}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: getPriorityColor(item.prioridad) + "20", marginTop: 4 }]}>
            <Text style={[styles.badgeText, { color: getPriorityColor(item.prioridad) }]}>{item.prioridad}</Text>
          </View>
        </View>
      </View>
      <Text style={styles.cardResumen} numberOfLines={2}>{item.resumen}</Text>
      <View style={styles.cardFooter}>
        {item.whatsapp_enviado && (
          <View style={styles.whatsappBadge}>
            <Ionicons name="logo-whatsapp" size={12} color={colors.accentGreen} />
            <Text style={styles.whatsappText}>Notificado</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Historial</Text>
        <Text style={styles.count}>{filtered.length} llamadas</Text>
      </View>

      {/* Filtros Categoría */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow} contentContainerStyle={{ paddingHorizontal: spacing.lg }}>
        {FILTROS_CATEGORIA.map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterChip, filtroCategoria === f && styles.filterActive]}
            onPress={() => setFiltroCategoria(f)}
          >
            <Text style={[styles.filterText, filtroCategoria === f && styles.filterTextActive]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Filtros Prioridad */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow} contentContainerStyle={{ paddingHorizontal: spacing.lg }}>
        {FILTROS_PRIORIDAD.map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterChip, filtroPrioridad === f && styles.filterActive]}
            onPress={() => setFiltroPrioridad(f)}
          >
            {f !== "Todas" && <View style={[styles.priDot, { backgroundColor: getPriorityColor(f) }]} />}
            <Text style={[styles.filterText, filtroPrioridad === f && styles.filterTextActive]}>{f}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Lista */}
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 100 }}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="call-outline" size={48} color={colors.textMuted} />
            <Text style={styles.emptyText}>No hay llamadas con estos filtros</Text>
          </View>
        }
      />

      {/* Modal Detalle */}
      <Modal visible={!!selectedLlamada} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHandle} />
            {selectedLlamada && (
              <ScrollView>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>{selectedLlamada.nombre_contacto || selectedLlamada.numero_origen}</Text>
                  <TouchableOpacity onPress={() => setSelectedLlamada(null)}>
                    <Ionicons name="close-circle" size={28} color={colors.textMuted} />
                  </TouchableOpacity>
                </View>
                <Text style={styles.modalPhone}>{selectedLlamada.numero_origen}</Text>

                <View style={styles.modalBadges}>
                  <View style={[styles.badge, { backgroundColor: getCategoryColor(selectedLlamada.categoria) + "20" }]}>
                    <Text style={[styles.badgeText, { color: getCategoryColor(selectedLlamada.categoria) }]}>{selectedLlamada.categoria}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: getPriorityColor(selectedLlamada.prioridad) + "20", marginLeft: 8 }]}>
                    <Text style={[styles.badgeText, { color: getPriorityColor(selectedLlamada.prioridad) }]}>Prioridad {selectedLlamada.prioridad}</Text>
                  </View>
                </View>

                <Text style={styles.modalSectionTitle}>Resumen</Text>
                <Text style={styles.modalText}>{selectedLlamada.resumen}</Text>

                {selectedLlamada.transcripcion ? (
                  <>
                    <Text style={styles.modalSectionTitle}>Transcripción</Text>
                    <View style={styles.transcriptionBox}>
                      <Text style={styles.transcriptionText}>{selectedLlamada.transcripcion}</Text>
                    </View>
                  </>
                ) : null}

                <Text style={styles.modalDate}>
                  {new Date(selectedLlamada.fecha_inicio).toLocaleDateString("es-CL", {
                    weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit",
                  })}
                </Text>
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "baseline", paddingHorizontal: spacing.lg, paddingTop: spacing.xxl + 20, paddingBottom: spacing.sm },
  title: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  count: { fontSize: fontSize.sm, color: colors.textMuted },
  filterRow: { marginBottom: spacing.sm, maxHeight: 40 },
  filterChip: { flexDirection: "row", alignItems: "center", backgroundColor: colors.bgCard, paddingHorizontal: 14, paddingVertical: 6, borderRadius: borderRadius.full, marginRight: spacing.sm },
  filterActive: { backgroundColor: colors.primary },
  filterText: { fontSize: fontSize.sm, color: colors.textSecondary },
  filterTextActive: { color: colors.textPrimary, fontWeight: "600" },
  priDot: { width: 6, height: 6, borderRadius: 3, marginRight: 4 },
  card: { backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: spacing.sm },
  cardHeader: { flexDirection: "row", alignItems: "center" },
  avatar: { width: 44, height: 44, borderRadius: borderRadius.md, justifyContent: "center", alignItems: "center", marginRight: spacing.sm },
  cardInfo: { flex: 1 },
  cardName: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary },
  cardTime: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: borderRadius.full },
  badgeText: { fontSize: fontSize.xs, fontWeight: "600" },
  cardResumen: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: spacing.sm, lineHeight: 20 },
  cardFooter: { flexDirection: "row", marginTop: spacing.sm },
  whatsappBadge: { flexDirection: "row", alignItems: "center" },
  whatsappText: { fontSize: fontSize.xs, color: colors.accentGreen, marginLeft: 4 },
  empty: { alignItems: "center", marginTop: spacing.xxl * 2 },
  emptyText: { fontSize: fontSize.md, color: colors.textMuted, marginTop: spacing.md },
  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.6)", justifyContent: "flex-end" },
  modalContent: { backgroundColor: colors.bgCard, borderTopLeftRadius: borderRadius.xl, borderTopRightRadius: borderRadius.xl, padding: spacing.lg, maxHeight: "85%" },
  modalHandle: { width: 40, height: 4, backgroundColor: colors.textMuted, borderRadius: 2, alignSelf: "center", marginBottom: spacing.md },
  modalHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  modalTitle: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  modalPhone: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: 4, marginBottom: spacing.md },
  modalBadges: { flexDirection: "row", marginBottom: spacing.lg },
  modalSectionTitle: { fontSize: fontSize.md, fontWeight: "600", color: colors.primary, marginBottom: spacing.sm, marginTop: spacing.md },
  modalText: { fontSize: fontSize.md, color: colors.textSecondary, lineHeight: 22 },
  transcriptionBox: { backgroundColor: colors.bg, borderRadius: borderRadius.md, padding: spacing.md },
  transcriptionText: { fontSize: fontSize.sm, color: colors.textSecondary, lineHeight: 20, fontFamily: "monospace" },
  modalDate: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: spacing.lg, textAlign: "center" },
});
