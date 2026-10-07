
import asyncio
import struct
import zlib

from bleak import BleakClient


MAC_ADDRESS = "93:EB:AB:37:E2:54"
WRITE_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"


FONT_MAP = {

    # MAIÚSCULAS
    "A": bytes.fromhex("1c366363637f63636363"),
    "B": bytes.fromhex("3f6666663e666666663f"),
    "C": bytes.fromhex("3c66430303030343663c"),
    "D": bytes.fromhex("1f36666666666666361f"),
    "E": bytes.fromhex("7f6606263e260606667f"),
    "F": bytes.fromhex("7f6606263e260606060f"),
    "G": bytes.fromhex("3e63630303037363633e"),
    "H": bytes.fromhex("636363637f6363636363"),
    "I": bytes.fromhex("3c18181818181818183c"),
    "J": bytes.fromhex("3c1818181818181b1b0e"),
    "K": bytes.fromhex("6333331b0f0f1b336363"),
    "L": bytes.fromhex("0f06060606060646667f"),
    "M": bytes.fromhex("636377777f6b6b6b6363"),
    "N": bytes.fromhex("636367676f7b73636363"),
    "O": bytes.fromhex("3e63636363636363633e"),
    "P": bytes.fromhex("3f666666663e0606060f"),
    "Q": bytes.fromhex("3e63636363636b6b3e60"),
    "R": bytes.fromhex("3f6666663e1e36666667"),
    "S": bytes.fromhex("3e6303030e386060633e"),
    "T": bytes.fromhex("7e5a181818181818183c"),
    "U": bytes.fromhex("6363636363636363633e"),
    "V": bytes.fromhex("63636363636363361c08"),
    "W": bytes.fromhex("6363636b6b6b7f776363"),
    "X": bytes.fromhex("636363361c1c36636363"),
    "Y": bytes.fromhex("66666666663c18183c00"),
    "Z": bytes.fromhex("7f636130180c0643637f"),

    # MINÚSCULAS
    "a": bytes.fromhex("001e303e33333b6e0000"),
    "b": bytes.fromhex("0706063e66666666663f"),
    "c": bytes.fromhex("00003e63030303633e00"),
    "d": bytes.fromhex("3830303e333333337e00"),
    "e": bytes.fromhex("00003e63637f03633e00"),
    "f": bytes.fromhex("386c0c0c3f0c0c0c0c1e"),
    "g": bytes.fromhex("006e736363736e60633e"),
    "h": bytes.fromhex("0706063e666666666667"),
    "i": bytes.fromhex("1818001c18181818183c"),
    "j": bytes.fromhex("30383030303030303333"),
    "k": bytes.fromhex("0706066666361e366667"),
    "l": bytes.fromhex("18181818181818181838"),
    "m": bytes.fromhex("0000367f6b6b63636363"),
    "n": bytes.fromhex("0000003b666666666666"),
    "o": bytes.fromhex("00003e6363636363633e"),
    "p": bytes.fromhex("00003b6666663e06060f"),
    "q": bytes.fromhex("006e33333333333e3030"),
    "r": bytes.fromhex("00003b66060606060f00"),
    "s": bytes.fromhex("00003e63033e60633e00"),
    "t": bytes.fromhex("0c0c0c3f0c0c0c0c6c38"),
    "u": bytes.fromhex("0000333333333333336e"),
    "v": bytes.fromhex("00006363636363361c08"),
    "w": bytes.fromhex("000063636b6b6b7f3600"),
    "x": bytes.fromhex("00006363361c36636300"),
    "y": bytes.fromhex("0063636363733360633e"),
    "z": bytes.fromhex("7f6130180c06467f0000"),

    # ESPAÇO
    " ": bytes(10),

    # DÍGITOS
    "0": bytes.fromhex("3c66c3c3c3c3c3c3663c"),
    "1": bytes.fromhex("1838781818181818187e"),
    "2": bytes.fromhex("3c66c303060c183060ff"),
    "3": bytes.fromhex("3c6603033e0303c3663c"),
    "4": bytes.fromhex("060f1b3363c3ff030303"),
    "5": bytes.fromhex("ffc0c0c0fe030303663c"),
    "6": bytes.fromhex("3c60c0c0fec3c3c3663c"),
    "7": bytes.fromhex("ff03060c0c1818303000"),
    "8": bytes.fromhex("3c66c3663c66c3c3663c"),
    "9": bytes.fromhex("3c66c3c37f0303060c3c"),

    # PONTUAÇÃO
    "!": bytes.fromhex("0000001e303e33333b6e"),
    "?": bytes.fromhex("183c3c3c3c1818001818"),
    ".": bytes.fromhex("00000000000000000018"),
    ",": bytes.fromhex("00000000000000001830"),
    ":": bytes.fromhex("00000018180000181800"),
    "-": bytes.fromhex("00000000007e00000000"),
    "'": bytes.fromhex("18183000000000000000"),
    '"': bytes.fromhex("66666600000000000000"),
    "(": bytes.fromhex("0c183030303030180c00"),
    ")": bytes.fromhex("30180c0c0c0c0c183000"),
    "/": bytes.fromhex("03060c18303060c00000"),
}


