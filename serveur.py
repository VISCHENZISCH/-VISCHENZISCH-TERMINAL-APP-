import socket

# Configuration identique au client
HOST_IP = "127.0.0.1"
HOST_PORT = 32000
MAX_DATA_SIZE = 1024

print(f"Démarrage du serveur sur {HOST_IP}:{HOST_PORT}")

# Créer le socket serveur
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Lier et écouter
server_socket.bind((HOST_IP, HOST_PORT))
server_socket.listen(1)
print("Serveur en attente de connexion...")

# Accepter une connexion
client_socket, client_address = server_socket.accept()
print(f"Client connecté depuis {client_address}")

# Envoyer le premier message
premier_message = "Bonjour ! Bienvenue sur le serveur"
client_socket.sendall(premier_message.encode())

# Boucle de communication
while True:
    try:
        # Recevoir le message du client
        data_recues = client_socket.recv(MAX_DATA_SIZE)
        
        if not data_recues:
            print("Client déconnecté")
            break
        
        message_client = data_recues.decode()
        print(f"Client: {message_client}")
        
        # Vérifier si le client veut quitter
        if message_client.lower() in ['quit', 'exit', 'bye']:
            reponse = "Au revoir !"
            client_socket.sendall(reponse.encode())
            break
        
        # Demander une réponse au serveur
        reponse = input("Serveur: ")
        if not reponse:
            reponse = "Message bien reçu !"
        
        # Envoyer la réponse
        client_socket.sendall(reponse.encode())
        
    except Exception as e:
        print(f"Erreur: {e}")
        break

# Fermer les connexions
client_socket.close()
server_socket.close()
print("Serveur fermé")