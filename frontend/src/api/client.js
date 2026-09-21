import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const apiClient = axios.create({ baseURL });

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("ft_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("ft_token");
      localStorage.removeItem("ft_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function friendlyError(error, fallback = "Something went wrong. Please try again.") {
  return error?.response?.data?.detail || fallback;
}
