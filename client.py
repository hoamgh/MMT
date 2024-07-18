import socket
import json
import os
import signal

# Configuration
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 4096  # Larger buffer size for faster downloads

def signal_handler(sig, frame):
    print("\nCtrl+C pressed. Exiting...")
    os._exit(0)  # Ensures immediate exit

signal.signal(signal.SIGINT, signal_handler)

def create_output_directory():
    if not os.path.exists('output'):
        os.makedirs('output')

def write_file_request(file_name):
    """Write the file request to input.txt."""
    with open('input.txt', 'w') as file:
        file.write(file_name + '\n')

def request_file_list(s):
    """Request and receive the list of files from the server."""
    print("Requesting file list...")
    s.sendall("LIST".encode())
    data = s.recv(BUFFER_SIZE)
    files = json.loads(data.decode())
    return files

def download_file(s, filename, total_size):
    """Download the file from the server and display progress."""
    print(f"Requesting {filename}...")
    s.sendall(filename.encode())
    
    file_path = os.path.join('output', filename)
    received_size = 0
    with open(file_path, 'wb') as f:
        try:
            while True:
                data = s.recv(BUFFER_SIZE)
                if not data:
                    print(f"\nFinished downloading {filename}.")
                    break
                elif data == b"File not found":
                    print(f"\nServer: File not found - {filename}")
                    if os.path.exists(file_path):
                        os.remove(file_path)  # Remove the empty file if it was created
                    break
                else:
                    f.write(data)
                    received_size += len(data)
                    progress = (received_size / total_size) * 100
                    print(f"\rDownloading {filename} .... {progress:.0f}%", end="", flush=True)
        except socket.error as e:
            print(f"Error while downloading {filename}: {e}")

def main():
    create_output_directory()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except socket.error as e:
            print(f"Failed to connect to server: {e}")
            return
        
        files = request_file_list(s)
        print("Available files (approximate sizes):")
        for file, size in files.items():
            print(f"{file} - {size}")
        
        file_name = input("Enter the name of the file you want to download (or 'exit' to quit): ")
        
        if file_name.lower() == 'exit':
            print("Exiting client.")
            return
        
        write_file_request(file_name)  # Write the file request to input.txt
        
        if file_name in files:
            # Parse the rough file size for progress estimation
            file_size_str = files[file_name]
            size_value = int(''.join(filter(str.isdigit, file_size_str)))
            size_unit = file_size_str[-2:]
            total_size = size_value * (1024 ** 2) if size_unit == 'MB' else size_value * 1024
            download_file(s, file_name, total_size)
        else:
            print("File does not exist on the server. Try again!")

if __name__ == "__main__":
    main()