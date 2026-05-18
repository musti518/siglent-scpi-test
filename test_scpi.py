import socket

# IP-Adresse deines Siglent SSG3000X eintragen
IP = "192.168.1.100"

# Standard-Port für SCPI über Socket beim SSG3000X
PORT = 5025

# Socket-Verbindung erstellen
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Maximal 5 Sekunden warten
    s.settimeout(5)

    # Verbindung zum Signalgenerator öffnen
    s.connect((IP, PORT))

    # Gerätekennung abfragen
    s.sendall(b"*IDN?\n")

    # Antwort empfangen und ausgeben
    antwort = s.recv(4096)
    print(antwort.decode(errors="ignore").strip())
