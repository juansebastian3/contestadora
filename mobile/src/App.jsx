/**
 * FiltroLlamadas - App Principal
 *
 * Flujo de autenticación:
 * - Al abrir, revisa si hay un token guardado en AsyncStorage
 * - Si NO hay token → muestra Login/Registro
 * - Si SÍ hay token → muestra la app principal con tabs
 * - Si el token expira → intenta refresh, si falla → vuelve a Login
 *
 * Onboarding:
 * - Despues del primer registro, muestra 3 slides de bienvenida
 * - Se guarda en AsyncStorage para no repetir
 *
 * AuthContext:
 * - Estado global de auth accesible desde cualquier pantalla
 * - ConfigScreen puede llamar logout() sin prop drilling
 */
import React, { useState, useEffect } from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { StatusBar } from "expo-status-bar";
import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";

import LoginScreen from "./screens/LoginScreen";
import RegistroScreen from "./screens/RegistroScreen";
import OnboardingScreen from "./screens/OnboardingScreen";
import DashboardScreen from "./screens/DashboardScreen";
import HistorialScreen from "./screens/HistorialScreen";
import PersonalizacionScreen from "./screens/PersonalizacionScreen";
import ConfigScreen from "./screens/ConfigScreen";
import VocesScreen from "./screens/VocesScreen";
import CalendarioScreen from "./screens/CalendarioScreen";
import LegalScreen from "./screens/LegalScreen";
import PlanesScreen from "./screens/PlanesScreen";

import api from "./services/api";
import { registrarPushNotifications } from "./services/notifications";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { colors } from "./utils/theme";

const ONBOARDING_KEY = "@filtrollamadas_onboarding_done";

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const tabBarStyle = {
  backgroundColor: "#0F0F23",
  borderTopColor: "#2A2A4A",
  borderTopWidth: 0.5,
  height: 85,
  paddingBottom: 25,
  paddingTop: 8,
};

// ─── Tabs principales (usuario autenticado) ────────────────
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: "#6C63FF",
        tabBarInactiveTintColor: "#6B6B8D",
        tabBarStyle,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        tabBarIcon: ({ focused, color }) => {
          const icons = {
            Dashboard: focused ? "grid" : "grid-outline",
            Historial: focused ? "time" : "time-outline",
            Personalizar: focused ? "color-wand" : "color-wand-outline",
            Calendario: focused ? "calendar" : "calendar-outline",
            Config: focused ? "settings" : "settings-outline",
          };
          return <Ionicons name={icons[route.name]} size={22} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ tabBarLabel: "Inicio" }}
      />
      <Tab.Screen
        name="Historial"
        component={HistorialScreen}
        options={{ tabBarLabel: "Historial" }}
      />
      <Tab.Screen
        name="Personalizar"
        component={PersonalizacionScreen}
        options={{ tabBarLabel: "Mi IA" }}
      />
      <Tab.Screen
        name="Calendario"
        component={CalendarioScreen}
        options={{ tabBarLabel: "Agenda" }}
      />
      <Tab.Screen
        name="Config"
        component={ConfigScreen}
        options={{ tabBarLabel: "Ajustes" }}
      />
    </Tab.Navigator>
  );
}

// ─── App Principal ─────────────────────────────────────────
function AppContent() {
  const [isLoading, setIsLoading] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const { isAuthenticated, login, logout } = useAuth();

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const authed = await api.isAuthenticated();
      if (authed) {
        try {
          const perfil = await api.getPerfil();
          login(perfil);
          registrarPushNotifications().catch(() => {});
        } catch {
          await logout();
        }
      }
    } catch {
      // No hay token, se queda en login
    } finally {
      setIsLoading(false);
    }
  }

  async function handleAuthSuccess(perfil, isNewUser = false) {
    login(perfil);
    if (isNewUser) {
      setShowOnboarding(true);
    } else {
      const done = await AsyncStorage.getItem(ONBOARDING_KEY);
      if (!done) {
        setShowOnboarding(true);
      }
    }
    registrarPushNotifications().catch(() => {});
  }

  async function handleOnboardingComplete() {
    await AsyncStorage.setItem(ONBOARDING_KEY, "true");
    setShowOnboarding(false);
  }

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <StatusBar style="light" />
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (isAuthenticated && showOnboarding) {
    return (
      <>
        <StatusBar style="light" />
        <OnboardingScreen onComplete={handleOnboardingComplete} />
      </>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      {isAuthenticated ? (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Main" component={MainTabs} />
          <Stack.Screen name="Legal" component={LegalScreen} />
          <Stack.Screen name="Planes" component={PlanesScreen} />
        </Stack.Navigator>
      ) : (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Login">
            {(props) => <LoginScreen {...props} onAuthSuccess={handleAuthSuccess} />}
          </Stack.Screen>
          <Stack.Screen name="Registro">
            {(props) => <RegistroScreen {...props} onAuthSuccess={handleAuthSuccess} />}
          </Stack.Screen>
          <Stack.Screen name="LegalAuth" component={LegalScreen} />
        </Stack.Navigator>
      )}
    </NavigationContainer>
  );
}

// ─── Wrapper con Error Boundary + AuthProvider ──────────────
export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    backgroundColor: colors.bg,
    justifyContent: "center",
    alignItems: "center",
  },
});
