import os
import random
import struct
from lab1 import fast_pow, ferm_test as ferm, extended_gcd as Evkl

def Shamir(p, m, Ca, Da, Cb, Db):
    x1 = fast_pow(m, Ca, p)
    x2 = fast_pow(x1, Cb, p)
    x3 = fast_pow(x2, Da, p)
    x4 = fast_pow(x3, Db, p)
    return x4

def shamir_full_cycle():
    input_file = input("Введите путь к файлу (любой формат, например .png): ").strip()
    if not os.path.exists(input_file):
        print("Файл не найден!")
        return
    
    print("\nШифрование файла")
    p, Ca, Cb, Da, Db, encrypted_blocks, original_size = shamir_encrypt_file(input_file)
    
    enc_file = "enc_" + input_file
    save_encrypted_binary(enc_file, p, Ca, Cb, Da, Db, encrypted_blocks, original_size)
    print(f"Файл зашифрован → {enc_file}")
    
    print("\nРасшифрование файла")
    p, Ca, Cb, Da, Db, encrypted_blocks, original_size = load_encrypted_binary(enc_file)
    decrypted_data = shamir_decrypt_file(encrypted_blocks, p, Db, original_size)
    
    dec_file = "dec_" + input_file
    with open(dec_file, 'wb') as f:
        f.write(decrypted_data)
    print(f"Файл расшифрован → {dec_file}")
    
    with open(input_file, 'rb') as f:
        original_data = f.read()
    
    if original_data == decrypted_data:
        print("\nПроверка успешна: исходный и расшифрованный файлы совпадают!")
    else:
        print("\nОшибка: файлы не совпадают!")

def shamir_encrypt_file(input_file, p=None, Ca=None, Cb=None):
    print("Ввести числа вручную? (y/n): ")
    
    ans = input().strip().lower()
    
    if ans == 'y':
        while True:
            p = int(input("p (простое число) = "))
            if ferm(p):
                break

        while True:
            Ca = int(input("Ca = "))
            res = Evkl(Ca, p - 1)
            if res[0] == 1:
                break
            else:
                print("Ca должно быть взаимно простым с p - 1")

        while True:
            Da = int(input("Da = "))
            if Ca * Da % (p - 1) == 1:
                break
            else:
                print("Da должно быть взаимно обратным с Ca")

        while True:
            Cb = int(input("Cb = "))
            res = Evkl(Cb, p - 1)
            if res[0] == 1:
                break
            else:
                print("Cb должно быть взаимно простым с p - 1")
        
        while True:
            Db = int(input("Db = "))
            if Cb * Db % (p - 1) == 1:
                break
            else:
                print("Db должно быть взаимно обратным с Cb")

    elif ans == 'n':
        while True:
            p = random.randint(1000000, 100000000)
            if ferm(p):
                break
        print(f"p = {p}")
        
        while True:
            Ca = random.randint(2, p-2)
            res = Evkl(Ca, p - 1)
            if res[0] == 1:
                break
        
        Da = res[1]
        if Da < 0:
            Da += (p - 1)
        print(f"Ca = {Ca}, Da = {Da}")
        
        while True:
            Cb = random.randint(2, p-2)
            res = Evkl(Cb, p - 1)
            if res[0] == 1:
                break
        
        Db = res[1]
        if Db < 0:
            Db += (p - 1)
        print(f"Cb = {Cb}, Db = {Db}")
    
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
        
        X1 = fast_pow(m, Ca, p)
        X2 = fast_pow(X1, Cb, p)
        X3 = fast_pow(X2, Da, p)
        encrypted_blocks.append((X1, X2, X3))
    
    return p, Ca, Cb, Da, Db, encrypted_blocks, len(file_data)

def shamir_decrypt_file(encrypted_blocks, p, Db, original_size):
    decrypted_data = b''
    for X1, X2, X3 in encrypted_blocks:
        X4 = fast_pow(X3, Db, p)
        block_data = X4.to_bytes(3, byteorder='big')
        decrypted_data += block_data
    return decrypted_data[:original_size]

def save_encrypted_binary(filename, p, Ca, Cb, Da, Db, encrypted_blocks, original_size):
    with open(filename, 'wb') as f:
        f.write(struct.pack('<6Q', p, Ca, Cb, Da, Db, original_size))
        f.write(struct.pack('<I', len(encrypted_blocks)))
        for X1, X2, X3 in encrypted_blocks:
            f.write(struct.pack('<3Q', X1, X2, X3))

def load_encrypted_binary(filename):
    with open(filename, 'rb') as f:
        p, Ca, Cb, Da, Db, original_size = struct.unpack('<6Q', f.read(48))
        block_count = struct.unpack('<I', f.read(4))[0]
        encrypted_blocks = []
        for _ in range(block_count):
            X1, X2, X3 = struct.unpack('<3Q', f.read(24))
            encrypted_blocks.append((X1, X2, X3))
    return p, Ca, Cb, Da, Db, encrypted_blocks, original_size

if __name__ == "__main__":
    shamir_full_cycle()
