import socket
import time
HOST_IP = "127.0.0.1"
HOST_PORT = 32000
MAX_DATA_SIZE = 1024

print(f"Connection au serveur  {HOST_IP}, port {HOST_PORT}...")
while True :
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((HOST_IP, HOST_PORT))
    except ConnectionRefusedError:
        print("Imposssible de se connecter au serveur")
        time.sleep(3)
    else:
        print("Connecté au serveur ")
        break


while True :
    data_recues = s.recv(MAX_DATA_SIZE)
    if not data_recues:
           break
    print("Message : ", data_recues.decode())
    texte_envoye = input("Vous:")
    s.sendall(texte_envoye.encode())
   
    



s.close()