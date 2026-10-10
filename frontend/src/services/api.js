const API_BASE_URL = '/api';

/**
 * Check backend health status
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'offline', error: error.message };
  }
}

/**
 * Fetch list of all uploaded documents
 */
export async function fetchDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch document library');
  }
  return await response.json();
}

/**
 * Fetch detailed document metadata by document_id
 */
export async function fetchDocumentDetails(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch document details');
  }
  return await response.json();
}

/**
 * Get direct PDF file URL for browser viewing/embedding
 */
export function getDocumentFileUrl(documentId, pageNumber = 1) {
  return `${API_BASE_URL}/documents/${documentId}/file#page=${pageNumber}`;
}

/**
 * Fetch source citation details by chunk_id
 */
export async function fetchSourceDetails(chunkId) {
  const response = await fetch(`${API_BASE_URL}/sources/${chunkId}`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to fetch source details');
  }
  return await response.json();
}

/**
 * Trigger Phase 2 ingestion & structure-aware chunking pipeline for a document
 * @param {string} documentId 
 */
export async function processDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to process document');
  }
  return data;
}

/**
 * Trigger Phase 3 Qdrant vector database indexing for a processed document
 * @param {string} documentId 
 */
export async function indexDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/index`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to index document in vector database');
  }
  return data;
}

/**
 * Perform vector similarity search in Qdrant
 * @param {string} query 
 * @param {number} topK 
 */
export async function searchVectorDb(query, topK = 5) {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, top_k: topK }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Vector search failed');
  }
  return data;
}

/**
 * Execute Phase 4 - 8 LangGraph Grounded RAG Query (with language EN/HI/MR support)
 * @param {string} query 
 * @param {number} topK 
 * @param {string} language 
 */
export async function queryRag(query, topK = 5, language = 'English', chatHistory = []) {
  const response = await fetch(`${API_BASE_URL}/rag/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, top_k: topK, language, chat_history: chatHistory }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'RAG query failed');
  }
  return data;
}

/**
 * Execute Phase 9 BIS Product Compliance Inspection Report
 * @param {string} productName 
 */
export async function checkCompliance(productName) {
  const response = await fetch(`${API_BASE_URL}/compliance/check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ product_name: productName }),
  });

  if (!response.ok) {
    let errorMessage = 'Compliance check failed (Server Error)';
    try {
      const errData = await response.json();
      errorMessage = errData.detail || errorMessage;
    } catch (e) {
      errorMessage = `Server returned status ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorMessage);
  }
  
  return await response.json();
}

/**
 * Upload single or multiple PDF documents
 * @param {File[]} files 
 */
export async function uploadPdfs(files) {
  const formData = new FormData();
  
  Array.from(files).forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to upload files');
  }
  return data;
}

/**
 * Wipe all documents and clear vector database
 */
export async function wipeDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents/wipe`, {
    method: 'DELETE',
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to wipe documents');
  }
  return data;
}

/**
 * Delete a single document by ID
 */
export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
  });

  let data = {};
  try {
    data = await response.json();
  } catch (e) {
    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}: ${response.statusText}`);
    }
  }

  if (!response.ok) {
    throw new Error(data.detail || 'Failed to delete document');
  }
  return data;
}
