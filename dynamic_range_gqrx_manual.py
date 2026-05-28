import socket
import time
import csv
from pathlib import Path


# ============================================================
# EINSTELLUNGEN
# ============================================================

# IP-Adresse deines Siglent SSG3000X
SIGLENT_IP = "192.168.1.100"

# SCPI-over-Socket-Port
SIGLENT_PORT = 5025

# Testfrequenz des Signalgenerators
# Muss zur Frequenz in GQRX passen.
FREQUENCY = "100MHz"

# Falls ein Attenuator zwischen Siglent und SDR steckt:
# Beispiel: 30 dB Attenuator -> ATTENUATOR_DB = 30
# Ohne Attenuator -> ATTENUATOR_DB = 0
ATTENUATOR_DB = 30

# Wie lange jeder Messpunkt aktiv bleiben soll
WAIT_SECONDS = 10

# SDR-Gain-Werte, die du nacheinander manuell in GQRX einstellst
# Das Skript erinnert dich jeweils daran.
SDR_GAINS_DB = [20, 30, 40]

# Generatorleistungen in dBm
# Für den Anfang bewusst nicht zu groß starten.
GENERATOR_POWERS_DBM = [-90, -85, -80, -75, -70, -65, -60, -55, -50, -45, -40]

# Name der CSV-Datei
CSV_FILE = "dynamic_range_gqrx_manual.csv"


# ============================================================
# SCPI-FUNKTIONEN
# ============================================================

def send(sock, command):
    """
    Sendet einen SCPI-Befehl an den Signalgenerator.

    Beispiel:
        :FREQ 100MHz
        :POW -60dBm
        :OUTP ON

    Das Zeilenende \\n ist wichtig, damit das Gerät erkennt:
    Der Befehl ist vollständig.
    """
    message = command.strip() + "\n"
    sock.sendall(message.encode("ascii"))
    time.sleep(0.1)


def query(sock, command):
    """
    Sendet eine SCPI-Abfrage und liest die Antwort.

    Abfragen erkennt man am Fragezeichen:
        *IDN?
        :FREQ?
        :POW?
        :OUTP?
    """
    send(sock, command)
    response = sock.recv(4096)
    return response.decode(errors="ignore").strip()


