import socket
import threading

# Liste pour stocker les connexions des clients
clients = []
lock = threading.Lock()  # Pour gérer l'accès concurrent

def handle_client(client_socket):
    global clients
    while True:
        try:
            # Recevoir des données du client
            frame_size_data = client_socket.recv(4)
            if not frame_size_data:
                break
            frame_size = int.from_bytes(frame_size_data, byteorder='big')

            # Recevoir les données de l'image
            frame_data = b""
            while len(frame_data) < frame_size:
                frame_data += client_socket.recv(4096)

            # Envoyer les données à tous les clients connectés
            with lock:
                for client in clients:
                    if client != client_socket:
                        client.send(frame_size_data + frame_data)
        except:
            break

    # Nettoyage de la connexion
    with lock:
        clients.remove(client_socket)
    client_socket.close()

# Créer un serveur socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 5000))
server_socket.listen(2)  # Accepter jusqu'à 2 connexions

print("Serveur en attente de connexions...")

while True:
    client_socket, addr = server_socket.accept()
    print(f"Connexion acceptée de {addr}")
    clients.append(client_socket)
    threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
