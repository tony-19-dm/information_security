import hashlib
import random
from lab1 import ferm_test, extended_gcd, fast_pow

class GOSTSignature:
    def __init__(self):
        self.p = 0  # большое простое число
        self.q = 0  # простой делитель p-1
        self.a = 0  # элемент порядка q
        self.x = 0  # закрытый ключ
        self.y = 0  # открытый ключ
    
    def generate_keys(self):
        """Генерация ключей по ГОСТ Р 34.10-94"""
        while True:
            self.q = random.randint(2**15, 2**16)
            if ferm_test(self.q):
                break
        
        k = 1
        while True:
            self.p = k * self.q + 1
            if ferm_test(self.p):
                break
            k += 1
        
        while True:
            h = random.randint(2, self.p - 2)
            self.a = fast_pow(h, (self.p - 1) // self.q, self.p)
            if self.a != 1:
                break

        self.x = random.randint(1, self.q - 1)
        
        self.y = fast_pow(self.a, self.x, self.p)
        
        print(f"Сгенерированы ключи по ГОСТ Р 34.10-94:")
        print(f"p = {self.p}")
        print(f"q = {self.q}")
        print(f"a = {self.a}")
        print(f"Закрытый ключ (x) = {self.x}")
        print(f"Открытый ключ (y) = {self.y}")
    
    def _mod_inverse(self, a, m):
        """Вычисление обратного элемента по модулю"""
        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            raise ValueError("Обратный элемент не существует")
        return x % m
    
    def sign_file(self, filename, output_filename=None):
        """Подпись файла по ГОСТ Р 34.10-94 (побайтовая подпись хеша)"""
        if self.p == 0 or self.q == 0 or self.a == 0 or self.x == 0:
            raise ValueError("Сначала сгенерируйте ключи!")
        
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        file_hash = hashlib.sha256(file_data).digest()
        
        print(f"Хеш файла: {file_hash.hex()}")
        
        r_list = []
        s_list = []
        
        for byte in file_hash:
            h = byte
            
            while True:
                k = random.randint(1, self.q - 1)
                
                # r = (a^k mod p) mod q
                r = fast_pow(self.a, k, self.p) % self.q
                
                if r == 0:
                    continue  # если r=0, генерируем новое k
                
                # s = (k * h + x * r) mod q
                s = (k * h + self.x * r) % self.q
                
                if s == 0:
                    continue  # если s=0, генерируем новое k
                
                r_list.append(r)
                s_list.append(s)
                break
        
        if output_filename is None:
            output_filename = filename + '.sig'
        
        with open(output_filename, 'w') as f:
            f.write(' '.join(str(r) for r in r_list) + '\n')
            f.write(' '.join(str(s) for s in s_list))
        
        print(f"Подпись сохранена в файл: {output_filename}")
        print(f"Размер подписи: {len(r_list)} пар (r, s)")
        return (r_list, s_list)
    
    def verify_signature(self, filename, signature_filename):
        """Проверка подписи по ГОСТ Р 34.10-94 (побайтовая проверка)"""
        if self.p == 0 or self.q == 0 or self.a == 0 or self.y == 0:
            raise ValueError("Сначала сгенерируйте или загрузите ключи!")
        
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        file_hash = hashlib.sha256(file_data).digest()
        
        with open(signature_filename, 'r') as f:
            signature_data = f.readlines()
        
        if len(signature_data) < 2:
            raise ValueError("Неверный формат файла подписи")
        
        r_list = [int(r) for r in signature_data[0].strip().split()]
        s_list = [int(s) for s in signature_data[1].strip().split()]
        
        if len(r_list) != len(file_hash) or len(s_list) != len(file_hash):
            print(f"Ошибка: размер подписи не соответствует размеру хеша")
            return False
        
        print(f"Загружена подпись для {len(r_list)} байт хеша")
        print(f"Вычисленный хеш: {file_hash.hex()}")
        
        # Проверяем подпись для каждого байта
        valid_count = 0
        total_bytes = len(file_hash)
        
        for i, (h_byte, r, s) in enumerate(zip(file_hash, r_list, s_list)):
            # Проверяем условия: 0 < r < q и 0 < s < q
            if r <= 0 or r >= self.q:
                print(f"Ошибка: r[{i}] = {r} не удовлетворяет условию 0 < r < q")
                continue
            
            if s <= 0 or s >= self.q:
                print(f"Ошибка: s[{i}] = {s} не удовлетворяет условию 0 < s < q")
                continue
            
            # v = h^(q-2) mod q
            v = fast_pow(h_byte, self.q - 2, self.q)
            
            # z1 = s * v mod q
            z1 = (s * v) % self.q
            
            # z2 = (q - r) * v mod q
            z2 = ((self.q - r) * v) % self.q
            
            # u = (a^z1 * y^z2 mod p) mod q
            u = (fast_pow(self.a, z1, self.p) * fast_pow(self.y, z2, self.p)) % self.p
            u = u % self.q
            
            # Подпись верна, если u = r
            if u == r:
                valid_count += 1
            else:
                print(f"Ошибка проверки для байта {i}: h={h_byte}, r={r}, s={s}, u={u}")
        
        is_valid = (valid_count == total_bytes)
        
        if is_valid:
            print(f"✓ Подпись верна! Все {total_bytes} байт проверены успешно.")
        else:
            print(f"✗ Подпись неверна! Проверено {valid_count} из {total_bytes} байт.")
        
        return is_valid
    
    def save_public_key(self):
        """Сохранение открытого ключа"""
        filename = 'o'
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.q}\n{self.a}\n{self.y}")
        print(f"Открытый ключ сохранен в: {filename}")
    
    def load_public_key(self, filename):
        """Загрузка открытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.q = int(lines[1].strip())
        self.a = int(lines[2].strip())
        self.y = int(lines[3].strip())
        print(f"Открытый ключ загружен: p={self.p}, q={self.q}, a={self.a}, y={self.y}")
    
    def save_private_key(self):
        """Сохранение закрытого ключа"""
        filename = 'c'
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.q}\n{self.a}\n{self.x}\n{self.y}")
        print(f"Закрытый ключ сохранен в: {filename}")
    
    def load_private_key(self, filename):
        """Загрузка закрытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.q = int(lines[1].strip())
        self.a = int(lines[2].strip())
        self.x = int(lines[3].strip())
        self.y = int(lines[4].strip())
        print(f"Закрытый ключ загружен")

