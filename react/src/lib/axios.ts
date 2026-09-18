import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_URL}/api`,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
  },
});
