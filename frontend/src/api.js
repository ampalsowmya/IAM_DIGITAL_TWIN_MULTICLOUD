import axios from 'axios';

// Use Vite environment variable for API base, with a local default.
export const API_BASE =
  import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Centralized axios error logging so network / server issues
// are clearly visible in the browser console.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API request failed', {
      message: error.message,
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

const DEFAULT_CLOUD = 'aws';

export const getSummary = (cloud = DEFAULT_CLOUD) =>
  api.get('/api/summary', { params: { cloud } });
export const getRoles = (cloud = DEFAULT_CLOUD) =>
  api.get('/api/roles', { params: { cloud } });
export const getRoleDetail = (roleName, cloud = DEFAULT_CLOUD) =>
  api.get(`/api/roles/${encodeURIComponent(roleName)}`, {
    params: { cloud },
  });
export const getGraph = (cloud = DEFAULT_CLOUD, limit = 100) =>
  api.get('/api/graph', { params: { cloud, limit } });
export const getCompliance = (cloud = DEFAULT_CLOUD) =>
  api.get('/api/compliance', { params: { cloud } });
export const getRisk = (cloud = DEFAULT_CLOUD) =>
  api.get('/api/risk', { params: { cloud } });
export const getEscalation = (cloud = DEFAULT_CLOUD) =>
  api.get('/api/escalation', { params: { cloud } });
export const explainRole = (roleName, cloud = DEFAULT_CLOUD) =>
  api.get(`/api/llm/explain/${encodeURIComponent(roleName)}`, {
    params: { cloud },
  });

export default api;
