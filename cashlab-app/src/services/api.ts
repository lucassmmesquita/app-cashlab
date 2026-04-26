/**
 * CashLab — Axios instance configurada
 */
import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — adiciona JWT token
api.interceptors.request.use(
  async (config) => {
    // TODO: Buscar token do SecureStore
    // const token = await SecureStore.getItemAsync('access_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — tratamento de erros
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // TODO: Tentar refresh token
      // TODO: Se falhar, redirecionar para login
    }
    return Promise.reject(error);
  },
);

export default api;
