/**
 * RegistroScreen - Pantalla de creación de cuenta
 */
import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, spacing, fontSize, borderRadius } from "../utils/theme";
import api from "../services/api";

export default function RegistroScreen({ navigation, onAuthSuccess }) {
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [telefono, setTelefono] = useState("+56");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleRegistro() {
    if (!nombre.trim() || !email.trim() || !telefono.trim() || !password) {
      Alert.alert("Campos requeridos", "Completa todos los campos.");
      return;
    }
    if (password.length < 6) {
      Alert.alert("Contraseña corta", "La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert("Error", "Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      const data = await api.registro(
        nombre.trim(),
        email.trim().toLowerCase(),
        telefono.trim(),
        password
      );
      if (onAuthSuccess) onAuthSuccess(data.perfil);
    } catch (e) {
      Alert.alert("Error", e.message || "No se pudo crear la cuenta.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.title}>Crear cuenta</Text>
          <Text style={styles.subtitle}>Configura tu asistente en 1 minuto</Text>
        </View>

        {/* Formulario */}
        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Ionicons name="person-outline" size={20} color={colors.textMuted} style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Tu nombre"
              placeholderTextColor={colors.textMuted}
              value={nombre}
              onChangeText={setNombre}
              autoCapitalize="words"
            />
          </View>

          <View style={styles.inputContainer}>
            <Ionicons name="mail-outline" size={20} color={colors.textMuted} style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Email"
              placeholderTextColor={colors.textMuted}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.inputContainer}>
            <Ionicons name="call-outline" size={20} color={colors.textMuted} style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Teléfono (+56...)"
              placeholderTextColor={colors.textMuted}
              value={telefono}
              onChangeText={setTelefono}
              keyboardType="phone-pad"
            />
          </View>

          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed-outline" size={20} color={colors.textMuted} style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Contraseña (mín. 6 caracteres)"
              placeholderTextColor={colors.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeButton}>
              <Ionicons name={showPassword ? "eye-off-outline" : "eye-outline"} size={20} color={colors.textMuted} />
            </TouchableOpacity>
          </View>

          <View style={styles.inputContainer}>
            <Ionicons name="checkmark-circle-outline" size={20} color={colors.textMuted} style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Confirmar contraseña"
              placeholderTextColor={colors.textMuted}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showPassword}
            />
          </View>

          <TouchableOpacity
            style={[styles.registerButton, loading && styles.registerButtonDisabled]}
            onPress={handleRegistro}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.registerButtonText}>Crear cuenta</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Texto legal */}
        <Text style={styles.legalText}>
          Al crear tu cuenta aceptas nuestros Términos de Servicio y Política de Privacidad.
        </Text>

        {/* Link a login */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>¿Ya tienes cuenta? </Text>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.footerLink}>Iniciar sesión</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { flexGrow: 1, padding: spacing.lg, paddingTop: spacing.xxl },

  header: { marginBottom: 30 },
  backButton: { marginBottom: spacing.md },
  title: { fontSize: fontSize.hero, fontWeight: "800", color: colors.textPrimary },
  subtitle: { fontSize: fontSize.md, color: colors.textMuted, marginTop: 4 },

  form: { gap: 14 },
  inputContainer: {
    flexDirection: "row", alignItems: "center",
    backgroundColor: colors.bgCard, borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md, height: 54,
    borderWidth: 1, borderColor: colors.border,
  },
  inputIcon: { marginRight: spacing.sm },
  input: { flex: 1, color: colors.textPrimary, fontSize: fontSize.md },
  eyeButton: { padding: 4 },

  registerButton: {
    backgroundColor: colors.primary, borderRadius: borderRadius.md,
    height: 54, justifyContent: "center", alignItems: "center",
    marginTop: spacing.sm,
  },
  registerButtonDisabled: { opacity: 0.6 },
  registerButtonText: { color: "#fff", fontSize: fontSize.lg, fontWeight: "700" },

  legalText: {
    fontSize: fontSize.xs, color: colors.textMuted, textAlign: "center",
    marginTop: spacing.lg, lineHeight: 16, paddingHorizontal: spacing.lg,
  },

  footer: { flexDirection: "row", justifyContent: "center", marginTop: spacing.lg },
  footerText: { color: colors.textMuted, fontSize: fontSize.md },
  footerLink: { color: colors.primary, fontSize: fontSize.md, fontWeight: "600" },
});
