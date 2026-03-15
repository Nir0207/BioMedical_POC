import type { User } from "../../types/api";

const TOKEN_KEY = "bio_token";
const USER_KEY = "bio_user";

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function setStoredUser(user: User): void {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  window.localStorage.removeItem(USER_KEY);
}
