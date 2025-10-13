import os
import random
import struct
from lab1 import fast_pow as fast_exponentiation, ferm_test as ferm, extended_gcd as Evkl


# ---------- Шаги Шамира ----------
def Shamir(p, m, Ca, Da, Cb, Db):
    x1 = fast_exponentiation(m, Ca, p)
    x2 = fast_exponentiation(x1, Cb, p)
    x3 = fast_exponentiation(x2, Da, p)
    x4 = fast_exponentiation(x3, Db, p)
    return x4


# ---------- Основная функция ----------
def shamir_full_cycle():
    input_file = input("Введите путь к файлу (любой формат, например .png): ").strip()
    if not os.path.exists(input_file):
        print("Файл не найден!")
        return
    
    # --- Шаг 1: Шифрование ---
    print("\n🔒 Шифрование файла...")
    p, Ca, Cb, Da, Db, encrypted_blocks, original_size = shamir_encrypt_file(input_file)
    
    enc_file = "enc_" + input_file
    save_encrypted_binary(enc_file, p, Ca, Cb, Da, Db, encrypted_blocks, original_size)
    print(f"✅ Файл зашифрован → {enc_file}")
    
    # --- Шаг 2: Расшифрование ---
    print("\n🔓 Расшифрование файла...")
    p, Ca, Cb, Da, Db, encrypted_blocks, original_size = load_encrypted_binary(enc_file)
    decrypted_data = shamir_decrypt_file(encrypted_blocks, p, Db, original_size)
    
    dec_file = "dec_" + input_file
    with open(dec_file, 'wb') as f:
        f.write(decrypted_data)
    print(f"✅ Файл расшифрован → {dec_file}")
    
    # --- Шаг 3: Проверка ---
    with open(input_file, 'rb') as f:
        original_data = f.read()
    
    if original_data == decrypted_data:
        print("\n🎉 Проверка успешна: исходный и расшифрованный файлы совпадают!")
    else:
        print("\n⚠️ Ошибка: файлы не совпадают!")
    
    print("\n--- Цикл завершён ---")


# ---------- Шифрование ----------
def shamir_encrypt_file(input_file, p=None, Ca=None, Cb=None):
    if p is None and Ca is None and Cb is None:
        while True:
            p = random.getrandbits(32)
            if ferm(p):
                break
        while True:
            Ca = random.randint(2, p-2)
            if Evkl(Ca, p-1)[0] == 1:
                break
        while True:
            Cb = random.randint(2, p-2)
            if Evkl(Cb, p-1)[0] == 1:
                break
        print(f"p = {p}\nCa = {Ca}\nCb = {Cb}")
    
    # Проверки
    if not ferm(p):
        raise ValueError("p должно быть простым числом")
    
    if Evkl(Ca, p-1)[0] != 1 or Evkl(Cb, p-1)[0] != 1:
        raise ValueError("Ca и Cb должны быть взаимно просты с p-1")
    
    # Вычисляем Da и Db
    _, Da, _ = Evkl(Ca, p-1)
    Da %= (p-1)
    _, Db, _ = Evkl(Cb, p-1)
    Db %= (p-1)
    print(f"Da = {Da}, Db = {Db}")
    
    with open(input_file, 'rb') as f:
        file_data = f.read()
    
    encrypted_blocks = []
    for i in range(0, len(file_data), 3):
        block = file_data[i:i+3]
        if len(block) < 3:
            block += b'\x00' * (3 - len(block))
        m = int.from_bytes(block, byteorder='big')
        if m >= p:
            raise ValueError(f"Блок данных слишком большой для p={p}")
        
        X1 = fast_exponentiation(m, Ca, p)
        X2 = fast_exponentiation(X1, Cb, p)
        X3 = fast_exponentiation(X2, Da, p)
        encrypted_blocks.append((X1, X2, X3))
    
    return p, Ca, Cb, Da, Db, encrypted_blocks, len(file_data)


# ---------- Расшифрование ----------
def shamir_decrypt_file(encrypted_blocks, p, Db, original_size):
    decrypted_data = b''
    for X1, X2, X3 in encrypted_blocks:
        X4 = fast_exponentiation(X3, Db, p)
        block_data = X4.to_bytes(3, byteorder='big')
        decrypted_data += block_data
    return decrypted_data[:original_size]


# ---------- Сохранение бинарного зашифрованного файла ----------
def save_encrypted_binary(filename, p, Ca, Cb, Da, Db, encrypted_blocks, original_size):
    with open(filename, 'wb') as f:
        # сохраняем заголовок (структурировано)
        f.write(struct.pack('<6Q', p, Ca, Cb, Da, Db, original_size))
        # сохраняем количество блоков
        f.write(struct.pack('<I', len(encrypted_blocks)))
        # сохраняем каждый блок как три числа
        for X1, X2, X3 in encrypted_blocks:
            f.write(struct.pack('<3Q', X1, X2, X3))


# ---------- Загрузка бинарного зашифрованного файла ----------
def load_encrypted_binary(filename):
    with open(filename, 'rb') as f:
        p, Ca, Cb, Da, Db, original_size = struct.unpack('<6Q', f.read(48))
        block_count = struct.unpack('<I', f.read(4))[0]
        encrypted_blocks = []
        for _ in range(block_count):
            X1, X2, X3 = struct.unpack('<3Q', f.read(24))
            encrypted_blocks.append((X1, X2, X3))
    return p, Ca, Cb, Da, Db, encrypted_blocks, original_size


# ---------- Точка входа ----------
if __name__ == "__main__":
    shamir_full_cycle()