def build_first_char(char, rgb):
    return (
        bytes(rgb)
        + bytes(5)
        + bytes(rgb)
        + bytes(3)
        + FONT_MAP[char]
        + bytes(3)
    )


def build_next_char(char, rgb):
    return (
        bytes(1)
        + bytes(rgb)
        + bytes(3)
        + FONT_MAP[char]
        + bytes(3)
    )


def generate_write_5(text, seq, rgb):

    

    for char in text:
        if char not in FONT_MAP:
            raise ValueError(f"Caractere não mapeado: {char}")

    # Quantidade de caracteres
    data = bytes([len(text)])

    # Configuração
    data += bytes.fromhex("000101015000")

    # Primeiro caractere
    data += build_first_char(text[0], rgb)

    # Demais caracteres
    for char in text[1:]:
        data += build_next_char(char, rgb)

    # CRC
    crc = zlib.crc32(data) & 0xffffffff
    crc_bytes = struct.pack("<I", crc)

    # Tamanhos
    internal_length = len(data)
    total_length = 15 + internal_length

    return (
        struct.pack("<H", total_length)
        + bytes.fromhex("000100")
        + struct.pack("<I", internal_length)
        + crc_bytes
        + bytes([0x00, seq])
        + data
    )


async def main():

    texto = "THE DREAM IS NOT DEAD"

    # COR
    rgb = (157, 0, 255)

    # ================================================
    # WRITE 1
    # LAO
    # ================================================

    write_1 = bytes.fromhex(
        "080001800b110900"
    )

    # ================================================
    # WRITE 2
    # FIXO
    # ================================================

    write_2 = bytes.fromhex(
        "04000580"
    )

    # ================================================
    # WRITE 3
    # FIXO
    # ================================================

    write_3 = bytes.fromhex(
        "0500128001"
    )

    # ================================================
    # WRITE 4
    # LAO
    # ================================================

    write_4 = bytes.fromhex(
        "0700088001000a"
    )

    # ================================================
    # WRITE 5
    # ================================================

    write_5 = generate_write_5(
        texto,
        0x0A,
        rgb
    )

    packets = [
        write_1,
        write_2,
        write_3,
        write_4,
        write_5,
    ]

    print("=" * 70)
    print("TESTE DE COR")
    print("Texto:", texto)
    print("RGB:", rgb)
    print("=" * 70)

    for i, packet in enumerate(packets, 1):
        print(f"Write {i}: {len(packet)} bytes")
        print(packet.hex())
        print()

    print("Conectando...")

    async with BleakClient(MAC_ADDRESS) as client:

        print("Conectado!")

        for i, packet in enumerate(packets, 1):

            print(f"Enviando Write {i}...")

            await client.write_gatt_char(
                WRITE_UUID,
                packet,
                response=False
            )

            await asyncio.sleep(0.2)

    print()
    print("TEXTO ENVIADO COM SUCESSO!")


if __name__ == "__main__":
    asyncio.run(main())
