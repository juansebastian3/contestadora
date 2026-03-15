/**
 * AuthContext - Estado global de autenticación
 *
 * Provee a toda la app:
 * - user: perfil del usuario autenticado (o null)
 * - isAuthenticated: boolean
 * - login(perfil): marca como autenticado
 * - logout(): limpia tokens y vuelve a Login
 * - refreshProfile(): recarga el perfil desde el backend
 *
 * Esto resuelve el problema de que ConfigScreen no podía
 * disparar un logout global porque el estado vivía solo en App.jsx.
 */
import React, { createContext, useContext, useState, useCallback } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = useCallback((perfil) => {
    setUser(perfil);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const refreshProfile = useCallback(async () => {
    try {
      const perfil = await api.getPerfil();
      setUser(perfil);
      return perfil;
    } catch (e) {
      // Si falla (token expirado sin refresh posible), logout
      await logout();
      return null;
    }
  }, [logout]);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return context;
}
