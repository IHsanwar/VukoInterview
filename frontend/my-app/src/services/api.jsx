import axios from 'axios';
import { getToken } from '../utils/auth';

const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Auto logout on 401
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
};

// Interview endpoints
export const interviewAPI = {
  getRoles: () => api.get('/interview/roles'),
  startSession: (data) => api.post('/interview/start-session', data),
  getQuestions: (sessionId) => api.get(`/interview/questions/${sessionId}`),
  uploadAnswer: (formData) => api.post('/interview/upload-answer', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  getAnswerDetail: (answerId) => api.get(`/interview/answer/${answerId}`),
};

// Dashboard endpoints
export const dashboardAPI = {
  getAnswersHistory: () => api.get('/dashboard/answers/history'),
};

export default api;