def save_rows_to_csv(rows, filename):
    """
    Speichert alle Messwerte in eine CSV-Datei.
    Die CSV kannst du später in MATLAB, Excel oder Python plotten.
    """
    fieldnames = [
        "frequency",
        "sdr_gain_db",
        "generator_power_dbm",
        "attenuator_db",
        "sdr_input_power_dbm",
        "sdr_output_dbfs",
    ]

    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_current_row(row):
    """
    Gibt den zuletzt gemessenen Punkt übersichtlich aus.
    """
    print("\nGespeicherter Messpunkt:")
    print(f"  Frequenz:              {row['frequency']}")
    print(f"  SDR-Gain:              {row['sdr_gain_db']} dB")
    print(f"  Generatorleistung:     {row['generator_power_dbm']} dBm")
    print(f"  Attenuator:            {row['attenuator_db']} dB")
    print(f"  SDR-Eingangsleistung:  {row['sdr_input_power_dbm']} dBm")
    print(f"  SDR-Ausgang:           {row['sdr_output_dbfs']} dBFS")


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():
    rows = []

    print("Dynamic-Range-Test mit GQRX und Siglent SSG3000X")
    print("------------------------------------------------")
    print("Ablauf:")
    print("1. GQRX läuft parallel.")
    print("2. Du stellst den SDR-Gain in GQRX manuell ein.")
    print("3. Das Skript setzt automatisch die Siglent-Leistung.")
    print("4. Du liest den dBFS-Wert in GQRX ab und gibst ihn hier ein.")
    print("5. Das Skript speichert alles als CSV.\n")

    print(f"Testfrequenz: {FREQUENCY}")
    print(f"Attenuator:   {ATTENUATOR_DB} dB")
    print(f"CSV-Datei:    {CSV_FILE}\n")

    # Verbindung zum Siglent öffnen
    print(f"Verbinde zu {SIGLENT_IP}:{SIGLENT_PORT} ...")

    with socket.create_connection((SIGLENT_IP, SIGLENT_PORT), timeout=5) as sock:
        print("Verbunden.")
        print("Gerät:", query(sock, "*IDN?"))

        # Sicherheitszustand
        send(sock, ":OUTP OFF")
        send(sock, ":OUTP:MOD OFF")
        send(sock, f":FREQ {FREQUENCY}")

        print("\nBitte jetzt GQRX vorbereiten:")
        print("- SDR auswählen")
        print("- gleiche Frequenz einstellen")
        print("- AGC ausschalten")
        print("- Gain manuell einstellbar machen")
        input("Wenn GQRX bereit ist, Enter drücken...")

        try:
            # Äußere Schleife: verschiedene SDR-Gains
            for gain in SDR_GAINS_DB:
                print("\n" + "=" * 70)
                print(f"Stelle jetzt in GQRX den SDR-Gain manuell auf {gain} dB.")
                print("=" * 70)
                input("Wenn der SDR-Gain eingestellt ist, Enter drücken...")

                # Innere Schleife: Generatorleistungen
                for power in GENERATOR_POWERS_DBM:
                    # Berechnung: Was kommt ungefähr am SDR an?
                    sdr_input_power = power - ATTENUATOR_DB

                    print("\n" + "-" * 70)
                    print(f"SDR-Gain:          {gain} dB")
                    print(f"Generatorleistung: {power} dBm")
                    print(f"SDR-Input ca.:     {sdr_input_power} dBm")

                    # RF kurz ausschalten, Leistung setzen, wieder einschalten
                    send(sock, ":OUTP OFF")
                    send(sock, f":POW {power}dBm")
                    send(sock, ":OUTP ON")

                    # Gerät zur Kontrolle abfragen
                    actual_freq = query(sock, ":FREQ?")
                    actual_power = query(sock, ":POW?")
                    output_state = query(sock, ":OUTP?")

                    print(f"Gerät meldet FREQ: {actual_freq} Hz")
                    print(f"Gerät meldet POW:  {actual_power} dBm")
                    print(f"RF Output Status:  {output_state}")
                    print(f"Warte {WAIT_SECONDS} Sekunden...")
                    time.sleep(WAIT_SECONDS)

                    # dBFS-Wert manuell aus GQRX ablesen und eingeben
                    dbfs_text = input("GQRX-dBFS-Wert eingeben, z. B. -52.3, oder leer zum Überspringen: ")

                    if dbfs_text.strip() == "":
                        print("Messpunkt übersprungen.")
                        continue

                    try:
                        dbfs_value = float(dbfs_text.replace(",", "."))
                    except ValueError:
                        print("Ungültiger Wert. Messpunkt übersprungen.")
                        continue

                    row = {
                        "frequency": FREQUENCY,
                        "sdr_gain_db": gain,
                        "generator_power_dbm": power,
                        "attenuator_db": ATTENUATOR_DB,
                        "sdr_input_power_dbm": sdr_input_power,
                        "sdr_output_dbfs": dbfs_value,
                    }

                    rows.append(row)
                    print_current_row(row)

                    # Nach jedem Messpunkt sofort speichern,
                    # damit bei Abbruch nichts verloren geht.
                    save_rows_to_csv(rows, CSV_FILE)

        except KeyboardInterrupt:
            print("\nTest wurde mit Ctrl+C abgebrochen.")

        finally:
            # Am Ende immer RF-Ausgang ausschalten
            send(sock, ":OUTP OFF")
            print("\nRF-Ausgang ausgeschaltet.")

    # Abschließend noch einmal speichern
    save_rows_to_csv(rows, CSV_FILE)
    print(f"\nFertig. CSV gespeichert unter:")
    print(Path(CSV_FILE).resolve())


if __name__ == "__main__":
    main()
