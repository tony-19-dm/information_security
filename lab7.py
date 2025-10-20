import os
import random
import struct
import hashlib
from typing import List, Tuple
from lab1 import ferm_test, fast_pow, extended_gcd

def derive_key_bytes_from_shared(shared_int: int, length: int) -> bytes:
    if shared_int == 0:
        shared_bytes = b'\x00'
    else:
        shared_bytes = shared_int.to_bytes((shared_int.bit_length() + 7) // 8, 'big')
    out = bytearray()
    counter = 0
    while len(out) < length:
        ctr_bytes = counter.to_bytes(4, 'big')
        digest = hashlib.sha256(shared_bytes + ctr_bytes).digest()
        out.extend(digest)
        counter += 1
    return bytes(out[:length])

def save_vernam_container(filename: str, p: int, g: int, A: int, B: int, original_size: int, b_or_0: int, ciphertext: bytes):
    with open(filename, 'wb') as f:
        header = struct.pack('<6Q', p, g, A, B, original_size, b_or_0)
        f.write(header)
        f.write(ciphertext)

def load_vernam_container(filename: str):
    with open(filename, 'rb') as f:
        hdr = f.read(48)
        if len(hdr) != 48:
            raise ValueError("Повреждённый контейнер (header).")
        p, g, A, B, original_size, b_or_0 = struct.unpack('<6Q', hdr)
        ciphertext = f.read()
    return p, g, A, B, original_size, b_or_0, ciphertext

def dh_generate_params_or_use_input():
    choice = input("Ввести p,g вручную? (y/n) ").strip().lower()
    if choice == 'y':
        p = int(input("p (простое) = ").strip())
        g = int(input("g = ").strip())
        if not ferm_test(p):
            print("Внимание: p не прошло тест простоты (ferm_test). Продолжаем, но результат может быть некорректен.")
        have_a = input("Ввести приватный ключ Алисы a вручную? (y/n) ").strip().lower() == 'y'
        if have_a:
            a = int(input("a (приватный Алисы) = ").strip())
        else:
            a = random.randint(2, p-2)
        have_b = input("Ввести приватный ключ Боба b вручную? (y/n) ").strip().lower() == 'y'
        if have_b:
            b = int(input("b (приватный Боба) = ").strip())
        else:
            b = random.randint(2, p-2)
    else:
        while True:
            p = random.getrandbits(32)
            if ferm_test(p):
                break
        g = random.randint(2, p-2)
        if g in (1, p-1):
            g = 2
        a = random.randint(2, p-2)
        b = random.randint(2, p-2)
        print(f"Сгенерировано: p={p}, g={g}, a(Алиса)={a}, b(Боб)={b}")

    A = fast_pow(g, a, p)
    B = fast_pow(g, b, p)
    return p, g, a, b, A, B

def vernam_dh_file_full_cycle():
    input_file = input("Введите путь к файлу для шифрования (любой формат): ").strip()
    if not os.path.exists(input_file):
        print("Файл не найден.")
        return

    p, g, a_priv, b_priv, A_pub, B_pub = dh_generate_params_or_use_input()

    with open(input_file, 'rb') as f:
        data = f.read()
    original_size = len(data)
    print(f"Исходный размер: {original_size} байт")

    shared_by_alice = fast_pow(B_pub, a_priv, p)
    shared_by_bob = fast_pow(A_pub, b_priv, p)
    if shared_by_alice != shared_by_bob:
        print("Ошибка: общий секрет не совпадает у сторон (что-то пошло не так).")
        return
    shared_secret = shared_by_alice
    key_bytes = derive_key_bytes_from_shared(shared_secret, original_size)

    # e_i = m_i ⊕ k_i
    ciphertext = bytes([data[i] ^ key_bytes[i] for i in range(original_size)])

    b_or_0 = b_priv if b_priv is not None else 0
    enc_path = "vtm_enc_" + input_file
    save_vernam_container(enc_path, p, g, A_pub, B_pub, original_size, b_or_0, ciphertext)
    print(f"Файл зашифрован и сохранён как: {enc_path}")

    p2, g2, A2, B2, orig_size2, b_or_0_loaded, ctext_loaded = load_vernam_container(enc_path)

    if b_or_0_loaded != 0:
        b_to_use = b_or_0_loaded
        print("Использую приватный ключ b из контейнера для расшифровки.")
    else:
        b_to_use = int(input("Введите приватный ключ b для расшифровки: ").strip())

    shared = fast_pow(A2, b_to_use, p2)
    key_for_decrypt = derive_key_bytes_from_shared(shared, orig_size2)

    # mi ​= ei ​⊕ ki
    decrypted = bytes([ctext_loaded[i] ^ key_for_decrypt[i] for i in range(orig_size2)])

    dec_path = "vtm_dec_" + input_file
    with open(dec_path, 'wb') as f:
        f.write(decrypted)
    print(f"Расшифрованный файл сохранён как: {dec_path}")

    if decrypted == data:
        print("Проверка успешна: исходный файл и расшифрованный идентичны.")
    else:
        print("Проверка НЕ пройдена: файлы отличаются!")

if __name__ == "__main__":
    vernam_dh_file_full_cycle()
