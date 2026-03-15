import axios, { type InternalAxiosRequestConfig } from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";
const agenticBaseURL = import.meta.env.VITE_AGENTIC_API_BASE_URL ?? "http://localhost:8011/api/v1";

export const httpClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json"
  }
});

export const agenticHttpClient = axios.create({
  baseURL: agenticBaseURL,
  headers: {
    "Content-Type": "application/json"
  }
});

function attachAuthToken(config: InternalAxiosRequestConfig) {
  const token = window.localStorage.getItem("bio_token");
  if (token) {
    if (typeof config.headers.set === "function") {
      config.headers.set("Authorization", `Bearer ${token}`);
    } else {
      config.headers = { ...config.headers, Authorization: `Bearer ${token}` };
    }
  }
  return config;
}

httpClient.interceptors.request.use(attachAuthToken);
agenticHttpClient.interceptors.request.use(attachAuthToken);
