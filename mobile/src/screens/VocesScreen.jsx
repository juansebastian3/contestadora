/**
 * VocesScreen - Catálogo de voces con selector por plan
 */
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";
import api from "../services/api";

const DEMO_VOCES = [
  { id: 1, nombre: "Mia", descripcion: "Femenina, español neutro latinoamericano", genero: "femenino", tipo: "polly", plan_minimo: "free", es_premium: false },
  { id: 2, nombre: "Conchita", descripcion: "Femenina, español castellano cálido", genero: "femenino", tipo: "polly", plan_minimo: "free", es_premium: false },
  { id: 3, nombre: "Lupe", descripcion: "Femenina, español mexicano amigable", genero: "femenino", tipo: "polly", plan_minimo: "free", es_premium: false },
  { id: 4, nombre: "Miguel", descripcion: "Masculina, español neutro profesional", genero: "masculino", tipo: "polly", plan_minimo: "free", es_premium: false },
  { id: 5, nombre: "Andrés", descripcion: "Masculina, español mexicano formal", genero: "masculino", tipo: "polly", plan_minimo: "free", es_premium: false },
  { id: 10, nombre: "Valentina", descripcion: "IA ultra-realista femenina, natural y cálida", genero: "femenino", tipo: "elevenlabs", plan_minimo: "pro", es_premium: true },
  { id: 11, nombre: "Mateo", descripcion: "IA ultra-realista masculina, profesional", genero: "masculino", tipo: "elevenlabs", plan_minimo: "pro", es_premium: true },
  { id: 12, nombre: "Isabella", descripcion: "IA premium femenina, elegante y sofisticada", genero: "femenino", tipo: "elevenlabs", plan_minimo: "pro", es_premium: true },
];

