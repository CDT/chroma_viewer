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
    """Main page showing collections"""
    if not chroma_client:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Database not connected. Please restart the application."
        })

    collections = ChromaViewer.get_collections()
    return templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": collections,
        "db_path": str(db_path)
    })


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
            "error": "Database not connected. Please restart the application."
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


def create_html_templates():
    """Create HTML templates for the web interface"""

    # Collections page template
    collections_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromaDB Viewer - Collections</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/style.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-database"></i> ChromaDB Viewer
            </span>
            <small class="text-light">Database: {{ db_path }}</small>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h2><i class="fas fa-list"></i> Collections</h2>
                <p class="text-muted">Select a collection to view its documents</p>

                {% if collections %}
                <div class="row">
                    {% for collection in collections %}
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">
                                    <i class="fas fa-folder"></i> {{ collection.name }}
                                </h5>
                                <p class="card-text">
                                    <span class="badge bg-primary">
                                        <i class="fas fa-file-alt"></i>
                                        {{ collection.document_count }} documents
                                    </span>
                                </p>
                                <a href="/collection/{{ collection.name }}" class="btn btn-primary">
                                    <i class="fas fa-eye"></i> View Documents
                                </a>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    No collections found in the database.
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

    # Documents page template
    documents_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromaDB Viewer - {{ collection_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/style.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-database"></i> ChromaDB Viewer
            </span>
            <a href="/" class="btn btn-outline-light btn-sm">
                <i class="fas fa-arrow-left"></i> Back to Collections
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12">
                <h2><i class="fas fa-file-alt"></i> Collection: {{ collection_name }}</h2>
                <p class="text-muted">
                    Showing {{ start_idx }}-{{ end_idx }} of {{ total_documents }} documents
                </p>
            </div>
        </div>

        {% if documents %}
        <div class="row">
            {% for document in documents %}
            <div class="col-12 mb-3">
                <div class="card">
                    <div class="card-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">
                                <i class="fas fa-hashtag"></i> Document #{{ document.index }}
                                <small class="text-muted">({{ document.id }})</small>
                            </h6>
                            <button class="btn btn-sm btn-outline-primary" onclick="toggleMetadata('{{ document.id }}')">
                                <i class="fas fa-info-circle"></i> Metadata
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="document-content">
                            <pre class="mb-0">{{ document.content }}</pre>
                        </div>

                        <div id="metadata-{{ document.id }}" class="metadata-section mt-3" style="display: none;">
                            <hr>
                            <h6><i class="fas fa-tags"></i> Metadata</h6>
                            {% if document.metadata_str %}
                            <pre class="bg-light p-2 rounded">{{ document.metadata_str }}</pre>
                            {% else %}
                            <p class="text-muted">No metadata available</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Pagination -->
        {% if total_pages > 1 %}
        <div class="row mt-4">
            <div class="col-12">
                <nav aria-label="Document pagination">
                    <ul class="pagination justify-content-center">
                        {% if current_page > 1 %}
                        <li class="page-item">
                            <a class="page-link" href="/collection/{{ collection_name }}?page={{ current_page - 1 }}&page_size={{ page_size }}">
                                <i class="fas fa-chevron-left"></i> Previous
                            </a>
                        </li>
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">
                                <i class="fas fa-chevron-left"></i> Previous
                            </span>
                        </li>
                        {% endif %}

                        {% for page_num in range(max(1, current_page - 2), min(total_pages + 1, current_page + 3)) %}
                        <li class="page-item {% if page_num == current_page %}active{% endif %}">
                            <a class="page-link" href="/collection/{{ collection_name }}?page={{ page_num }}&page_size={{ page_size }}">
                                {{ page_num }}
                            </a>
                        </li>
                        {% endfor %}

                        {% if current_page < total_pages %}
                        <li class="page-item">
                            <a class="page-link" href="/collection/{{ collection_name }}?page={{ current_page + 1 }}&page_size={{ page_size }}">
                                Next <i class="fas fa-chevron-right"></i>
                            </a>
                        </li>
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">
                                Next <i class="fas fa-chevron-right"></i>
                            </span>
                        </li>
                        {% endif %}
                    </ul>
                </nav>

                <div class="text-center mt-2">
                    <small class="text-muted">
                        Page {{ current_page }} of {{ total_pages }} |
                        <a href="/collection/{{ collection_name }}?page=1&page_size=50">Show 50 per page</a> |
                        <a href="/collection/{{ collection_name }}?page=1&page_size=100">Show 100 per page</a>
                    </small>
                </div>
            </div>
        </div>
        {% endif %}

        {% else %}
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            No documents found in this collection.
        </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/app.js"></script>
</body>
</html>"""

    # Error page template
    error_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromaDB Viewer - Error</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-danger">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-exclamation-triangle"></i> ChromaDB Viewer - Error
            </span>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="alert alert-danger">
                    <h4><i class="fas fa-exclamation-triangle"></i> Error</h4>
                    <p>{{ error }}</p>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

    # Write templates to files
    with open("templates/collections.html", "w") as f:
        f.write(collections_html)

    with open("templates/documents.html", "w") as f:
        f.write(documents_html)

    with open("templates/error.html", "w") as f:
        f.write(error_html)


def create_static_files():
    """Create CSS and JavaScript files"""

    # CSS file
    css_content = """/* Custom styles for ChromaDB Viewer */

.document-content pre {
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    line-height: 1.4;
    max-height: 300px;
    overflow-y: auto;
}

.metadata-section pre {
    font-size: 0.8em;
    max-height: 200px;
    overflow-y: auto;
}

.card {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: box-shadow 0.3s ease;
}

.card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.navbar-brand {
    font-weight: bold;
}

.badge {
    font-size: 0.75em;
}

.pagination .page-link {
    color: #0d6efd;
}

.pagination .page-link:hover {
    color: #0b5ed7;
}

.btn-outline-light:hover {
    color: #212529;
}

.alert {
    border-radius: 8px;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .card {
        background-color: #2d3748;
        border-color: #4a5568;
        color: #e2e8f0;
    }

    .document-content pre {
        background-color: #1a202c;
        color: #e2e8f0;
    }

    .metadata-section pre {
        background-color: #1a202c;
        color: #e2e8f0;
    }
}"""

    # JavaScript file
    js_content = """// Custom JavaScript for ChromaDB Viewer

function toggleMetadata(docId) {
    const metadataSection = document.getElementById(`metadata-${docId}`);
    const button = event.target.closest('button');

    if (metadataSection.style.display === 'none' || metadataSection.style.display === '') {
        metadataSection.style.display = 'block';
        button.innerHTML = '<i class="fas fa-times"></i> Hide Metadata';
        button.classList.remove('btn-outline-primary');
        button.classList.add('btn-outline-secondary');
    } else {
        metadataSection.style.display = 'none';
        button.innerHTML = '<i class="fas fa-info-circle"></i> Metadata';
        button.classList.remove('btn-outline-secondary');
        button.classList.add('btn-outline-primary');
    }
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.classList.contains('alert-danger')) {
            setTimeout(function() {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 300);
            }, 5000);
        }
    });
});"""

    # Write static files
    with open("static/css/style.css", "w") as f:
        f.write(css_content)

    with open("static/js/app.js", "w") as f:
        f.write(js_content)


def main():
    parser = argparse.ArgumentParser(
        description="Web-based viewer for local Chroma databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python viewer.py /path/to/chroma/db
  python viewer.py ./chroma_db
  python viewer.py ../my_project/data/chroma

The web interface will be available at: http://localhost:8000
        """
    )

    parser.add_argument(
        "db_path",
        help="Path to the local Chroma database directory"
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

    # Validate database path
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

    # Create necessary directories and files
    print("Setting up web interface...")
    create_directories()
    create_html_templates()
    create_static_files()

    # Connect to database
    print(f"Connecting to Chroma database at: {db_path}")
    if not ChromaViewer.connect(str(db_path)):
        print("Failed to connect to database. Exiting.")
        sys.exit(1)

    print(f"✓ Connected successfully. Starting web server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")

    # Start the web server
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
