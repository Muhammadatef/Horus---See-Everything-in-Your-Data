/**
 * API service for Local AI-BI Platform
 * Handles all backend communication
 */

import axios from 'axios';

// API client configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Types
export interface DataSource {
  id: string;
  name: string;
  filename: string;
  file_type: string;
  status: string;
  row_count?: number;
  column_count?: number;
  upload_date: string;
}

export interface Dataset {
  id: string;
  name: string;
  table_name: string;
  description?: string;
  sample_questions?: string[];
  created_at: string;
}

export interface QueryRequest {
  dataset_id: string;
  question: string;
}

export interface QueryResponse {
  id: string;
  question: string;
  answer: string;
  sql?: string;
  results?: {
    columns: string[];
    data: any[];
    row_count: number;
  };
  visualization?: any;
  execution_time_ms: number;
  success: boolean;
  error_message?: string;
}

export interface UploadResponse {
  id: string;
  filename: string;
  size: number;
  status: string;
  message: string;
}

// Health API
export const healthApi = {
  check: () => apiClient.get('/health'),
  detailed: () => apiClient.get('/health/detailed'),
};

// Upload API
export const uploadApi = {
  uploadFile: (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post('/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(response => response.data);
  },
  
  getStatus: (uploadId: string) => 
    apiClient.get(`/upload/status/${uploadId}`).then(response => response.data),
  
  getHistory: (limit = 10) => 
    apiClient.get(`/upload/history?limit=${limit}`).then(response => response.data),
};

// Data API
export const dataApi = {
  getSources: (): Promise<DataSource[]> => 
    apiClient.get('/data/sources').then(response => response.data),
  
  getDatasets: (): Promise<Dataset[]> => 
    apiClient.get('/data/datasets').then(response => response.data),
  
  getDatasetDetails: (datasetId: string) => 
    apiClient.get(`/data/datasets/${datasetId}`).then(response => response.data),
  
  previewDataset: (datasetId: string, limit = 10) => 
    apiClient.get(`/data/datasets/${datasetId}/preview?limit=${limit}`).then(response => response.data),
  
  getSchema: (datasetId: string) => 
    apiClient.get(`/data/datasets/${datasetId}/schema`).then(response => response.data),
  
  deleteDataset: (datasetId: string) => 
    apiClient.delete(`/data/datasets/${datasetId}`).then(response => response.data),
};

// Query API
export const queryApi = {
  askQuestion: (request: QueryRequest): Promise<QueryResponse> => 
    apiClient.post('/query/ask', request).then(response => response.data),
  
  getHistory: (datasetId: string, limit = 20) => 
    apiClient.get(`/query/history/${datasetId}?limit=${limit}`).then(response => response.data),
  
  getSuggestions: (datasetId: string) => 
    apiClient.get(`/query/suggestions/${datasetId}`).then(response => response.data),
};

// Utility functions
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};

export default apiClient;