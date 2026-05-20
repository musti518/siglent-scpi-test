import socket
import time

IP = "192.168.1.100"
PORT = 5025
FREQUENCY = "1GHz"
POWER = "-10dBm"
ON_TIME = 10  # Sekunden


def send(sock, cmd):
    """Sende einen SCPI-Befehl."""
    if not cmd.endswith("\n"):
        cmd += "\n"
    sock.sendall(cmd.encode("ascii"))


def query(sock, cmd):
    """Sende eine Abfrage und lese die Antwort."""
    send(sock, cmd)
    data = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
        if b"\n" in chunk:
            break
    return data.decode("ascii", errors="ignore").splitlines()[0].strip() if data else ""


def main():
    try:
        with socket.create_connection((IP, PORT), timeout=5) as s:
            print("Verbindung hergestellt...")
            print("Gerät:", query(s, "*IDN?"))

            # RF Output ausschalten (Sicherheit)
            send(s, ":OUTP OFF")
            time.sleep(0.5)

            # Frequenz und Leistung setzen
            send(s, ":FREQ " + FREQUENCY)
            send(s, ":POW " + POWER)
            time.sleep(0.5)

            print(f"Frequenz: {query(s, ':FREQ?')}")
            print(f"Leistung: {query(s, ':POW?')}")

            # RF Output einschalten
            send(s, ":OUTP ON")
            print("RF Output: AN")

            # Warten
            print(f"Warte {ON_TIME} Sekunden...")
            time.sleep(ON_TIME)

            # RF Output ausschalten
            send(s, ":OUTP OFF")
            print("RF Output: AUS")

    except socket.timeout:
        print("FEHLER: Verbindung zum Gerät abgelaufen. IP/Port korrekt?")
    except socket.error as e:
        print(f"FEHLER: Verbindungsproblem - {e}")
    except Exception as e:
        print(f"FEHLER: {e}")


if __name__ == "__main__":
    main()
