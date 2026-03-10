/**
 * Tema visual de la app - Dark mode premium estilo App Store
 */
export const colors = {
  // Fondo
  bg: "#0F0F23",
  bgCard: "#1A1A2E",
  bgCardLight: "#25254A",
  bgInput: "#2A2A4A",

  // Primarios
  primary: "#6C63FF",
  primaryLight: "#8B83FF",
  primaryDark: "#4A42CC",

  // Acentos
  accent: "#00D9FF",
  accentGreen: "#00E676",
  accentRed: "#FF5252",
  accentYellow: "#FFD740",
  accentOrange: "#FF9100",

  // Texto
  textPrimary: "#FFFFFF",
  textSecondary: "#B0B0D0",
  textMuted: "#6B6B8D",

  // Categorías
  catPersonal: "#6C63FF",
  catTrabajo: "#00D9FF",
  catTramite: "#FFD740",
  catMarketing: "#FF5252",

  // Prioridades
  priAlta: "#FF5252",
  priMedia: "#FFD740",
  priBaja: "#00E676",

  // Bordes
  border: "#2A2A4A",
  borderLight: "#3A3A5A",
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const fontSize = {
  xs: 11,
  sm: 13,
  md: 15,
  lg: 18,
  xl: 22,
  xxl: 28,
  hero: 36,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 999,
};

export const getCategoryColor = (categoria) => {
  const map = {
    Personal: colors.catPersonal,
    Trabajo: colors.catTrabajo,
    "Trámite": colors.catTramite,
    Marketing: colors.catMarketing,
  };
  return map[categoria] || colors.textMuted;
};

export const getPriorityColor = (prioridad) => {
  const map = {
    Alta: colors.priAlta,
    Media: colors.priMedia,
    Baja: colors.priBaja,
  };
  return map[prioridad] || colors.textMuted;
};
