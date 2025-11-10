import hashlib
import random
from lab1 import ferm_test, extended_gcd, fast_pow

class RSASignature:
    def __init__(self):
        self.p = 0
        self.q = 0
        self.n = 0
        self.phi = 0
        self.d = 0  # открытый ключ
        self.c = 0  # закрытый ключ
    
    def generate_keys(self):
        """Генерация ключей RSA"""
        # Генерируем простые числа в диапазоне 32500-45000
        while(True):
            self.p = random.randint(32500, 45000)
            if ferm_test(self.p):
                break

        while(True):
            self.q = random.randint(32500, 45000)
            if ferm_test(self.q):
                break
        
        # Вычисляем параметры
        self.n = self.p * self.q
        self.phi = (self.p - 1) * (self.q - 1)
        
        # Выбираем d (открытый ключ)
        while True:
            self.d = random.randint(2, self.phi - 1)
            if extended_gcd(self.d, self.phi)[0] == 1:
                break
        
        # Вычисляем c (закрытый ключ)
        self.c = self._mod_inverse(self.d, self.phi)
        
        print(f"Сгенерированы ключи:")
        print(f"p = {self.p}")
        print(f"q = {self.q}")
        print(f"N = {self.n}")
        print(f"φ(N) = {self.phi}")
        print(f"Открытый ключ (d) = {self.d}")
        print(f"Закрытый ключ (c) = {self.c}")
    
    def _mod_inverse(self, a, m):
        """Вычисление обратного элемента по модулю"""
        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            raise ValueError("Обратный элемент не существует")
        return x % m
    
    def sign_file(self, filename, output_filename=None):
        """Подпись файла"""
        if self.c == 0 or self.n == 0:
            raise ValueError("Сначала сгенерируйте ключи!")
        
        # Чтение файла
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        # Вычисление хеша (SHA-256)
        file_hash = hashlib.sha256(file_data).digest()
        
        print(f"Хеш файла: {file_hash.hex()}")
        
        # Подпись каждого байта хеша
        signature_bytes = []
        for byte in file_hash:
            # Преобразуем байт в число
            h = byte
            # Подписываем: s = h^c mod N
            s = fast_pow(h, self.c, self.n)
            signature_bytes.append(s)
        
        # Сохраняем подпись
        if output_filename is None:
            output_filename = filename + '.sig'
        
        with open(output_filename, 'w') as f:
            # Сохраняем подпись как числа, разделенные пробелами
            f.write(' '.join(str(x) for x in signature_bytes))
        
        print(f"Подпись сохранена в файл: {output_filename}")
        return signature_bytes
    
    def verify_signature(self, filename, signature_filename):
        """Проверка подписи"""
        if self.d == 0 or self.n == 0:
            raise ValueError("Сначала сгенерируйте ключи!")
        
        # Чтение исходного файла
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        # Вычисление хеша
        file_hash = hashlib.sha256(file_data).digest()
        
        # Чтение подписи
        with open(signature_filename, 'r') as f:
            signature_data = f.read().strip()
        
        signature_bytes = [int(x) for x in signature_data.split()]
        
        # Проверка подписи для каждого байта
        is_valid = True
        for i, (byte, s) in enumerate(zip(file_hash, signature_bytes)):
            # Проверяем: e = s^d mod N должно равняться h
            e = fast_pow(s, self.d, self.n)
            if e != byte:
                print(f"Ошибка проверки для байта {i}: ожидалось {byte}, получено {e}")
                is_valid = False
        
        return is_valid
    
    def save_public_key(self, filename):
        """Сохранение открытого ключа"""
        with open(filename, 'w') as f:
            f.write(f"{self.n}\n{self.d}")
        print(f"Открытый ключ сохранен в: {filename}")
    
    def load_public_key(self, filename):
        """Загрузка открытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.n = int(lines[0].strip())
        self.d = int(lines[1].strip())
        print(f"Открытый ключ загружен: N={self.n}, d={self.d}")
    
    def save_private_key(self, filename):
        """Сохранение закрытого ключа"""
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.q}\n{self.n}\n{self.phi}\n{self.d}\n{self.c}")
        print(f"Закрытый ключ сохранен в: {filename}")
    
    def load_private_key(self, filename):
        """Загрузка закрытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.q = int(lines[1].strip())
        self.n = int(lines[2].strip())
        self.phi = int(lines[3].strip())
        self.d = int(lines[4].strip())
        self.c = int(lines[5].strip())
        print(f"Закрытый ключ загружен")

def main():
    rsa = RSASignature()
    
    while True:
        print("\n=== Система электронной подписи RSA ===")
        print("1. Сгенерировать новые ключи")
        print("2. Подписать файл")
        print("3. Проверить подпись")
        print("4. Сохранить ключи")
        print("5. Загрузить ключи")
        print("6. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            rsa.generate_keys()
        
        elif choice == '2':
            filename = input("Введите имя файла для подписи: ")
            try:
                signature = rsa.sign_file(filename)
                print("Файл успешно подписан!")
            except Exception as e:
                print(f"Ошибка при подписи: {e}")
        
        elif choice == '3':
            filename = input("Введите имя файла для проверки: ")
            signature_file = input("Введите имя файла с подписью: ")
            try:
                if rsa.verify_signature(filename, signature_file):
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
                filename = input("Введите имя файла: ")
                rsa.save_public_key(filename)
            elif key_choice == '2':
                filename = input("Введите имя файла: ")
                rsa.save_private_key(filename)
        
        elif choice == '5':
            print("1. Загрузить открытый ключ")
            print("2. Загрузить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                filename = input("Введите имя файла: ")
                rsa.load_public_key(filename)
            elif key_choice == '2':
                filename = input("Введите имя файла: ")
                rsa.load_private_key(filename)
        
        elif choice == '6':
            break
        
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()