import axios from "axios";

// Defaults to "" (relative / same-origin) so a single-process deploy where
// the backend also serves the built frontend just works with zero config.
// Local dev (frontend and backend on separate ports) sets an explicit
// VITE_API_BASE_URL in frontend/.env instead.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("creditlens_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function apiErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || "Something went wrong.";
}

export default client;