export default function VocesScreen() {
  const [voces, setVoces] = useState(DEMO_VOCES);
  const [selected, setSelected] = useState(1);
  const [userPlan, setUserPlan] = useState("free"); // demo

  useEffect(() => {
    api.get("/api/v1/voces").then(setVoces).catch(() => setVoces(DEMO_VOCES));
  }, []);

  const vocesGratis = voces.filter((v) => !v.es_premium);
  const vocesPremium = voces.filter((v) => v.es_premium);

  const canSelect = (voz) => {
    const orden = { free: 0, pro: 1, premium: 2 };
    return orden[userPlan] >= orden[voz.plan_minimo];
  };

  const VoiceCard = ({ voz }) => {
    const isSelected = selected === voz.id;
    const locked = !canSelect(voz);

    return (
      <TouchableOpacity
        style={[
          styles.voiceCard,
          isSelected && styles.voiceCardSelected,
          locked && styles.voiceCardLocked,
        ]}
        activeOpacity={0.7}
        onPress={() => !locked && setSelected(voz.id)}
      >
        <View style={styles.voiceTop}>
          <View style={[styles.voiceAvatar, {
            backgroundColor: voz.genero === "femenino" ? colors.primary + "25" : colors.accent + "25"
          }]}>
            <Ionicons
              name={voz.genero === "femenino" ? "woman" : "man"}
              size={20}
              color={voz.genero === "femenino" ? colors.primary : colors.accent}
            />
          </View>
          {isSelected && (
            <View style={styles.checkmark}>
              <Ionicons name="checkmark-circle" size={22} color={colors.accentGreen} />
            </View>
          )}
          {locked && (
            <View style={styles.lockBadge}>
              <Ionicons name="lock-closed" size={12} color={colors.accentYellow} />
            </View>
          )}
        </View>
        <Text style={styles.voiceName}>{voz.nombre}</Text>
        <Text style={styles.voiceDesc} numberOfLines={2}>{voz.descripcion}</Text>
        {voz.es_premium && (
          <View style={styles.premiumBadge}>
            <Ionicons name="diamond" size={10} color={colors.primary} />
            <Text style={styles.premiumText}>ElevenLabs</Text>
          </View>
        )}
        <TouchableOpacity style={styles.playBtn}>
          <Ionicons name="play-circle" size={28} color={locked ? colors.textMuted : colors.primary} />
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Voces</Text>
        <Text style={styles.subtitle}>Elige cómo suena tu asistente</Text>
      </View>

      {/* Voces Estándar */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Estándar</Text>
          <View style={styles.freeBadge}>
            <Text style={styles.freeText}>Gratis</Text>
          </View>
        </View>
        <View style={styles.voicesGrid}>
          {vocesGratis.map((v) => <VoiceCard key={v.id} voz={v} />)}
        </View>
      </View>

      {/* Voces Premium */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Ultra-realistas</Text>
          <View style={[styles.freeBadge, { backgroundColor: colors.primary + "20" }]}>
            <Ionicons name="diamond" size={10} color={colors.primary} />
            <Text style={[styles.freeText, { color: colors.primary, marginLeft: 4 }]}>Pro</Text>
          </View>
        </View>
        <Text style={styles.premiumDesc}>
          Voces de IA generadas por ElevenLabs. Suenan indistinguibles de una persona real.
        </Text>
        <View style={styles.voicesGrid}>
          {vocesPremium.map((v) => <VoiceCard key={v.id} voz={v} />)}
        </View>
      </View>

      {/* Voz personalizada */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.customCard}>
          <View style={styles.customLeft}>
            <View style={[styles.voiceAvatar, { backgroundColor: colors.accentYellow + "20" }]}>
              <Ionicons name="mic" size={20} color={colors.accentYellow} />
            </View>
            <View>
              <Text style={styles.customTitle}>Clona tu voz</Text>
              <Text style={styles.customDesc}>Graba 30 segundos y crea una voz idéntica a la tuya</Text>
            </View>
          </View>
          <View style={[styles.freeBadge, { backgroundColor: colors.accentYellow + "20" }]}>
            <Text style={[styles.freeText, { color: colors.accentYellow }]}>Premium</Text>
          </View>
        </TouchableOpacity>
      </View>

      <View style={{ height: 120 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.xxl + 20, paddingBottom: spacing.sm },
  title: { fontSize: fontSize.xl, fontWeight: "700", color: colors.textPrimary },
  subtitle: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: 2 },
  section: { paddingHorizontal: spacing.lg, marginTop: spacing.lg },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.sm },
  sectionTitle: { fontSize: fontSize.lg, fontWeight: "700", color: colors.textPrimary },
  freeBadge: { flexDirection: "row", alignItems: "center", backgroundColor: colors.accentGreen + "20", paddingHorizontal: 10, paddingVertical: 3, borderRadius: borderRadius.full },
  freeText: { fontSize: fontSize.xs, fontWeight: "600", color: colors.accentGreen },
  premiumDesc: { fontSize: fontSize.sm, color: colors.textSecondary, marginBottom: spacing.md, lineHeight: 20 },
  voicesGrid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  voiceCard: {
    width: "48%", backgroundColor: colors.bgCard, borderRadius: borderRadius.lg,
    padding: spacing.md, borderWidth: 2, borderColor: "transparent",
  },
  voiceCardSelected: { borderColor: colors.primary },
  voiceCardLocked: { opacity: 0.5 },
  voiceTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.sm },
  voiceAvatar: { width: 40, height: 40, borderRadius: borderRadius.md, justifyContent: "center", alignItems: "center" },
  checkmark: {},
  lockBadge: {},
  voiceName: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary },
  voiceDesc: { fontSize: fontSize.xs, color: colors.textSecondary, marginTop: 2, lineHeight: 16 },
  premiumBadge: { flexDirection: "row", alignItems: "center", marginTop: spacing.sm },
  premiumText: { fontSize: fontSize.xs, color: colors.primary, marginLeft: 4 },
  playBtn: { alignSelf: "flex-end", marginTop: spacing.sm },
  customCard: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, padding: spacing.md,
    borderWidth: 1, borderColor: colors.accentYellow + "30", borderStyle: "dashed",
  },
  customLeft: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flex: 1 },
  customTitle: { fontSize: fontSize.md, fontWeight: "600", color: colors.textPrimary },
  customDesc: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2, maxWidth: 200 },
});
