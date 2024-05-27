import random


def generate_mac_address() -> str:

    # Generiere sechs zufällige Hexadezimalzahlen im Bereich von 0x00 bis 0xFF
    random_bytes = [random.randint(0x00, 0xFF) for _ in range(6)]

    # Konvertiere die Zahlen in Hexadezimalstrings und füge sie mit ':' zusammen
    mac_address = ":".join("{:02X}".format(byte) for byte in random_bytes)
    return mac_address
