import requests
import time
import os

BASE_URL = "http://localhost:3000/api"

def test_pipeline():
    print("Testing End-to-End BIS RAG Pipeline...")

    # 1. Test Health (FastAPI)
    print("\n[Health] Testing AI Service...")
    res = requests.get(f"http://localhost:8000/api/health")
    print(f"[Health] Status Code: {res.status_code}")
    if res.status_code == 200:
        print(f"[Health] Response: {res.json()}")

    # 2. Upload Document
    pdf_path = r"E:\Web Development\Projects\bis-assistant\BIS-Documents\2347_2023.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return

    print(f"\n[Upload] Uploading {pdf_path}...")
    with open(pdf_path, 'rb') as f:
        files = {'files': (os.path.basename(pdf_path), f, 'application/pdf')}
        res = requests.post(f"http://localhost:8000/api/documents/upload", files=files)
        
    print(f"[Upload] Status Code: {res.status_code}")
    if res.status_code not in [200, 201]:
        print(f"[Upload] Error: {res.status_code}")
        return
        
    doc_data = res.json()['documents'][0]
    doc_id = doc_data['document_id']
    print(f"[Upload] Document ID: {doc_id}")

    # 3. Process Document
    print(f"\n[Process] Processing and chunking document {doc_id}...")
    res = requests.post(f"http://localhost:8000/api/documents/{doc_id}/process")
    print(f"[Process] Status Code: {res.status_code}")
    if res.status_code not in [200, 201]:
        print(f"[Process] Error: {res.status_code}")
        return
    print(f"[Process] Result: {res.json()}")

    # 4. Index Document
    print(f"\n[Index] Indexing chunks into Qdrant for {doc_id}...")
    res = requests.post(f"http://localhost:8000/api/documents/{doc_id}/index")
    print(f"[Index] Status Code: {res.status_code}")
    if res.status_code not in [200, 201]:
        print(f"[Index] Error: {res.status_code}")
        return
    print(f"[Index] Result: {res.json()}")

    # 5. Query
    query = "What are the safety requirements?"
    print(f"\n[Query] Asking RAG System: '{query}'")
    payload = {
        "query": query,
        "language": "English",
        "top_k": 3
    }
    # Using Node proxy to test proxying (chat route) or direct FastAPI
    res = requests.post(f"http://localhost:3000/api/chat", json=payload)
    print(f"[Query] Status Code: {res.status_code}")
    if res.status_code not in [200, 201]:
        print(f"[Query] Error: {res.status_code}")
        return
        
    chat_res = res.json()
    print(f"\n[AI Answer]:\n{chat_res.get('answer')}")
    print(f"\n[Sources Found]: {len(chat_res.get('sources', []))}")
    for src in chat_res.get('sources', []):
        print(f"  - {src.get('document_name')} (Page {src.get('page_number')})")

    print("\nEnd-to-End Pipeline test complete!")

if __name__ == '__main__':
    test_pipeline()
