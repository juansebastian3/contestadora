/**
 * OnboardingScreen - Flujo de bienvenida para usuarios nuevos
 * Se muestra solo la primera vez despues del registro.
 * 3 pasos: Bienvenida → Cómo funciona → Configurar desvío
 */
import React, { useState, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  FlatList,
  TouchableOpacity,
  Animated,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";

const { width } = Dimensions.get("window");

const SLIDES = [
  {
    key: "bienvenida",
    icon: "shield-checkmark",
    iconColor: colors.primary,
    titulo: "Hola! Soy Dora",
    subtitulo: "Tu ContestaDora personal. Un pulpo con 8 tentaculos lista para contestar, filtrar y resumir tus llamadas.",
    puntos: [
      { icon: "call-outline", texto: "Soy tu FiltraDora: separo lo importante del spam" },
      { icon: "chatbubble-outline", texto: "Soy tu OperaDora: contesto y converso por ti" },
      { icon: "logo-whatsapp", texto: "Soy tu AvisaDora: te mando resumen al instante" },
    ],
  },
  {
    key: "como_funciona",
    icon: "git-network-outline",
    iconColor: colors.accent,
    titulo: "Como funciono?",
    subtitulo: "3 sencillos pasos y empiezo a trabajar para ti",
    pasos: [
      { numero: "1", titulo: "Conoceme 7 dias gratis", desc: "Prueba toda mi experiencia Pro sin compromiso" },
      { numero: "2", titulo: "Te asigno tu numero", desc: "Dora te da un numero de asistente dedicado" },
      { numero: "3", titulo: "Configura el desvio", desc: "Marca un codigo en tu telefono y listo, empiezo a contestar" },
    ],
  },
  {
    key: "personaliza",
    icon: "color-wand",
    iconColor: colors.accentGreen,
    titulo: "Soy tu GrabaDora",
    subtitulo: "Personalizame a tu medida. Mientras mas me conozcas, mejor te cuido.",
    features: [
      { icon: "mic-outline", color: colors.accent, titulo: "Tu voz, mi saludo", desc: "Graba un saludo con tu voz y lo uso para contestar" },
      { icon: "calendar-outline", color: colors.accentYellow, titulo: "AgendaDora", desc: "Conecto con tu calendario y se cuando estas ocupado" },
      { icon: "shield-checkmark-outline", color: colors.accentGreen, titulo: "Facil de activar", desc: "Un codigo lo activa, otro lo quita. GuardaDora de confianza" },
    ],
  },
];

export default function OnboardingScreen({ onComplete }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef(null);
  const scrollX = useRef(new Animated.Value(0)).current;

  function goToNext() {
    if (currentIndex < SLIDES.length - 1) {
      flatListRef.current?.scrollToIndex({ index: currentIndex + 1, animated: true });
    } else {
      onComplete();
    }
  }

  function goToSlide(index) {
    flatListRef.current?.scrollToIndex({ index, animated: true });
  }

  function onViewableItemsChanged({ viewableItems }) {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index);
    }
  }

  const viewabilityConfig = useRef({ viewAreaCoveragePercentThreshold: 50 }).current;
  const onViewableRef = useRef(onViewableItemsChanged);

  // ─── Render de cada slide ──────────────────────────
  function renderSlide({ item }) {
    return (
      <View style={styles.slide}>
        {/* Icono principal */}
        <View style={[styles.iconCircle, { backgroundColor: item.iconColor + "15" }]}>
          <Ionicons name={item.icon} size={56} color={item.iconColor} />
        </View>

        {/* Titulo */}
        <Text style={styles.slideTitulo}>{item.titulo}</Text>
        <Text style={styles.slideSubtitulo}>{item.subtitulo}</Text>

        {/* Contenido segun tipo de slide */}
        <View style={styles.slideContent}>
          {/* Slide 1: puntos clave */}
          {item.puntos?.map((punto, i) => (
            <View key={i} style={styles.puntoRow}>
              <View style={styles.puntoIcon}>
                <Ionicons name={punto.icon} size={20} color={colors.primary} />
              </View>
              <Text style={styles.puntoText}>{punto.texto}</Text>
            </View>
          ))}

          {/* Slide 2: pasos numerados */}
          {item.pasos?.map((paso, i) => (
            <View key={i} style={styles.pasoRow}>
              <View style={styles.pasoCircle}>
                <Text style={styles.pasoNumero}>{paso.numero}</Text>
              </View>
              <View style={styles.pasoInfo}>
                <Text style={styles.pasoTitulo}>{paso.titulo}</Text>
                <Text style={styles.pasoDesc}>{paso.desc}</Text>
              </View>
            </View>
          ))}

          {/* Slide 3: features */}
          {item.features?.map((feat, i) => (
            <View key={i} style={styles.featureCard}>
              <View style={[styles.featureIcon, { backgroundColor: feat.color + "15" }]}>
                <Ionicons name={feat.icon} size={22} color={feat.color} />
              </View>
              <View style={styles.featureInfo}>
                <Text style={styles.featureTitulo}>{feat.titulo}</Text>
                <Text style={styles.featureDesc}>{feat.desc}</Text>
              </View>
            </View>
          ))}
        </View>
      </View>
    );
  }

  const isLastSlide = currentIndex === SLIDES.length - 1;

  return (
    <View style={styles.container}>
      {/* Skip button */}
      {!isLastSlide && (
        <TouchableOpacity style={styles.skipBtn} onPress={onComplete}>
          <Text style={styles.skipText}>Saltar</Text>
        </TouchableOpacity>
      )}

      {/* Slides */}
      <FlatList
        ref={flatListRef}
        data={SLIDES}
        renderItem={renderSlide}
        keyExtractor={(item) => item.key}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        bounces={false}
        onScroll={Animated.event([{ nativeEvent: { contentOffset: { x: scrollX } } }], {
          useNativeDriver: false,
        })}
        onViewableItemsChanged={onViewableRef.current}
        viewabilityConfig={viewabilityConfig}
        getItemLayout={(_, index) => ({ length: width, offset: width * index, index })}
      />

      {/* Footer: dots + boton */}
      <View style={styles.footer}>
        {/* Dots */}
        <View style={styles.dotsContainer}>
          {SLIDES.map((_, i) => {
            const inputRange = [(i - 1) * width, i * width, (i + 1) * width];
            const dotWidth = scrollX.interpolate({
              inputRange,
              outputRange: [8, 24, 8],
              extrapolate: "clamp",
            });
            const dotOpacity = scrollX.interpolate({
              inputRange,
              outputRange: [0.3, 1, 0.3],
              extrapolate: "clamp",
            });
            return (
              <TouchableOpacity key={i} onPress={() => goToSlide(i)}>
                <Animated.View
                  style={[styles.dot, { width: dotWidth, opacity: dotOpacity }]}
                />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Boton principal */}
        <TouchableOpacity style={styles.nextBtn} onPress={goToNext} activeOpacity={0.8}>
          {isLastSlide ? (
            <Text style={styles.nextBtnText}>Empezar</Text>
          ) : (
            <>
              <Text style={styles.nextBtnText}>Siguiente</Text>
              <Ionicons name="arrow-forward" size={18} color="#fff" />
            </>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },

  skipBtn: {
    position: "absolute",
    top: spacing.xxl + 10,
    right: spacing.lg,
    zIndex: 10,
    padding: spacing.sm,
  },
  skipText: {
    color: colors.textMuted,
    fontSize: fontSize.md,
    fontWeight: "500",
  },

  // ─── Slide ─────────────────────────────────
  slide: {
    width,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl + 40,
    alignItems: "center",
  },
  iconCircle: {
    width: 110,
    height: 110,
    borderRadius: 55,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: spacing.lg,
  },
  slideTitulo: {
    fontSize: fontSize.xxl,
    fontWeight: "800",
    color: colors.textPrimary,
    textAlign: "center",
    marginBottom: spacing.sm,
  },
  slideSubtitulo: {
    fontSize: fontSize.md,
    color: colors.textMuted,
    textAlign: "center",
    lineHeight: 22,
    marginBottom: spacing.xl,
    paddingHorizontal: spacing.md,
  },

  slideContent: {
    width: "100%",
    gap: 12,
  },

  // ─── Puntos (slide 1) ─────────────────────
  puntoRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: 14,
  },
  puntoIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary + "15",
    justifyContent: "center",
    alignItems: "center",
  },
  puntoText: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: fontSize.md,
    lineHeight: 20,
  },

  // ─── Pasos (slide 2) ──────────────────────
  pasoRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 14,
    paddingVertical: 6,
  },
  pasoCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.accent,
    justifyContent: "center",
    alignItems: "center",
  },
  pasoNumero: {
    color: "#fff",
    fontSize: fontSize.lg,
    fontWeight: "800",
  },
  pasoInfo: {
    flex: 1,
    paddingTop: 2,
  },
  pasoTitulo: {
    color: colors.textPrimary,
    fontSize: fontSize.lg,
    fontWeight: "700",
    marginBottom: 2,
  },
  pasoDesc: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    lineHeight: 18,
  },

  // ─── Features (slide 3) ───────────────────
  featureCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.bgCard,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    gap: 14,
  },
  featureIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  featureInfo: {
    flex: 1,
  },
  featureTitulo: {
    color: colors.textPrimary,
    fontSize: fontSize.md,
    fontWeight: "600",
    marginBottom: 2,
  },
  featureDesc: {
    color: colors.textMuted,
    fontSize: fontSize.sm,
    lineHeight: 18,
  },

  // ─── Footer ───────────────────────────────
  footer: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
    paddingTop: spacing.md,
    alignItems: "center",
    gap: spacing.lg,
  },
  dotsContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  dot: {
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.primary,
  },
  nextBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingVertical: 16,
    paddingHorizontal: spacing.xl,
    width: "100%",
    gap: 8,
  },
  nextBtnText: {
    color: "#fff",
    fontSize: fontSize.lg,
    fontWeight: "700",
  },
});
