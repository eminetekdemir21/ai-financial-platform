import axios from "axios";

// Backend'in tum endpoint'leri /api/v1 altinda (bkz. backend/app/api/v1/router.py)
const BASE_URL = "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Her istekte, localStorage'da bir token varsa otomatik olarak
// Authorization header'ina ekler. Boylece her API cagrisinda
// manuel token eklemeye gerek kalmaz.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Token gecersiz/suresi dolmussa (401), otomatik olarak kullaniciyi
// login sayfasina yonlendirir ve eski token'i temizler.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
