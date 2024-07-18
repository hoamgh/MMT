import socket
import json
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Server Configuration
HOST = '127.0.0.1'
PORT = 65432

# Directory where the files are stored
FILE_DIR = 'files'

# List of downloadable files with their sizes
FILES = {
    "File1.zip": "2MB",
    "File2.zip": "10MB",
    "File3.zip": "20MB",
    "File4.zip": "50MB",
    "File5.zip": "100MB"
}

def secure_filename(filename):
    """Ensure the filename does not contain path traversal attempts."""
    return os.path.basename(filename)

def send_file(conn, file_path):
    """Send the file size and then the file in chunks to the client."""
    file_size = os.path.getsize(file_path)
    conn.sendall(f"{file_size}".encode())
    with open(file_path, 'rb') as file:
        chunk = file.read(4096)
        while chunk:
            conn.sendall(chunk)
            chunk = file.read(4096)

def handle_client(conn, addr):
    logging.info(f"Connected by {addr}")
    
    # Send the list of files to the client
    conn.sendall(json.dumps(FILES).encode())
    
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        
        filename = data.strip()
        if filename == "LIST":
            conn.sendall(json.dumps(FILES).encode())
        elif filename in FILES:
            file_path = os.path.join(FILE_DIR, secure_filename(filename))
            if os.path.exists(file_path):
                try:
                    send_file(conn, file_path)
                    logging.info(f"Sent {filename}")
                except IOError as e:
                    logging.error(f"Failed to read file: {e}")
                    conn.sendall(b"Failed to send file")
            else:
                conn.sendall(b"File not found")
        else:
            conn.sendall(b"File not found")
    
    conn.close()
    logging.info(f"Connection closed for {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen()
            logging.info(f"Server listening on {HOST}:{PORT}")
            while True:
                conn, addr = s.accept()
                with conn:
                    handle_client(conn, addr)
        except socket.error as e:
            logging.error(f"Socket error: {e}")

if __name__ == "__main__":
    start_server()