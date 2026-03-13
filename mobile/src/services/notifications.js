/**
 * Servicio de Push Notifications con Expo
 *
 * Flujo:
 * 1. Al abrir la app, pedimos permiso para notificaciones
 * 2. Obtenemos el Expo Push Token (unico por dispositivo+app)
 * 3. Lo enviamos al backend para almacenarlo
 * 4. El backend usa este token para enviar push notifications via Expo Push API
 *
 * Eventos que disparan push:
 * - Llamada recibida por el asistente
 * - Llamada finalizada con resumen disponible
 */
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
import api from "./api";

// ─── Configurar como se muestran las notificaciones en foreground ───
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

/**
 * Registra el dispositivo para push notifications.
 * Pide permisos, obtiene el token y lo envia al backend.
 *
 * @returns {string|null} El Expo Push Token o null si fallo
 */
export async function registrarPushNotifications() {
  try {
    // 1. Verificar permisos actuales
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    // 2. Si no tiene permiso, pedirlo
    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.log("Push notifications: permiso denegado");
      return null;
    }

    // 3. Obtener Expo Push Token
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: undefined, // Usa el projectId del app.json automaticamente
    });
    const pushToken = tokenData.data;

    console.log("Push token:", pushToken);

    // 4. Enviar al backend
    try {
      await api.registrarPushToken(pushToken);
      console.log("Push token registrado en backend");
    } catch (e) {
      console.warn("Error registrando push token en backend:", e.message);
    }

    // 5. Configurar canal de Android
    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("llamadas", {
        name: "Llamadas",
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: "#6C63FF",
        sound: "default",
      });
    }

    return pushToken;
  } catch (error) {
    console.error("Error configurando push notifications:", error);
    return null;
  }
}

/**
 * Listener para cuando el usuario toca una notificacion.
 * Retorna un subscription que debe limpiarse en cleanup.
 *
 * @param {function} callback - Recibe la notificacion tocada
 * @returns {Subscription}
 */
export function onNotificationTapped(callback) {
  return Notifications.addNotificationResponseReceivedListener((response) => {
    const data = response.notification.request.content.data;
    callback(data);
  });
}

/**
 * Listener para notificaciones recibidas en foreground.
 *
 * @param {function} callback - Recibe la notificacion
 * @returns {Subscription}
 */
export function onNotificationReceived(callback) {
  return Notifications.addNotificationReceivedListener(callback);
}
