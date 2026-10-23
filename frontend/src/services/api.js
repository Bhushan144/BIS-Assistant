// In production, calls go to separate backend URLs.
// In dev, Vite proxy handles routing so both can be empty strings.
const rawNode = (import.meta.env.VITE_NODE_API_URL || '').trim();
const rawAi = (import.meta.env.VITE_AI_API_URL || '').trim();

// Strip any trailing slash or accidental /api suffix so calls like /api/auth don't duplicate
const NODE_API = rawNode.replace(/\/+$/, '').replace(/\/api$/, '');
const AI_API = rawAi.replace(/\/+$/, '').replace(/\/api$/, '');

// --- Helper: Node backend fetch (auth/chat) with cookies ---
async function nodeFetch(path, options = {}) {
  return fetch(`${NODE_API}${path}`, { credentials: 'include', ...options });
}

// --- Helper: AI service fetch (documents/search/rag) ---
async function aiFetch(path, options = {}) {
  return fetch(`${AI_API}${path}`, options);
}

// ===========================
// NODE BACKEND APIs (auth, chat, conversations)
// ===========================

export async function authMe() {
  try {
    const res = await nodeFetch('/api/auth/me');
    if (!res.ok) return null;
    const data = await res.json();
    return data.user || null;
  } catch {
    return null;
  }
}

export async function authLogin(email, password) {
  const res = await nodeFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    throw new Error(`Server returned status ${res.status}`);
  }
  if (!res.ok) throw new Error(data.error || 'Login failed');
  return data.user;
}

export async function authRegister(name, email, password) {
  const res = await nodeFetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  let data = {};
  try {
    data = await res.json();
  } catch {
    throw new Error(`Server returned status ${res.status}`);
  }
  if (!res.ok) throw new Error(data.error || 'Registration failed');
  return data.user;
}

export async function authLogout() {
  try {
    await nodeFetch('/api/auth/logout', { method: 'POST' });
  } catch {
    // Ignore logout network errors
  }
}

export async function queryRag(query, topK = 5, language = 'English', chatHistory = []) {
  const response = await nodeFetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK, language, chat_history: chatHistory }),
  });
  let data = {};
  try {
    data = await response.json();
  } catch {
    throw new Error(`Server returned status ${response.status}`);
  }
  if (!response.ok) throw new Error(data.detail || data.error || 'RAG query failed');
  return data;
}

// ===========================
// AI SERVICE APIs (documents, search, compliance)
// ===========================

export async function checkHealth() {
  try {
    const response = await aiFetch('/api/health');
    if (!response.ok) throw new Error(`Server returned status ${response.status}`);
    return await response.json();
  } catch (error) {
    return { status: 'offline', error: error.message };
  }
}

export async function fetchDocuments() {
  const response = await aiFetch('/api/documents');
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch document library');
  }
  return await response.json();
}

export async function fetchDocumentDetails(documentId) {
  const response = await aiFetch(`/api/documents/${documentId}`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch document details');
  }
  return await response.json();
}

export function getDocumentFileUrl(documentId, pageNumber = 1) {
  return `${AI_API}/api/documents/${documentId}/file#page=${pageNumber}`;
}

export async function fetchSourceDetails(chunkId) {
  const response = await aiFetch(`/api/sources/${chunkId}`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch source details');
  }
  return await response.json();
}

export async function processDocument(documentId) {
  const response = await aiFetch(`/api/documents/${documentId}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Failed to process document');
  return data;
}

export async function indexDocument(documentId) {
  const response = await aiFetch(`/api/documents/${documentId}/index`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Failed to index document');
  return data;
}

export async function searchVectorDb(query, topK = 5) {
  const response = await aiFetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Vector search failed');
  return data;
}

export async function checkCompliance(productName) {
  const response = await aiFetch('/api/compliance/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_name: productName }),
  });
  if (!response.ok) {
    let errorMessage = 'Compliance check failed';
    try {
      const errData = await response.json();
      errorMessage = errData.detail || errorMessage;
    } catch (e) {
      errorMessage = `Server returned status ${response.status}`;
    }
    throw new Error(errorMessage);
  }
  return await response.json();
}

export async function uploadPdfs(files) {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append('files', file));

  const response = await aiFetch('/api/documents/upload', {
    method: 'POST',
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Failed to upload files');
  return data;
}

export async function wipeDocuments() {
  const response = await aiFetch('/api/documents/wipe', { method: 'DELETE' });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Failed to wipe documents');
  return data;
}

export async function deleteDocument(documentId) {
  const response = await aiFetch(`/api/documents/${documentId}`, { method: 'DELETE' });
  let data = {};
  try { data = await response.json(); } catch (e) {
    if (!response.ok) throw new Error(`Server returned status ${response.status}`);
  }
  if (!response.ok) throw new Error(data.detail || 'Failed to delete document');
  return data;
}
