import React, { createContext, ReactNode, useContext, useEffect, useState } from "react";

import { authApi } from "@/api/auth";
import { secureSession } from "@/auth/secureSession";
import { setAuthToken } from "@/api/client";
import { AuthUser } from "@/types";

const SESSION_KEY = "lexishelf.auth.session";

type AuthContextValue = {
  user: AuthUser | null;
  isRestoring: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<{ message: string; devResetToken?: string | null }>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    secureSession
      .getItem(SESSION_KEY)
      .then((stored) => {
        if (!stored) return;
        const session = JSON.parse(stored) as { access_token: string; user: AuthUser };
        setAuthToken(session.access_token);
        setUser(session.user);
      })
      .catch(() => secureSession.removeItem(SESSION_KEY))
      .finally(() => setIsRestoring(false));
  }, []);

  const authenticate = async (mode: "login" | "register", email: string, password: string) => {
    const session = await authApi[mode]({ email, password });
    await secureSession.setItem(SESSION_KEY, JSON.stringify(session));
    setAuthToken(session.access_token);
    setUser(session.user);
  };

  const logout = async () => {
    setAuthToken(null);
    setUser(null);
    await secureSession.removeItem(SESSION_KEY);
  };

  const forgotPassword = async (email: string) => {
    const result = await authApi.forgotPassword({ email });
    return { message: result.message, devResetToken: result.dev_reset_token };
  };

  const resetPassword = async (token: string, newPassword: string) => {
    const session = await authApi.resetPassword({ token, new_password: newPassword });
    await secureSession.setItem(SESSION_KEY, JSON.stringify(session));
    setAuthToken(session.access_token);
    setUser(session.user);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isRestoring,
        login: (email, password) => authenticate("login", email, password),
        register: (email, password) => authenticate("register", email, password),
        logout,
        forgotPassword,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}