import socket
import sys
import time

# Standard-IP und Port des Siglent SSG3000X
IP = "192.168.1.100"
PORT = 5025

# Frequenzen, die nacheinander getestet werden sollen
FREQUENCIES = ["100MHz", "433.92MHz", "868MHz", "1GHz"]

# Ausgangsleistung für den Test
POWER = "-30dBm"

# Wartezeit in Sekunden nach jeder Frequenzänderung
WAIT = 5


def send(sock, cmd):
    """Sende einen SCPI-Befehl an das Gerät."""
    # Jeder SCPI-Befehl benötigt ein Zeilenende
    if not cmd.endswith("\n"):
        cmd += "\n"
    sock.sendall(cmd.encode("ascii"))


def query(sock, cmd):
    """Sende eine SCPI-Abfrage und lese die Antwort ein."""
    send(sock, cmd)
    # Die Antwort als Text dekodieren, Fehler ignorieren
    return sock.recv(4096).decode("ascii", errors="ignore").strip()


def main(ip, port):
    """Hauptfunktion: Verbindung aufbauen und Sweep ausführen."""
    print(f"Verbinde zu {ip}:{port}...")

    # Socket-Verbindung zum Gerät öffnen
    with socket.create_connection((ip, port), timeout=5) as s:
        # Gerätetest: Identifikation abfragen
        print("Gerät:", query(s, "*IDN?"))

        # Sicherheit: RF-Ausgang vor der Einstellung ausschalten
        send(s, ":OUTP OFF")
        # Ausgangsleistung setzen
        send(s, ":POW " + POWER)

        # Schleife über alle definierten Frequenzen
        for freq in FREQUENCIES:
            print(f"\nSetze {freq}, Power {POWER}")

            # Vor dem Umschalten kurz ausschalten
            send(s, ":OUTP OFF")
            # Frequenz setzen
            send(s, ":FREQ " + freq)
            # Ausgang wieder einschalten
            send(s, ":OUTP ON")

            # Aktuelle Werte vom Gerät abfragen
            print("FREQ?", query(s, ":FREQ?"))
            print("POW?", query(s, ":POW?"))

            # Kurze Pause, damit das Gerät sich stabilisiert
            time.sleep(WAIT)

        # Nach dem Test den Ausgang abschalten
        send(s, ":OUTP OFF")
        print("ERR?", query(s, ":SYSTEM:ERROR?"))


if __name__ == "__main__":
    # IP und Port können optional als Kommandozeilenparameter übergeben werden
    target_ip = sys.argv[1] if len(sys.argv) > 1 else IP
    target_port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT
    main(target_ip, target_port)
