import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

export const httpClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json"
  }
});

httpClient.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("bio_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
