import axios from 'axios';

// Automatically target port 8000 on whatever IP/hostname the frontend is being served from
// This ensures it works seamlessly both on localhost and when deployed to AWS EC2!
const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const healthCheck = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const uploadCSV = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const getValidationStats = async (filename: string) => {
  const [missing, duplicates, types, stats] = await Promise.all([
    api.get('/validate/missing', { params: { filename } }),
    api.get('/validate/duplicates', { params: { filename } }),
    api.get('/validate/column-types', { params: { filename } }),
    api.get('/validate/statistics', { params: { filename } })
  ]);
  return {
    missing: missing.data,
    duplicates: duplicates.data,
    types: types.data,
    stats: stats.data
  };
};

export const imputeMissing = async (filename: string, strategy: string, columns: string[] | null) => {
  const res = await api.post('/clean/missing', { strategy, columns }, { params: { filename } });
  return res.data;
};

export const encodeCategorical = async (filename: string, method: string, columns: string[] | null) => {
  const res = await api.post('/clean/encode', { method, columns }, { params: { filename } });
  return res.data;
};

export const scaleNumeric = async (filename: string, method: string, columns: string[] | null) => {
  const res = await api.post('/clean/scale', { method, columns }, { params: { filename } });
  return res.data;
};

export const featureSelection = async (filename: string, drop_constant: boolean, drop_high_missing_threshold: number | null, drop_duplicate_cols: boolean) => {
  const res = await api.post('/clean/features', { drop_constant, drop_high_missing_threshold, drop_duplicate_cols }, { params: { filename } });
  return res.data;
};

export const runFullPipeline = async (filename: string, payload: any) => {
  const res = await api.post('/clean/pipeline', payload, { params: { filename } });
  return res.data;
};

export const dropDuplicates = async (filename: string, keep: string = 'first') => {
  const res = await api.post('/clean/duplicates', { keep }, { params: { filename } });
  return res.data;
};

export const getEDAReport = async (filename: string) => {
  const res = await api.post('/eda/report', null, { params: { filename } });
  return res.data;
};

export const getEDAChart = async (endpoint: string, filename: string, column?: string, column_x?: string, column_y?: string) => {
  const params: any = { filename };
  if (column) params.column = column;
  if (column_x) params.column_x = column_x;
  if (column_y) params.column_y = column_y;
  
  const res = await api.get(`/eda/${endpoint}`, { params });
  return res.data;
};

export const getDashboardOverview = async (filename: string) => {
  const res = await api.get('/dashboard/overview', { params: { filename } });
  return res.data;
};

export const getQualityScore = async (raw_filename: string, clean_filename?: string) => {
  const res = await api.get('/dashboard/quality_score', { params: { raw_filename, clean_filename } });
  return res.data;
};

export const getDashboardChart = async (endpoint: string, filename: string, raw_filename?: string, clean_filename?: string) => {
  const params: any = { filename };
  if (raw_filename) params.raw_filename = raw_filename;
  if (clean_filename) params.clean_filename = clean_filename;
  
  const res = await api.get(`/dashboard/${endpoint}`, { params });
  return res.data;
};

export const postChat = async (message: string, history: any[], filename: string = '', datasetContext: string = '') => {
  const res = await api.post('/api/chat', {
    message,
    history,
    filename,
    dataset_context: datasetContext,
  });
  return res.data;
};

export default api;
