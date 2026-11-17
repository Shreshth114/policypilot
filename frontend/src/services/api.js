import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const getHealth = async () => {
  const resp = await client.get('/health');
  return resp.data;
};

export const sendChatMessage = async (query, conversationId = null, searchMode = 'hybrid_hyde', topK = 4) => {
  const resp = await client.post('/chat', {
    query,
    conversation_id: conversationId,
    search_mode: searchMode,
    top_k: topK
  });
  return resp.data;
};

export const getDocuments = async () => {
  const resp = await client.get('/documents');
  return resp.data;
};

export const uploadDocument = async (file, category, version, effectiveDate) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  formData.append('version', version);
  formData.append('effective_date', effectiveDate);

  const resp = await client.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return resp.data;
};

export const deleteDocument = async (id) => {
  const resp = await client.delete(`/documents/${id}`);
  return resp.data;
};

export const executeSearch = async (query, mode = 'hybrid_hyde', topK = 5) => {
  const resp = await client.post('/retrieval/search', {
    query,
    mode,
    top_k: topK
  });
  return resp.data;
};

export const runEvaluation = async () => {
  const resp = await client.post('/retrieval/evaluate', {}, {
    timeout: 120000 // 120 seconds timeout for full multi-mode evaluation benchmark
  });
  return resp.data;
};