def main():
    gost = GOSTSignature()
    
    while True:
        print("\n=== Система электронной подписи ГОСТ Р 34.10-94 ===")
        print("1. Сгенерировать новые ключи")
        print("2. Подписать файл")
        print("3. Проверить подпись")
        print("4. Сохранить ключи")
        print("5. Загрузить ключи")
        print("6. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            gost.generate_keys()
        
        elif choice == '2':
            filename = input("Введите имя файла для подписи: ")
            try:
                signature = gost.sign_file(filename)
                print("Файл успешно подписан!")
            except Exception as e:
                print(f"Ошибка при подписи: {e}")
        
        elif choice == '3':
            filename = input("Введите имя файла для проверки: ")
            signature_file = input("Введите имя файла с подписью: ")
            try:
                if gost.verify_signature(filename, signature_file):
                    print("✓ Подпись верна!")
                else:
                    print("✗ Подпись неверна!")
            except Exception as e:
                print(f"Ошибка при проверке: {e}")
        
        elif choice == '4':
            print("1. Сохранить открытый ключ")
            print("2. Сохранить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                gost.save_public_key()
            elif key_choice == '2':
                gost.save_private_key()
        
        elif choice == '5':
            print("1. Загрузить открытый ключ")
            print("2. Загрузить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                filename = input("Введите имя файла: ")
                gost.load_public_key(filename)
            elif key_choice == '2':
                filename = input("Введите имя файла: ")
                gost.load_private_key(filename)
        
        elif choice == '6':
            break
        
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()