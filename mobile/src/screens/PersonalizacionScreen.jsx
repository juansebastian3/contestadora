/**
 * PersonalizacionScreen - Pantalla de personalización del asistente
 *
 * Permite al usuario:
 * 1. Elegir modo de asistente (Asistente Básico / Contestadora / Agente IA)
 * 2. Escribir un prompt personalizado para la IA
 * 3. Grabar audio de saludo con expo-av para modo contestadora/agente IA
 */
import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Animated,
} from "react-native";
import { Audio } from "expo-av";
import api from "../services/api";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";

const MODOS = [
  {
    key: "asistente_basico",
    titulo: "Asistente Basico",
    icono: "📞",
    descripcion: "La IA saluda con voz Polly, escucha el recado y te envia un resumen. Plan Free.",
    requiereAudio: false,
    planMinimo: "free",
  },
  {
    key: "contestadora",
    titulo: "Contestadora Personal",
    icono: "🎙️",
    descripcion: "Tu voz grabada como saludo para conocidos. Polly saluda a desconocidos. La IA solo escucha.",
    requiereAudio: true,
    planMinimo: "pro",
  },
  {
    key: "agente_ia",
    titulo: "Agente IA",
    icono: "🤖",
    descripcion: "Tu voz grabada como saludo + la IA conversa como tu agente personal. Agenda, calendario y mas.",
    requiereAudio: true,
    planMinimo: "premium",
  },
];

const MAX_PROMPT_LENGTH = 2000;

