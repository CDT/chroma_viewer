#!/usr/bin/env python3
"""
ChromaDB Viewer - Web-based viewer for local Chroma databases

This web application allows you to:
- List all collections in a Chroma database
- Browse documents within a collection
- Navigate with pagination support through a web interface
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

import chromadb
from chromadb.api import Collection
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn


# Global variables for the web app
app = FastAPI(title="ChromaDB Viewer", description="Web-based viewer for local Chroma databases")
chroma_client = None
db_path = None

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChromaViewer:
    @staticmethod
    def connect(db_path_str: str) -> bool:
        """Connect to the Chroma database"""
        global chroma_client, db_path

        try:
            db_path = Path(db_path_str)
            chroma_client = chromadb.PersistentClient(path=str(db_path))

            return True
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            return False

    @staticmethod
    def disconnect() -> bool:
        """Disconnect from the current database"""
        global chroma_client, db_path

        try:
            chroma_client = None
            db_path = None
            return True
        except Exception as e:
            print(f"Error during disconnect: {e}")
            return False

    @staticmethod
    def get_collections() -> List[Dict[str, Any]]:
        """Get all collections with their metadata"""
        collections_data = []
        collections_list = chroma_client.list_collections()
        for col_info in collections_list:
            try:
                collection = chroma_client.get_collection(name=col_info.name)
                doc_count = collection.count()
                collections_data.append({
                    "name": collection.name,
                    "document_count": doc_count
                })
            except Exception as e:
                collections_data.append({
                    "name": col_info.name,
                    "document_count": 0,
                    "error": str(e)
                })
        return collections_data

    @staticmethod
    def get_collection_documents(collection_name: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get documents from a specific collection with pagination"""
        try:
            # Get the collection
            collection = chroma_client.get_collection(name=collection_name)

            # Get all documents
            results = collection.get(include=['documents', 'metadatas'])
            # IDs are returned by default in ChromaDB results

            if not results['documents']:
                return {
                    "collection_name": collection_name,
                    "documents": [],
                    "total_documents": 0,
                    "current_page": page,
                    "total_pages": 0,
                    "page_size": page_size
                }

            documents = results['documents']
            metadatas = results.get('metadatas', [])
            # IDs are always available in ChromaDB results
            ids = results.get('ids', list(range(len(documents))))

            total_docs = len(documents)
            total_pages = (total_docs + page_size - 1) // page_size  # Ceiling division

            # Validate page number
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages

            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_docs)

            # Prepare documents for current page
            page_documents = []
            for idx in range(start_idx, end_idx):
                doc_id = ids[idx] if idx < len(ids) else f"doc_{idx}"
                content = documents[idx]
                metadata = metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {}

                page_documents.append({
                    "index": idx + 1,  # 1-based indexing
                    "id": doc_id,
                    "content": content,
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    "metadata": metadata,
                    "metadata_str": json.dumps(metadata, indent=2) if metadata else ""
                })

            return {
                "collection_name": collection_name,
                "documents": page_documents,
                "total_documents": total_docs,
                "current_page": page,
                "total_pages": total_pages,
                "page_size": page_size,
                "start_idx": start_idx + 1,
                "end_idx": end_idx
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


# API Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page showing connection form or collections"""
    if not chroma_client:
        return templates.TemplateResponse("connection.html", {
            "request": request
        })

    collections = ChromaViewer.get_collections()
    return templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": collections,
        "db_path": str(db_path)
    })


@app.post("/api/connect", response_class=JSONResponse)
async def connect_database(request: Request):
    """API endpoint to connect to a database"""
    body = await request.json()
    db_path_str = body.get("db_path", "").strip()
    
    if not db_path_str:
        raise HTTPException(status_code=400, detail="Database path is required")
    
    db_path = Path(db_path_str)
    if not db_path.exists():
        raise HTTPException(status_code=400, detail=f"Database path '{db_path}' does not exist")
    
    if not db_path.is_dir():
        raise HTTPException(status_code=400, detail=f"'{db_path}' is not a directory")
    
    # Check if it looks like a Chroma database
    chroma_files = ['chroma.sqlite3', 'header.bin']
    has_chroma_files = any((db_path / f).exists() for f in chroma_files)
    
    if not has_chroma_files:
        raise HTTPException(status_code=400, detail=f"'{db_path}' doesn't appear to contain Chroma database files")
    
    # Try to connect
    if ChromaViewer.connect(db_path_str):
        return {"success": True, "message": f"Successfully connected to database at {db_path}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to database")


