import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchCurrentUser, loginUser, registerUser } from "../../services/auth";
import {
  clearStoredToken,
  clearStoredUser,
  getStoredToken,
  getStoredUser,
  setStoredToken,
  setStoredUser
} from "./storage";
import type { LoginPayload, RegisterPayload, User } from "../../types/api";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(token && !user));

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    setIsLoading(true);
    fetchCurrentUser()
      .then((currentUser) => {
        if (cancelled) {
          return;
        }
        setUser(currentUser);
        setStoredUser(currentUser);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        clearStoredToken();
        clearStoredUser();
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function hydrateAuthenticatedUser(): Promise<void> {
    const currentUser = await fetchCurrentUser();
    setStoredUser(currentUser);
    setUser(currentUser);
  }

  async function login(payload: LoginPayload): Promise<void> {
    const authToken = await loginUser(payload);
    setStoredToken(authToken.access_token);
    setToken(authToken.access_token);
    await hydrateAuthenticatedUser();
  }

  async function register(payload: RegisterPayload): Promise<void> {
    await registerUser(payload);
    await login({ email: payload.email, password: payload.password });
  }

  function logout(): void {
    clearStoredToken();
    clearStoredUser();
    setToken(null);
    setUser(null);
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      login,
      register,
      logout
    }),
    [isLoading, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