export default function PersonalizacionScreen() {
  // Estado general
  const [modoActual, setModoActual] = useState("asistente_basico");
  const [prompt, setPrompt] = useState("");
  const [promptOriginal, setPromptOriginal] = useState("");
  const [tieneAudio, setTieneAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  const [cargando, setCargando] = useState(true);
  const [guardandoPrompt, setGuardandoPrompt] = useState(false);
  const [guardandoModo, setGuardandoModo] = useState(false);

  // Estado de grabación (expo-av)
  const [grabando, setGrabando] = useState(false);
  const [subiendoAudio, setSubiendoAudio] = useState(false);
  const [duracionGrabacion, setDuracionGrabacion] = useState(0);
  const recordingRef = useRef(null);
  const soundRef = useRef(null);
  const timerRef = useRef(null);

  // Animación pulso
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    cargarPersonalizacion();
    return () => {
      // Limpiar al desmontar
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(() => {});
      }
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(() => {});
      }
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    if (grabando) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.3, duration: 600, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    }
  }, [grabando]);

  async function cargarPersonalizacion() {
    try {
      const data = await api.getPersonalizacion();
      setModoActual(data.modo_asistente || "asistente_basico");
      setPrompt(data.prompt_personalizado || "");
      setPromptOriginal(data.prompt_personalizado || "");
      setTieneAudio(!!data.audio_saludo_url);
      setAudioUrl(data.audio_saludo_url);
    } catch (e) {
      console.log("Error cargando personalización:", e);
    } finally {
      setCargando(false);
    }
  }

  // ─── PROMPT ───────────────────────────────────────────────

  async function guardarPrompt() {
    if (prompt.trim() === promptOriginal) return;
    setGuardandoPrompt(true);
    try {
      if (prompt.trim()) {
        await api.guardarPrompt(prompt.trim());
      } else {
        await api.borrarPrompt();
      }
      setPromptOriginal(prompt.trim());
      Alert.alert("Listo", "Tu prompt se guardó correctamente.");
    } catch (e) {
      Alert.alert("Error", e.message || "No se pudo guardar el prompt.");
    } finally {
      setGuardandoPrompt(false);
    }
  }

  // ─── MODO ─────────────────────────────────────────────────

  async function cambiarModo(nuevoModo) {
    if (nuevoModo === modoActual) return;
    const modo = MODOS.find((m) => m.key === nuevoModo);
    if (modo.requiereAudio && !tieneAudio) {
      Alert.alert("Audio requerido", "Primero graba un audio de saludo.", [{ text: "Entendido" }]);
      return;
    }
    setGuardandoModo(true);
    try {
      await api.cambiarModoAsistente(nuevoModo);
      setModoActual(nuevoModo);
    } catch (e) {
      Alert.alert("Error", e.message || "No se pudo cambiar el modo.");
    } finally {
      setGuardandoModo(false);
    }
  }

  // ─── GRABACIÓN CON EXPO-AV ────────────────────────────────

  async function iniciarGrabacion() {
    try {
      // Pedir permiso de micrófono
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== "granted") {
        Alert.alert("Permiso requerido", "Necesitamos acceso al micrófono para grabar tu saludo.");
        return;
      }

      // Configurar modo de audio
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Crear y empezar grabación
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      await recording.startAsync();
      recordingRef.current = recording;
      setGrabando(true);
      setDuracionGrabacion(0);

      // Timer para mostrar duración
      timerRef.current = setInterval(() => {
        setDuracionGrabacion((d) => {
          if (d >= 59) {
            // Auto-detener a los 60 segundos
            detenerGrabacion();
            return 60;
          }
          return d + 1;
        });
      }, 1000);
    } catch (e) {
      Alert.alert("Error", "No se pudo iniciar la grabación: " + e.message);
    }
  }

  async function detenerGrabacion() {
    if (!recordingRef.current) return;

    try {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      setGrabando(false);
      setSubiendoAudio(true);

      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;

      // Restaurar modo de audio
      await Audio.setAudioModeAsync({ allowsRecordingIOS: false });

      if (!uri) {
        Alert.alert("Error", "No se obtuvo el archivo de audio.");
        setSubiendoAudio(false);
        return;
      }

      // Subir al backend
      const result = await api.subirAudioSaludo(uri, "saludo.m4a", "audio/m4a");
      setTieneAudio(true);
      setAudioUrl(result.audio_url);
      Alert.alert("Audio guardado", "Tu saludo se subió correctamente.");
    } catch (e) {
      Alert.alert("Error", "No se pudo guardar el audio: " + e.message);
    } finally {
      setSubiendoAudio(false);
    }
  }

  async function reproducirAudio() {
    if (!audioUrl) return;
    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
      }
      const { sound } = await Audio.Sound.createAsync({ uri: audioUrl });
      soundRef.current = sound;
      await sound.playAsync();
    } catch (e) {
      Alert.alert("Error", "No se pudo reproducir el audio.");
    }
  }

  async function eliminarAudio() {
    Alert.alert(
      "Eliminar audio",
      "Si estas en modo contestadora o Agente IA, volveras a asistente basico.",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Eliminar",
          style: "destructive",
          onPress: async () => {
            try {
              const result = await api.borrarAudioSaludo();
              setTieneAudio(false);
              setAudioUrl(null);
              setModoActual(result.modo_asistente || "asistente_basico");
            } catch (e) {
              Alert.alert("Error", e.message);
            }
          },
        },
      ]
    );
  }

  function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  }

  // ─── RENDER ───────────────────────────────────────────────

  const promptModificado = prompt.trim() !== promptOriginal;

  if (cargando) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.cargandoText}>Cargando personalización...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.titulo}>Personaliza tu asistente</Text>
      <Text style={styles.subtitulo}>Configura cómo se comporta cuando alguien te llama</Text>

      {/* ═══ MODO DE ASISTENTE ═══ */}
      <View style={styles.seccion}>
        <Text style={styles.seccionTitulo}>Modo de asistente</Text>
        {MODOS.map((modo) => {
          const activo = modoActual === modo.key;
          const bloqueado = modo.requiereAudio && !tieneAudio;
          return (
            <TouchableOpacity
              key={modo.key}
              style={[styles.modoCard, activo && styles.modoCardActivo, bloqueado && styles.modoCardBloqueado]}
              onPress={() => cambiarModo(modo.key)}
              disabled={guardandoModo}
              activeOpacity={0.7}
            >
              <View style={styles.modoHeader}>
                <Text style={styles.modoIcono}>{modo.icono}</Text>
                <Text style={[styles.modoTitulo, activo && styles.modoTituloActivo]}>{modo.titulo}</Text>
                {activo && <View style={styles.activoBadge}><Text style={styles.activoBadgeText}>Activo</Text></View>}
                {bloqueado && <Text style={styles.lockIcon}>🔒</Text>}
              </View>
              <Text style={[styles.modoDesc, activo && styles.modoDescActivo]}>{modo.descripcion}</Text>
              {bloqueado && <Text style={styles.requiereAudioText}>Requiere audio de saludo grabado</Text>}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* ═══ PROMPT PERSONALIZADO ═══ */}
      <View style={styles.seccion}>
        <Text style={styles.seccionTitulo}>Prompt personalizado</Text>
        <Text style={styles.seccionDesc}>
          Escribe instrucciones para que la IA sepa cómo comportarse cuando conteste tus llamadas.
        </Text>
        <View style={styles.promptContainer}>
          <TextInput
            style={styles.promptInput}
            multiline
            numberOfLines={6}
            maxLength={MAX_PROMPT_LENGTH}
            placeholder="Ejemplo: Soy diseñador freelance. Si llaman por trabajo, pregunta por el tipo de proyecto, presupuesto y plazo."
            placeholderTextColor={colors.textMuted}
            value={prompt}
            onChangeText={setPrompt}
            textAlignVertical="top"
          />
          <Text style={styles.promptCounter}>{prompt.length}/{MAX_PROMPT_LENGTH}</Text>
        </View>
        <TouchableOpacity
          style={[styles.botonGuardar, !promptModificado && styles.botonGuardarDisabled]}
          onPress={guardarPrompt}
          disabled={!promptModificado || guardandoPrompt}
        >
          {guardandoPrompt ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.botonGuardarText}>{promptModificado ? "Guardar prompt" : "Sin cambios"}</Text>
          )}
        </TouchableOpacity>
        {promptOriginal ? (
          <TouchableOpacity style={styles.botonBorrarPrompt} onPress={() => setPrompt("")}>
            <Text style={styles.botonBorrarPromptText}>Borrar prompt</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* ═══ AUDIO DE SALUDO ═══ */}
      <View style={styles.seccion}>
        <Text style={styles.seccionTitulo}>Audio de saludo</Text>
        <Text style={styles.seccionDesc}>
          Graba tu propio saludo. Se usa en los modos Contestadora y Agente IA.
        </Text>

        {subiendoAudio ? (
          <View style={styles.grabandoContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.grabandoTexto}>Subiendo audio...</Text>
          </View>
        ) : tieneAudio ? (
          <View style={styles.audioExistente}>
            <TouchableOpacity style={styles.audioInfo} onPress={reproducirAudio}>
              <Text style={styles.audioIcono}>🎙️</Text>
              <View>
                <Text style={styles.audioTexto}>Audio guardado</Text>
                <Text style={styles.audioSubtexto}>Toca para reproducir</Text>
              </View>
            </TouchableOpacity>
            <View style={styles.audioAcciones}>
              <TouchableOpacity style={styles.botonRegrabar} onPress={iniciarGrabacion}>
                <Text style={styles.botonRegrabarText}>Regrabar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.botonEliminarAudio} onPress={eliminarAudio}>
                <Text style={styles.botonEliminarAudioText}>Eliminar</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : grabando ? (
          <View style={styles.grabandoContainer}>
            <Animated.View style={[styles.grabandoCircle, { transform: [{ scale: pulseAnim }] }]}>
              <Text style={styles.grabandoIcono}>🔴</Text>
            </Animated.View>
            <Text style={styles.grabandoTexto}>Grabando...</Text>
            <Text style={styles.grabandoTimer}>{formatTime(duracionGrabacion)}</Text>
            <Text style={styles.grabandoSub}>Habla tu saludo ahora (máx. 60s)</Text>
            <TouchableOpacity style={styles.botonDetener} onPress={detenerGrabacion}>
              <Text style={styles.botonDetenerText}>Detener y guardar</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity style={styles.botonGrabar} onPress={iniciarGrabacion}>
            <Text style={styles.botonGrabarIcono}>🎤</Text>
            <Text style={styles.botonGrabarText}>Grabar mi saludo</Text>
            <Text style={styles.botonGrabarSub}>Máximo 60 segundos</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: spacing.lg, paddingTop: spacing.xxl + 12 },
  centered: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.bg },
  cargandoText: { color: colors.textMuted, marginTop: 12, fontSize: fontSize.sm },

  titulo: { fontSize: fontSize.hero - 8, fontWeight: "800", color: colors.textPrimary, marginBottom: 4 },
  subtitulo: { fontSize: fontSize.sm, color: colors.textMuted, marginBottom: spacing.lg },

  seccion: { marginBottom: 28 },
  seccionTitulo: { fontSize: fontSize.lg, fontWeight: "700", color: colors.textPrimary, marginBottom: 4 },
  seccionDesc: { fontSize: fontSize.sm, color: colors.textSecondary, marginBottom: 14, lineHeight: 18 },

  modoCard: { backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, padding: spacing.md, marginBottom: 10, borderWidth: 2, borderColor: "transparent" },
  modoCardActivo: { borderColor: colors.primary, backgroundColor: colors.bgCardLight },
  modoCardBloqueado: { opacity: 0.55 },
  modoHeader: { flexDirection: "row", alignItems: "center", marginBottom: 6 },
  modoIcono: { fontSize: 22, marginRight: 10 },
  modoTitulo: { fontSize: fontSize.md, fontWeight: "700", color: colors.textSecondary, flex: 1 },
  modoTituloActivo: { color: colors.textPrimary },
  modoDesc: { fontSize: fontSize.sm, color: colors.textSecondary, lineHeight: 18, marginLeft: 32 },
  modoDescActivo: { color: colors.primaryLight },
  activoBadge: { backgroundColor: colors.primary, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  activoBadgeText: { color: "#fff", fontSize: fontSize.xs, fontWeight: "700" },
  lockIcon: { fontSize: 16, marginLeft: 8 },
  requiereAudioText: { fontSize: fontSize.xs, color: colors.accentRed, marginTop: 6, marginLeft: 32 },

  promptContainer: { backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, padding: 14, marginBottom: 12 },
  promptInput: { color: colors.textPrimary, fontSize: fontSize.md, minHeight: 120, lineHeight: 22 },
  promptCounter: { textAlign: "right", color: colors.textMuted, fontSize: fontSize.xs, marginTop: 4 },
  botonGuardar: { backgroundColor: colors.primary, borderRadius: borderRadius.md, paddingVertical: 14, alignItems: "center" },
  botonGuardarDisabled: { backgroundColor: colors.bgCardLight, opacity: 0.6 },
  botonGuardarText: { color: "#fff", fontSize: fontSize.md, fontWeight: "700" },
  botonBorrarPrompt: { alignItems: "center", marginTop: 10 },
  botonBorrarPromptText: { color: colors.accentRed, fontSize: fontSize.sm },

  audioExistente: { backgroundColor: "#1A2E1A", borderRadius: borderRadius.lg, padding: spacing.md, borderWidth: 1, borderColor: "#2D5A2D" },
  audioInfo: { flexDirection: "row", alignItems: "center", marginBottom: 12 },
  audioIcono: { fontSize: 28, marginRight: 12 },
  audioTexto: { color: colors.accentGreen, fontSize: fontSize.md, fontWeight: "600" },
  audioSubtexto: { color: "#6B8F6B", fontSize: fontSize.xs },
  audioAcciones: { flexDirection: "row", gap: 10 },
  botonRegrabar: { flex: 1, backgroundColor: colors.bgCardLight, borderRadius: borderRadius.sm, paddingVertical: 10, alignItems: "center" },
  botonRegrabarText: { color: colors.accent, fontSize: fontSize.sm, fontWeight: "600" },
  botonEliminarAudio: { flex: 1, backgroundColor: "#3A2020", borderRadius: borderRadius.sm, paddingVertical: 10, alignItems: "center" },
  botonEliminarAudioText: { color: colors.accentRed, fontSize: fontSize.sm, fontWeight: "600" },

  grabandoContainer: { alignItems: "center", paddingVertical: 30 },
  grabandoCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: "#3A1A1A", justifyContent: "center", alignItems: "center", marginBottom: 16 },
  grabandoIcono: { fontSize: 36 },
  grabandoTexto: { color: colors.accentRed, fontSize: fontSize.lg, fontWeight: "700" },
  grabandoTimer: { color: colors.textPrimary, fontSize: fontSize.xxl, fontWeight: "800", marginTop: 4 },
  grabandoSub: { color: colors.textMuted, fontSize: fontSize.sm, marginTop: 4 },
  botonDetener: { marginTop: 20, backgroundColor: colors.accentRed, borderRadius: borderRadius.md, paddingVertical: 12, paddingHorizontal: 30 },
  botonDetenerText: { color: "#fff", fontSize: fontSize.md, fontWeight: "700" },

  botonGrabar: { backgroundColor: colors.bgCard, borderRadius: borderRadius.lg, padding: 24, alignItems: "center", borderWidth: 2, borderColor: colors.border, borderStyle: "dashed" },
  botonGrabarIcono: { fontSize: 40, marginBottom: 8 },
  botonGrabarText: { color: colors.textPrimary, fontSize: fontSize.md, fontWeight: "600" },
  botonGrabarSub: { color: colors.textMuted, fontSize: fontSize.xs, marginTop: 4 },
});
