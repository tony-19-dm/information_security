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
        while True:
            q = int(input("q (простое число) = "))
            if ferm_test(q):
                # Проверяем условие p = 2 * q + 1 и простоту p
                p_candidate = 2 * q + 1
                if ferm_test(p_candidate):
                    p = p_candidate
                    print(f"p = 2*q + 1 = {p} (простое число)")
                    break
                else:
                    print(f"q - простое, но p = 2*q + 1 = {p_candidate} не является простым")
                    print("Введите другое q")
            else:
                print("q - не простое, введите q повторно")
        
        while True:
            g = int(input("g (1 < a < p - 1) = "))
            if 1 < g < p - 1:
                if fast_pow(g, q, p) != 1:
                    break
                print("не выполняется условие g^q mod p != 1")
            else:
                print("g должно быть в диапазоне (1, p - 1)")
        
        while True:
            Xa = int(input("(секретный ключ Алисы) Xa = "))
            if 1 <= Xa < p:
                break
            else:
                print("Xa должно быть в диапазоне [1, p)")

        while True:
            Xb = int(input("(секретный ключ Боба) Xb = "))
            if 1 <= Xb < p:
                break
            else:
                print("Xb должно быть в диапазоне [1, p)")
        
    else:
        while True:
            q = random.randint(1000000, 1000000000)
            if ferm_test(q):
                p_temp = 2 * q + 1
                if ferm_test(p_temp):
                    p = p_temp
                    break
        
        # Генерация g - первообразного корня по модулю p
        while True:
            g = random.randint(2, p - 2)
            if fast_pow(g, q, p) != 1:  # проверка условия g^q mod p != 1
                break
        
        # Генерация секретных ключей
        Xa = random.randint(1, p - 1)
        Xb = random.randint(1, p - 1)
        print(f"Сгенерировано: p={p}, g={g}, a(Алиса)={Xa}, b(Боб)={Xb}")

    A = fast_pow(g, Xa, p)
    B = fast_pow(g, Xb, p)
    return p, g, Xa, Xb, A, B

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

    # Diffi
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

    # Diffi
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
