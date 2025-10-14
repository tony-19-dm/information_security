import os
import random
import struct
from typing import List, Tuple
from lab1 import ferm_test, fast_pow

def choose_block_size_for_p(p: int) -> int:  
    if p <= 2:
        raise ValueError("p слишком мало")
    k = (p.bit_length() - 1) // 8
    if k < 1:
        k = 1
    return k

def elgamal_encrypt_block(m: int, p: int, g: int, y: int) -> Tuple[int,int]:
    k = random.randint(2, p - 2)
    a = fast_pow(g, k, p)
    yk = fast_pow(y, k, p)
    b = (m * yk) % p
    return a, b

def elgamal_decrypt_block(a: int, b: int, p: int, x: int) -> int:
    ax_inv = fast_pow(a, (p - 1 - x), p)
    m = (b * ax_inv) % p
    return m

def save_encrypted_file_bin(filename: str, p: int, g: int, y: int, x_or_0: int,
                            encrypted_pairs: List[Tuple[int,int]], original_size: int, block_size: int):
    with open(filename, 'wb') as f:
        header = struct.pack('<6Q', p, g, y, x_or_0, original_size, block_size)
        f.write(header)
        f.write(struct.pack('<I', len(encrypted_pairs)))
        for a, b in encrypted_pairs:
            f.write(struct.pack('<2Q', a, b))

def load_encrypted_file_bin(filename: str):
    with open(filename, 'rb') as f:
        hdr = f.read(48)
        if len(hdr) != 48:
            raise ValueError("Неправильный/повреждённый зашифрованный файл (header).")
        p, g, y, x_or_0, original_size, block_size = struct.unpack('<6Q', hdr)
        cnt_bytes = f.read(4)
        if len(cnt_bytes) != 4:
            raise ValueError("Неправильный/повреждённый зашифрованный файл (count).")
        count = struct.unpack('<I', cnt_bytes)[0]
        pairs = []
        for _ in range(count):
            pair_bytes = f.read(16)
            if len(pair_bytes) != 16:
                raise ValueError("Неправильный/повреждённый зашифрованный файл (pairs).")
            a, b = struct.unpack('<2Q', pair_bytes)
            pairs.append((a, b))
    return p, g, y, x_or_0, original_size, block_size, pairs

def elgamal_file_full_cycle():
    input_file = input("Путь к файлу для шифрования (любой формат): ").strip()
    if not os.path.exists(input_file):
        print("Файл не найден.")
        return

    choice = input("Ввести p,g,x вручную? (y/n) ").strip().lower()
    if choice == 'y':
        while True:
            p = int(input("p (простое число) = "))
            if ferm_test(p):
                break
        while True:
            g = int(input("g = "))
            if fast_pow(g, (p - 1) // 2, p) != 1:
                break
            else:
                print("g не удовлетворяет условию")
        while True:
            x = int(input("x (1 < x < p) = "))
            if 1 < x < p:
                break
    else:
        while True:
            p = random.randint(1000000, 100000000)
            if ferm_test(p):
                break

        while True:
            g = random.randint(2, p - 2)
            if fast_pow(g, (p - 1) // 2, p) != 1:
                break
        x = random.randint(2, p - 1)
        y = fast_pow(g, x, p)
        print(f"Сгенерировано: p={p}, g={g}, y={y}, x={x}")

    with open(input_file, 'rb') as f:
        data = f.read()
    original_size = len(data)

    block_size = choose_block_size_for_p(p)
    print(f"Использовать блоки по {block_size} байт (каждый блок < p).")

    encrypted_pairs = []
    for i in range(0, len(data), block_size):
        block = data[i:i+block_size]
        if len(block) < block_size:
            block = block + b'\x00' * (block_size - len(block))
        m = int.from_bytes(block, byteorder='big')
        if m >= p:
            raise ValueError(f"Момент: числовой блок m = {m} не меньше p = {p}. Увеличьте p или уменьшите block_size.")
        a, b = elgamal_encrypt_block(m, p, g, y)
        encrypted_pairs.append((a, b))

    enc_path = "eg_enc" + input_file
    x_or_0 = x if x != 0 else 0
    save_encrypted_file_bin(enc_path, p, g, y, x_or_0, encrypted_pairs, original_size, block_size)
    print(f"Файл зашифрован и сохранён как: {enc_path}")

    p2, g2, y2, x_saved, original_size2, block_size2, pairs_loaded = load_encrypted_file_bin(enc_path)

    if p2 != p or g2 != g or y2 != y:
        print("Внимание: параметры в загруженном файле не равны используемым (неожиданно).")
    if x_saved != 0:
        x_to_use = x_saved
        print("Использую сохранённый приватный ключ x из файла для расшифровки.")
    else:
        x_to_use = int(input("Введите приватный ключ x (для расшифровки): ").strip())

    decrypted = bytearray()
    for a,b in pairs_loaded:
        m = elgamal_decrypt_block(a, b, p2, x_to_use)
        block_bytes = m.to_bytes(block_size2, byteorder='big')
        decrypted.extend(block_bytes)

    decrypted = bytes(decrypted[:original_size2])

    dec_path = "eg_dec_" + input_file
    with open(dec_path, 'wb') as f:
        f.write(decrypted)
    print(f"Расшифрованный файл сохранён как: {dec_path}")

    if decrypted == data:
        print("Проверка: исходный файл и расшифрованный идентичны (OK).")
    else:
        print("Проверка: файлы НЕ совпадают! (ERROR)")

if __name__ == "__main__":
    elgamal_file_full_cycle()
