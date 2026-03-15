/**
 * ErrorBoundary - Captura errores de renderizado en React
 *
 * Si un componente hijo crashea, muestra una pantalla amigable
 * en lugar de que toda la app se cierre.
 *
 * React Error Boundaries DEBEN ser class components (no hooks).
 */
import React, { Component } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Aqui se podria integrar un servicio de crash reporting
    // como Sentry, Bugsnag, etc.
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  handleRestart = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <View style={styles.content}>
            <View style={styles.iconCircle}>
              <Ionicons name="warning-outline" size={48} color="#F59E0B" />
            </View>

            <Text style={styles.title}>Algo salio mal</Text>
            <Text style={styles.message}>
              La aplicacion tuvo un error inesperado. No te preocupes, tus datos estan seguros.
            </Text>

            <TouchableOpacity style={styles.retryButton} onPress={this.handleRestart} activeOpacity={0.8}>
              <Ionicons name="refresh-outline" size={20} color="#fff" />
              <Text style={styles.retryText}>Reintentar</Text>
            </TouchableOpacity>

            {__DEV__ && this.state.error && (
              <View style={styles.debugContainer}>
                <Text style={styles.debugTitle}>Debug info:</Text>
                <Text style={styles.debugText}>{this.state.error.toString()}</Text>
              </View>
            )}
          </View>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F0F23",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  content: {
    alignItems: "center",
    maxWidth: 320,
  },
  iconCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: "rgba(245, 158, 11, 0.15)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: "800",
    color: "#fff",
    marginBottom: 12,
    textAlign: "center",
  },
  message: {
    fontSize: 15,
    color: "#B0B0D0",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 32,
  },
  retryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#6C63FF",
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 32,
    gap: 8,
    width: "100%",
  },
  retryText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
  debugContainer: {
    marginTop: 24,
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderRadius: 8,
    padding: 12,
    width: "100%",
  },
  debugTitle: {
    color: "#F59E0B",
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 4,
  },
  debugText: {
    color: "#6B6B8D",
    fontSize: 11,
    fontFamily: "monospace",
  },
});
