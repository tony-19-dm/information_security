import os
import random
import struct
from typing import List, Tuple
from lab1 import ferm_test, fast_pow, extended_gcd

def choose_block_size_for_N(N: int) -> int:
    if N <= 2:
        raise ValueError("N слишком мало")
    k = (N.bit_length() - 1) // 8
    if k < 1:
        k = 1
    return k

def save_encrypted_file_bin(filename: str, N: int, d: int, c_or_0: int,
                            encrypted_vals: List[int], original_size: int, block_size: int):
    reserved = 0
    with open(filename, 'wb') as f:
        header = struct.pack('<6Q', N, d, c_or_0, original_size, block_size, reserved)
        f.write(header)
        f.write(struct.pack('<I', len(encrypted_vals)))
        for val in encrypted_vals:
            f.write(struct.pack('<Q', val))

def load_encrypted_file_bin(filename: str):
    with open(filename, 'rb') as f:
        hdr = f.read(48)
        if len(hdr) != 48:
            raise ValueError("Неверный/повреждённый зашифрованный файл (header).")
        N, d, c_or_0, original_size, block_size, _ = struct.unpack('<6Q', hdr)
        cnt_bytes = f.read(4)
        if len(cnt_bytes) != 4:
            raise ValueError("Неверный/повреждённый зашифрованный файл (count).")
        count = struct.unpack('<I', cnt_bytes)[0]
        vals = []
        for _ in range(count):
            val_bytes = f.read(8)
            if len(val_bytes) != 8:
                raise ValueError("Неверный/повреждённый зашифрованный файл (values).")
            v = struct.unpack('<Q', val_bytes)[0]
            vals.append(v)
    return N, d, c_or_0, original_size, block_size, vals

def rsa_encrypt_block(m: int, N: int, d: int) -> int:
    # e = m^d mod N   (по вашей нотации)
    return fast_pow(m, d, N)

def rsa_decrypt_block(e_val: int, N: int, c: int) -> int:
    # m = e^c mod N
    return fast_pow(e_val, c, N)

def rsa_file_full_cycle():
    input_file = input("Введите путь к файлу для шифрования (любой формат): ").strip()
    if not os.path.exists(input_file):
        print("Файл не найден.")
        return

    choice = input("Ввести p,q,d вручную? (y/n) ").strip().lower()
    if choice == 'y':
        while True:
            q = int(input("q (простое число) = "))
            if ferm_test(q):
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

        d = int(input("d (открытый ключ Боба) = ").strip())
        if not ferm_test(p) or not ferm_test(q):
            print("Внимание: p или q не прошли тест простоты (ferm_test). Результат может быть некорректен.")
        N = p * q
        phi = (p - 1) * (q - 1)
        gcd_res = extended_gcd(d, phi)
        if gcd_res[0] != 1:
            print("Внимание: введённый d не взаимно прост с phi; необходимо выбрать другое d.")
            return
        c = gcd_res[1] % phi
        x_saved = 0
    else:
        
        while True:
            q = random.randint(1000000, 1000000000)
            if ferm_test(q):
                p_temp = 2 * q + 1
                if ferm_test(p_temp):
                    p = p_temp
                    break
        
        N = p * q
        phi = (p - 1) * (q - 1)
        while True:
            d = random.randint(2, phi - 1)
            if extended_gcd(d, phi)[0] == 1:
                break
        g, xinv, y = extended_gcd(d, phi)
        c = xinv % phi
        print(f"Сгенерировано: p={p}, q={q}, N={N}, d={d}, c(приватный)={c}")
        x_saved = c

    print(f"Будем работать с N = {N}. Проверка размера блоков ...")
    with open(input_file, 'rb') as f:
        data = f.read()
    original_size = len(data)

    block_size = choose_block_size_for_N(N)
    print(f"Используется block_size = {block_size} байт (каждый блок < N).")

    encrypted_values = []
    for i in range(0, len(data), block_size):
        block = data[i:i+block_size]
        if len(block) < block_size:
            block = block + b'\x00' * (block_size - len(block))
        m = int.from_bytes(block, byteorder='big')
        if m >= N:
            raise ValueError(f"Числовой блок m = {m} >= N = {N}. Увеличьте N или уменьшите block_size.")
        e_val = rsa_encrypt_block(m, N, d)
        encrypted_values.append(e_val)

    enc_path = "rsa_enc_" + input_file
    save_encrypted_file_bin(enc_path, N, d, x_saved, encrypted_values, original_size, block_size)
    print(f"Зашифрованный файл сохранён: {enc_path}")

    N2, d2, c_or_0, original_size2, block_size2, vals_loaded = load_encrypted_file_bin(enc_path)
    if N2 != N:
        print("Внимание: N в загруженном файле не совпадает с ожидаемым.")
    if c_or_0 != 0:
        c_to_use = c_or_0
        print("Использую сохранённый приватный ключ c для расшифровки.")
    else:
        c_to_use = int(input("Введите приватный ключ c для расшифровки: ").strip())

    decrypted = bytearray()
    for e_val in vals_loaded:
        m = rsa_decrypt_block(e_val, N2, c_to_use)
        block_bytes = m.to_bytes(block_size2, byteorder='big')
        decrypted.extend(block_bytes)

    decrypted = bytes(decrypted[:original_size2])
    dec_path = "rsa_dec_" + input_file
    with open(dec_path, 'wb') as f:
        f.write(decrypted)
    print(f"Расшифрованный файл сохранён: {dec_path}")

    if decrypted == data:
        print("Проверка успешна: исходный и расшифрованный файлы идентичны.")
    else:
        print("Проверка НЕ пройдена: файлы отличаются!")

if __name__ == "__main__":
    rsa_file_full_cycle()