@app.post("/api/disconnect", response_class=JSONResponse)
async def disconnect_database():
    """API endpoint to disconnect from the current database"""
    if not chroma_client:
        raise HTTPException(status_code=400, detail="No database connection to disconnect")
    
    if ChromaViewer.disconnect():
        return {"success": True, "message": "Successfully disconnected from database"}
    else:
        raise HTTPException(status_code=500, detail="Failed to disconnect from database")


@app.get("/api/collections", response_class=JSONResponse)
async def get_collections_api():
    """API endpoint to get collections"""
    if not chroma_client:
        raise HTTPException(status_code=500, detail="Database not connected")
    return {"collections": ChromaViewer.get_collections()}


@app.get("/collection/{collection_name}", response_class=HTMLResponse)
async def view_collection(request: Request, collection_name: str, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """View documents in a collection"""
    if not chroma_client:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Database not connected. Please reconnect."
        })

    documents_data = ChromaViewer.get_collection_documents(collection_name, page, page_size)
    return templates.TemplateResponse("documents.html", {
        "request": request,
        "collection_name": collection_name,
        "documents": documents_data["documents"],
        "total_documents": documents_data["total_documents"],
        "current_page": documents_data["current_page"],
        "total_pages": documents_data["total_pages"],
        "page_size": page_size,
        "start_idx": documents_data["start_idx"],
        "end_idx": documents_data["end_idx"],
        "max": max,
        "min": min,
        "range": range
    })


@app.get("/api/collection/{collection_name}/documents", response_class=JSONResponse)
async def get_collection_documents_api(collection_name: str, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """API endpoint to get documents from a collection"""
    if not chroma_client:
        raise HTTPException(status_code=500, detail="Database not connected")
    return ChromaViewer.get_collection_documents(collection_name, page, page_size)


def create_directories():
    """Create necessary directories for templates and static files"""
    Path("templates").mkdir(exist_ok=True)
    Path("static/css").mkdir(parents=True, exist_ok=True)
    Path("static/js").mkdir(parents=True, exist_ok=True)






def main():
    parser = argparse.ArgumentParser(
        description="Web-based viewer for local Chroma databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python viewer.py                           # Start with connection UI
  python viewer.py /path/to/chroma/db        # Connect directly to database
  python viewer.py ./chroma_db               # Connect to local database
  python viewer.py ../my_project/data/chroma # Connect to relative path

The web interface will be available at: http://localhost:8000
        """
    )

    parser.add_argument(
        "db_path",
        nargs="?",  # Make db_path optional
        help="Path to the local Chroma database directory (optional)"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the web server to (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the web server to (default: 8000)"
    )

    args = parser.parse_args()

    # Create necessary directories
    print("Setting up web interface...")
    create_directories()

    # Connect to database if path provided
    if args.db_path:
        db_path = Path(args.db_path)
        if not db_path.exists():
            print(f"Error: Database path '{db_path}' does not exist.")
            sys.exit(1)

        if not db_path.is_dir():
            print(f"Error: '{db_path}' is not a directory.")
            sys.exit(1)

        # Check if it looks like a Chroma database
        chroma_files = ['chroma.sqlite3', 'header.bin']
        has_chroma_files = any((db_path / f).exists() for f in chroma_files)

        if not has_chroma_files:
            print(f"Warning: '{db_path}' doesn't appear to contain Chroma database files.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                sys.exit(0)

        # Connect to database
        print(f"Connecting to Chroma database at: {db_path}")
        if not ChromaViewer.connect(str(db_path)):
            print("Failed to connect to database. Exiting.")
            sys.exit(1)
        print(f"✓ Connected successfully.")
    else:
        print("No database path provided. You can connect via the web interface.")

    print(f"Starting web server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")

    # Start the web server
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
