/**
 * Servicio API con autenticación JWT
 *
 * Flujo de auth:
 * 1. Usuario se registra/logea → recibe access_token + refresh_token
 * 2. Tokens se guardan en AsyncStorage
 * 3. Cada request incluye: Authorization: Bearer <access_token>
 * 4. Si el access_token expira (401) → se renueva con refresh_token
 * 5. Si el refresh_token expira → se redirige a login
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

// ═══ CONFIGURACIÓN ═══
// Cambiar a tu URL real (ngrok, Railway, etc.)
const API_BASE = "https://TU_DOMINIO";

const STORAGE_KEYS = {
  ACCESS_TOKEN: "@filtro_access_token",
  REFRESH_TOKEN: "@filtro_refresh_token",
  USER_PROFILE: "@filtro_user_profile",
};

// ═══ TOKENS ═══

async function getAccessToken() {
  try {
    return await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  } catch {
    return null;
  }
}

async function saveTokens(accessToken, refreshToken) {
  try {
    await AsyncStorage.multiSet([
      [STORAGE_KEYS.ACCESS_TOKEN, accessToken],
      [STORAGE_KEYS.REFRESH_TOKEN, refreshToken],
    ]);
  } catch (e) {
    console.error("Error guardando tokens:", e);
  }
}

async function saveProfile(perfil) {
  try {
    await AsyncStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(perfil));
  } catch (e) {
    console.error("Error guardando perfil:", e);
  }
}

async function clearAuth() {
  try {
    await AsyncStorage.multiRemove([
      STORAGE_KEYS.ACCESS_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
      STORAGE_KEYS.USER_PROFILE,
    ]);
  } catch (e) {
    console.error("Error limpiando auth:", e);
  }
}

// ═══ REFRESH AUTOMÁTICO ═══

async function refreshAccessToken() {
  try {
    const refreshToken = await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    if (!refreshToken) return null;

    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      // Refresh token expirado → limpiar y forzar login
      await clearAuth();
      return null;
    }

    const data = await response.json();
    await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

// ═══ HTTP CLIENT CON AUTH ═══

const api = {
  /**
   * GET con autenticación automática y refresh de token.
   */
  async get(endpoint) {
    let token = await getAccessToken();

    let response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    // Si 401 → intentar refresh
    if (response.status === 401 && token) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        response = await fetch(`${API_BASE}${endpoint}`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${newToken}`,
          },
        });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * POST con autenticación automática y refresh de token.
   */
  async post(endpoint, body) {
    let token = await getAccessToken();

    let response = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });

    // Si 401 → intentar refresh
    if (response.status === 401 && token) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${newToken}`,
          },
          body: JSON.stringify(body),
        });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  },

  /**
   * DELETE con autenticación automática y refresh de token.
   */
  async delete(endpoint) {
    let token = await getAccessToken();

    let response = await fetch(`${API_BASE}${endpoint}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (response.status === 401 && token) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        response = await fetch(`${API_BASE}${endpoint}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${newToken}`,
          },
        });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  },

  // ═══ AUTH ═══

  async registro(nombre, email, telefono, password) {
    const response = await fetch(`${API_BASE}/auth/registro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, email, telefono, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Error en el registro");
    }

    const data = await response.json();
    await saveTokens(data.access_token, data.refresh_token);
    await saveProfile(data.perfil);
    return data;
  },

  async login(email, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Email o contraseña incorrectos");
    }

    const data = await response.json();
    await saveTokens(data.access_token, data.refresh_token);
    await saveProfile(data.perfil);
    return data;
  },

  async logout() {
    await clearAuth();
  },

  async isAuthenticated() {
    const token = await getAccessToken();
    return !!token;
  },

  async getSavedProfile() {
    try {
      const json = await AsyncStorage.getItem(STORAGE_KEYS.USER_PROFILE);
      return json ? JSON.parse(json) : null;
    } catch {
      return null;
    }
  },

  // ═══ ENDPOINTS PROTEGIDOS ═══

  // Dashboard
  getDashboard: () => api.get("/api/v1/dashboard"),

  // Llamadas
  getLlamadas: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return api.get(`/api/v1/llamadas${query ? `?${query}` : ""}`);
  },
  getLlamada: (id) => api.get(`/api/v1/llamadas/${id}`),

  // Estadísticas
  getStatsSemanal: () => api.get("/api/v1/stats/semanal"),

  // Perfil
  getPerfil: () => api.get("/api/v1/perfil"),
  cambiarModo: (modo, horario_inicio, horario_fin) =>
    api.post("/api/v1/perfil/modo-filtrado", { modo, horario_inicio, horario_fin }),
  actualizarContactos: (contactos) =>
    api.post("/api/v1/perfil/contactos", { contactos }),

  // Voces (público)
  getVoces: () => api.get("/api/v1/voces"),
  seleccionarVoz: (voz_id) => api.post("/api/v1/voces/seleccionar", { voz_id }),

  // Planes (público)
  getPlanes: () => api.get("/api/v1/planes"),

  // Configuración
  getConfig: () => api.get("/api/v1/config"),
  updateConfig: (clave, valor) => api.post("/api/v1/config", { clave, valor }),

  // Personalización (prompt, contestadora, modo asistente)
  getPersonalizacion: () => api.get("/api/v1/perfil/personalizacion"),
  guardarPrompt: (prompt) => api.post("/api/v1/perfil/prompt", { prompt }),
  borrarPrompt: () => api.delete("/api/v1/perfil/prompt"),
  cambiarModoAsistente: (modo) => api.post("/api/v1/perfil/modo-asistente", { modo }),
  borrarAudioSaludo: () => api.delete("/api/v1/perfil/audio-saludo"),

  /**
   * Subir audio de saludo (multipart/form-data).
   * @param {string} uri - URI local del archivo de audio
   * @param {string} filename - Nombre del archivo
   * @param {string} mimeType - Tipo MIME (audio/mp3, audio/wav, etc.)
   */
  async subirAudioSaludo(uri, filename = "saludo.mp3", mimeType = "audio/mpeg") {
    let token = await getAccessToken();
    const formData = new FormData();
    formData.append("audio", { uri, name: filename, type: mimeType });

    let response = await fetch(`${API_BASE}/api/v1/perfil/audio-saludo`, {
      method: "POST",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        // No "Content-Type" para FormData (el browser lo añade con boundary)
      },
      body: formData,
    });

    if (response.status === 401 && token) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        response = await fetch(`${API_BASE}/api/v1/perfil/audio-saludo`, {
          method: "POST",
          headers: { Authorization: `Bearer ${newToken}` },
          body: formData,
        });
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  },

  // ═══ CALENDARIO (Pro/Premium) ═══

  // Obtener URL de autorización Google Calendar
  getGoogleAuthUrl: () => api.get("/api/v1/calendario/google/auth-url"),

  // Enviar authorization code de Google al backend
  conectarGoogleCalendar: (code, redirectUri) =>
    api.post("/api/v1/calendario/google/conectar", { code, redirect_uri: redirectUri }),

  // Desconectar Google Calendar
  desconectarGoogleCalendar: () => api.delete("/api/v1/calendario/google"),

  // Desconectar Outlook Calendar
  desconectarOutlookCalendar: () => api.delete("/api/v1/calendario/outlook"),

  // Estado de calendarios conectados + evento actual
  getCalendarioEstado: () => api.get("/api/v1/calendario/estado"),

  // Configurar modo calendario (auto_activar, modo)
  configurarCalendario: (config) => api.post("/api/v1/calendario/config", config),

  // Tips para grabar saludo
  getTipsSaludo: () => api.get("/api/v1/tips/saludo"),

  // Health (público)
  health: () => api.get("/api/v1/health"),
};

export default api;
