# ChromaDB Viewer - Web Edition

A modern web-based viewer for exploring and browsing local Chroma databases.

## Features

- **Web Interface**: Clean, responsive web UI built with Bootstrap
- **Collection Browser**: View all collections in your Chroma database
- **Document Viewer**: Browse documents with pagination support
- **Metadata Display**: Toggle metadata visibility for each document
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Automatic dark mode based on system preferences

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the web viewer with your Chroma database path:

```bash
python viewer.py /path/to/your/chroma/database
```

The web interface will be available at: http://localhost:8000

### Command Line Options

- `--host`: Host to bind the web server to (default: 127.0.0.1)
- `--port`: Port to bind the web server to (default: 8000)

Example:
```bash
python viewer.py ./my_chroma_db --host 0.0.0.0 --port 8080
```

## Web Interface

### Collections Page
- Displays all collections in your database
- Shows document count for each collection
- Click "View Documents" to browse a collection

### Documents Page
- Paginated view of documents in a collection
- Document content with syntax highlighting
- Toggle metadata visibility
- Navigation controls for pagination
- Options to change page size (10, 50, 100 documents per page)

## Requirements

- Python 3.8+
- ChromaDB database files (chroma.sqlite3, header.bin, etc.)

## Migration from CLI Version

This web version replaces the previous command-line interface. All functionality is preserved and enhanced with:

- Better navigation and user experience
- Visual document browsing
- Responsive design for different screen sizes
- No need to remember CLI commands

## API Endpoints

The web application also provides REST API endpoints:

- `GET /api/collections` - Get list of collections
- `GET /api/collection/{name}/documents` - Get documents from a collection
- `GET /` - Main web interface
- `GET /collection/{name}` - Web interface for a specific collection
