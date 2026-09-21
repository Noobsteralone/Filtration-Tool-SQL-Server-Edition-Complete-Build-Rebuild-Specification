import React, { createContext, useContext, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";

const AuthContext = createContext(null);

const ROLE_RANK = { USER: 0, ADMIN: 1, SUPER_ADMIN: 2 };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("ft_user");
    return raw ? JSON.parse(raw) : null;
  });

  async function login(username, password) {
    const { data } = await apiClient.post("/api/auth/login", { username, password });
    localStorage.setItem("ft_token", data.access_token);
    const nextUser = { username: data.username, role: data.role };
    localStorage.setItem("ft_user", JSON.stringify(nextUser));
    setUser(nextUser);
    return nextUser;
  }

  function logout() {
    localStorage.removeItem("ft_token");
    localStorage.removeItem("ft_user");
    setUser(null);
  }

  function hasRole(minimumRole) {
    if (!user) return false;
    return (ROLE_RANK[user.role] ?? 0) >= (ROLE_RANK[minimumRole] ?? 0);
  }

  const value = useMemo(() => ({ user, login, logout, hasRole }), [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
