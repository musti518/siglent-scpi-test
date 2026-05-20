import argparse
import socket
import sys
import time
from typing import List

DEFAULT_IP = "192.168.1.100"
DEFAULT_PORT = 5025
DEFAULT_FREQUENCIES = ["100MHz", "433.92MHz", "868MHz", "1GHz"]
DEFAULT_POWER = "-40dBm"
DEFAULT_WAIT_TIME = 10
DEFAULT_TIMEOUT = 5.0


def send_command(sock: socket.socket, command: str) -> None:
    """Sende einen SCPI-Befehl an den Generator."""
    if not command.endswith("\n"):
        command += "\n"
    sock.sendall(command.encode("ascii"))
    time.sleep(0.1)


def query_command(sock: socket.socket, command: str) -> str:
    """Sende eine SCPI-Abfrage und gib die Antwort zurück."""
    send_command(sock, command)
    # Lese bis zum nächsten Zeilenende, um unvollständige Antworten zu vermeiden
    data = bytearray()
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data.extend(chunk)
        if b"\n" in chunk:
            break
    text = data.decode("ascii", errors="ignore")
    # Gib die erste Zeile zurück, bereinigt
    return text.splitlines()[0].strip() if text else ""


def connect_to_device(ip: str, port: int, timeout: float) -> socket.socket:
    """Erstelle eine TCP-Verbindung zum Siglent-Gerät."""
    # socket.create_connection setzt Timeout intern und gibt einen verbundenen Socket zurück
    return socket.create_connection((ip, port), timeout)


def run_sweep(ip: str, port: int, frequencies: List[str], power: str, wait_time: int, timeout: float = DEFAULT_TIMEOUT) -> None:
    """Führe den Sweep aus: Frequenz setzen, Ausgang aktivieren und prüfen."""
    print(f"Verbinde zu {ip}:{port}...")
    with connect_to_device(ip, port, timeout) as sock:
        print("Verbunden.")
        print("Gerät:", query_command(sock, "*IDN?"))

        print("Sichere Startkonfiguration...")
        send_command(sock, ":OUTP OFF")
        send_command(sock, ":OUTP:MOD OFF")
        send_command(sock, f":POW {power}")

        try:
            for freq in frequencies:
                print(f"\nSetze Frequenz auf {freq} und Leistung auf {power}...")
                send_command(sock, ":OUTP OFF")
                send_command(sock, f":FREQ {freq}")
                send_command(sock, ":OUTP ON")

                actual_freq = query_command(sock, ":FREQ?")
                actual_pow = query_command(sock, ":POW?")
                print(f"Gerät meldet Frequenz: {actual_freq}")
                print(f"Gerät meldet Leistung: {actual_pow}")

                print(f"Warte {wait_time} Sekunden...")
                time.sleep(wait_time)
        finally:
            print("\nSchalte RF-Ausgang aus...")
            try:
                send_command(sock, ":OUTP OFF")
            except (socket.error, OSError):
                print("Warnung: Konnte RF-Ausgang nicht ausschalten.")

        # Fehlerabfrage am Ende schützen, falls die Verbindung bereits getrennt ist
        try:
            error = query_command(sock, ":SYSTEM:ERROR?")
            print(f"Systemfehlermeldung: {error}")
        except (socket.error, OSError) as exc:
            print(f"Warnung: Konnte Systemfehler nicht abfragen: {exc}")
        print("Sweep abgeschlossen.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SSG3000X Frequenz- und Pegelsweep über SCPI/TCP")
    parser.add_argument("--ip", default=DEFAULT_IP, help="IP-Adresse des Geräts")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="SCPI-Port")
    parser.add_argument("--freq", nargs="+", default=DEFAULT_FREQUENCIES, help="Liste der Frequenzen")
    parser.add_argument("--power", default=DEFAULT_POWER, help="Ausgangsleistung")
    parser.add_argument("--wait", type=int, default=DEFAULT_WAIT_TIME, help="Wartezeit pro Frequenz in Sekunden")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Socket-Timeout in Sekunden")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_sweep(args.ip, args.port, args.freq, args.power, args.wait, args.timeout)
        return 0
    except socket.timeout:
        print("Fehler: Verbindung zum Gerät hat zu lange gedauert.")
        return 1
    except socket.error as exc:
        print(f"Socket-Fehler: {exc}")
        return 2
    except KeyboardInterrupt:
        print("\nAbgebrochen durch Benutzer.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
