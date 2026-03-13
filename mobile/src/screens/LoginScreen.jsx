/**
 * LoginScreen - Pantalla de inicio de sesión
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

export default function LoginScreen({ navigation, onAuthSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email.trim() || !password) {
      Alert.alert("Campos requeridos", "Ingresa tu email y contraseña.");
      return;
    }

    setLoading(true);
    try {
      const data = await api.login(email.trim().toLowerCase(), password);
      if (onAuthSuccess) onAuthSuccess(data.perfil);
    } catch (e) {
      Alert.alert("Error", e.message || "No se pudo iniciar sesión.");
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
        {/* Logo y nombre */}
        <View style={styles.logoContainer}>
          <View style={styles.logoCircle}>
            <Ionicons name="shield-checkmark" size={48} color={colors.primary} />
          </View>
          <Text style={styles.appName}><Text style={{fontWeight: "300"}}>Contesta</Text><Text style={{fontWeight: "800"}}>Dora</Text></Text>
          <Text style={styles.tagline}>Dora contesta, tu decides</Text>
        </View>

        {/* Formulario */}
        <View style={styles.form}>
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
            <Ionicons name="lock-closed-outline" size={20} color={colors.textMuted} style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Contraseña"
              placeholderTextColor={colors.textMuted}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeButton}>
              <Ionicons name={showPassword ? "eye-off-outline" : "eye-outline"} size={20} color={colors.textMuted} />
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.loginButton, loading && styles.loginButtonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.loginButtonText}>Iniciar sesión</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Link a registro */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>¿No tienes cuenta? </Text>
          <TouchableOpacity onPress={() => navigation.navigate("Registro")}>
            <Text style={styles.footerLink}>Crear cuenta</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { flexGrow: 1, justifyContent: "center", padding: spacing.lg },

  logoContainer: { alignItems: "center", marginBottom: 40 },
  logoCircle: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: colors.primary + "15",
    justifyContent: "center", alignItems: "center",
    marginBottom: spacing.md,
  },
  appName: { fontSize: fontSize.hero, fontWeight: "800", color: colors.textPrimary },
  tagline: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: 4, textAlign: "center" },

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

  loginButton: {
    backgroundColor: colors.primary, borderRadius: borderRadius.md,
    height: 54, justifyContent: "center", alignItems: "center",
    marginTop: spacing.sm,
  },
  loginButtonDisabled: { opacity: 0.6 },
  loginButtonText: { color: "#fff", fontSize: fontSize.lg, fontWeight: "700" },

  footer: { flexDirection: "row", justifyContent: "center", marginTop: spacing.xl },
  footerText: { color: colors.textMuted, fontSize: fontSize.md },
  footerLink: { color: colors.primary, fontSize: fontSize.md, fontWeight: "600" },
});
