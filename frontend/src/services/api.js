/** API service for backend communication */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// File uploads
export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getFiles = async (fileType = null, page = 1, pageSize = 20) => {
  const params = { page, page_size: pageSize };
  if (fileType) params.file_type = fileType;
  return api.get('/files/list', { params });
};

export const getFileMetadata = async (fileId) => {
  return api.get(`/files/${fileId}`);
};

export const deleteFile = async (fileId) => {
  return api.delete(`/files/${fileId}`);
};

// PDF Processing
export const processPDF = async (fileId, options = {}) => {
  return api.post(`/files/${fileId}/process`, options);
};

export const getFileChunks = async (fileId, limit = null, offset = 0) => {
  const params = { offset };
  if (limit) params.limit = limit;
  return api.get(`/files/${fileId}/chunks`, { params });
};

// Transcription
export const transcribeFile = async (fileId, options = {}) => {
  return api.post(`/files/${fileId}/transcribe`, options);
};

export const getTranscription = async (fileId) => {
  return api.get(`/files/${fileId}/transcription`);
};

// Embeddings
export const generateEmbeddings = async (fileId, options = {}) => {
  return api.post(`/files/${fileId}/embeddings`, options);
};

// Q&A
export const askQuestion = async (question, options = {}) => {
  return api.post('/ask', { question, ...options });
};

export const askQuestionAboutFile = async (fileId, question, options = {}) => {
  return api.post(`/files/${fileId}/ask`, { question, ...options });
};

// Streaming Q&A
export const askQuestionStreaming = async (question, options = {}, onChunk) => {
  const response = await fetch(`${API_BASE_URL}/ask/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, ...options }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // Stream completed - send completion signal if no sources were sent
        if (onChunk) {
          onChunk({ type: 'complete' });
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim() && line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (onChunk) onChunk(data);
          } catch (e) {
            console.error('Error parsing SSE data:', e, 'Line:', line);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error reading stream:', error);
    if (onChunk) {
      onChunk({ type: 'error', content: `Stream error: ${error.message}` });
    }
    throw error;
  }
};

export const askQuestionAboutFileStreaming = async (fileId, question, options = {}, onChunk) => {
  // Use the general streaming endpoint with file_id
  return askQuestionStreaming(question, { file_id: fileId, ...options }, onChunk);
};

// Summarization
export const summarizeFile = async (fileId, options = {}) => {
  return api.post(`/files/${fileId}/summarize`, options);
};

export const summarizeFileCustom = async (fileId, customPrompt, options = {}) => {
  return api.post(`/files/${fileId}/summarize/custom`, { custom_prompt: customPrompt, ...options });
};

// Timestamp Extraction
export const extractTimestamps = async (fileId, text) => {
  return api.post(`/files/${fileId}/timestamps`, { text });
};

// Media Playback
export const getPlaybackInfo = async (fileId, timestamp = null) => {
  const params = timestamp !== null ? { timestamp } : {};
  return api.get(`/files/${fileId}/playback`, { params });
};

export default api;

