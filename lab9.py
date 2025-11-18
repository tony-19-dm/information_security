import hashlib
import random
from lab1 import ferm_test, extended_gcd, fast_pow

class ElGamalSignature:
    def __init__(self):
        self.q = 0
        self.p = 0
        self.g = 0
        self.x = 0  # закрытый ключ
        self.y = 0  # открытый ключ
    
    def generate_keys(self):
        """Генерация ключей Эль-Гамаля"""

        while True:
            self.q = random.randint(2**15, 2**16)
            if ferm_test(self.q):
                p_temp = 2 * self.q + 1
                if ferm_test(p_temp):
                    self.p = p_temp
                    break
        
        while True:
            self.g = random.randint(2, self.p - 2)
            if fast_pow(self.g, self.q, self.p) != 1:  # проверка условия g^q mod p != 1
                break

        self.x = random.randint(2, self.p - 2)
        
        self.y = fast_pow(self.g, self.x, self.p)
        
        print(f"Сгенерированы ключи Эль-Гамаля:")
        print(f"p = {self.p}")
        print(f"g = {self.g}")
        print(f"Закрытый ключ (x) = {self.x}")
        print(f"Открытый ключ (y) = {self.y}")
    
    def _mod_inverse(self, a, m):
        """Вычисление обратного элемента по модулю"""
        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            raise ValueError("Обратный элемент не существует")
        return x % m
    
    def sign_file(self, filename, output_filename=None):
        """Подпись файла по схеме Эль-Гамаля"""
        if self.p == 0 or self.g == 0 or self.x == 0:
            raise ValueError("Сначала сгенерируйте ключи!")
        
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        file_hash = hashlib.sha256(file_data).digest()
        # Преобразуем хеш в целое число
        h = int.from_bytes(file_hash, byteorder='big') % self.p
        
        print(f"Хеш файла: {file_hash.hex()}")
        print(f"Числовое представление хеша: {h}")
        
        # Генерируем случайное k, взаимно простое с p-1
        while True:
            k = random.randint(2, self.p - 2)
            if extended_gcd(k, self.p - 1)[0] == 1:
                break
        
        r = fast_pow(self.g, k, self.p)
        
        k_inv = self._mod_inverse(k, self.p - 1)
        u = (h - self.x * r) % (self.p - 1)
        s = (u * k_inv) % (self.p - 1)
        
        if output_filename is None:
            output_filename = filename + '.sig'
        
        # Сохраняем подпись (r, s)
        with open(output_filename, 'w') as f:
            f.write(f"{r}\n{s}")
        
        print(f"Подпись (r, s) = ({r}, {s})")
        print(f"Подпись сохранена в файл: {output_filename}")
        return (r, s)
    
    def verify_signature(self, filename, signature_filename):
        """Проверка подписи Эль-Гамаля"""
        if self.p == 0 or self.g == 0 or self.y == 0:
            raise ValueError("Сначала сгенерируйте или загрузите ключи!")
        
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        file_hash = hashlib.sha256(file_data).digest()
        h = int.from_bytes(file_hash, byteorder='big') % self.p
        
        with open(signature_filename, 'r') as f:
            signature_data = f.readlines()
        
        if len(signature_data) < 2:
            raise ValueError("Неверный формат файла подписи")
        
        r = int(signature_data[0].strip())
        s = int(signature_data[1].strip())
        
        print(f"Загруженная подпись (r, s) = ({r}, {s})")
        print(f"Вычисленный хеш: {h}")
        
        # Проверяем условия: 1 < r < p и 0 < s < p-1
        if r <= 1 or r >= self.p:
            print(f"Ошибка: r = {r} не удовлетворяет условию 1 < r < p")
            return False
        
        if s <= 0 or s >= self.p - 1:
            print(f"Ошибка: s = {s} не удовлетворяет условию 0 < s < p-1")
            return False
        
        # Проверяем подпись: g^h mod p = y^r * r^s mod p
        left_side = fast_pow(self.g, h, self.p)
        right_side = (fast_pow(self.y, r, self.p) * fast_pow(r, s, self.p)) % self.p
        
        print(f"Левая часть проверки (g^h mod p): {left_side}")
        print(f"Правая часть проверки (y^r * r^s mod p): {right_side}")
        
        is_valid = (left_side == right_side)
        
        if is_valid:
            print("✓ Подпись верна!")
        else:
            print("✗ Подпись неверна!")
        
        return is_valid
    
    def save_public_key(self):
        """Сохранение открытого ключа"""
        filename = 'o'
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.g}\n{self.y}")
        print(f"Открытый ключ сохранен в: {filename}")
    
    def load_public_key(self, filename):
        """Загрузка открытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.g = int(lines[1].strip())
        self.y = int(lines[2].strip())
        print(f"Открытый ключ загружен: p={self.p}, g={self.g}, y={self.y}")
    
    def save_private_key(self):
        """Сохранение закрытого ключа"""
        filename = 'c'
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.g}\n{self.x}\n{self.y}")
        print(f"Закрытый ключ сохранен в: {filename}")
    
    def load_private_key(self, filename):
        """Загрузка закрытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.g = int(lines[1].strip())
        self.x = int(lines[2].strip())
        self.y = int(lines[3].strip())
        print(f"Закрытый ключ загружен")

def main():
    elgamal = ElGamalSignature()
    
    while True:
        print("\n=== Система электронной подписи Эль-Гамаля ===")
        print("1. Сгенерировать новые ключи")
        print("2. Подписать файл")
        print("3. Проверить подпись")
        print("4. Сохранить ключи")
        print("5. Загрузить ключи")
        print("6. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            elgamal.generate_keys()
        
        elif choice == '2':
            filename = input("Введите имя файла для подписи: ")
            try:
                signature = elgamal.sign_file(filename)
                print("Файл успешно подписан!")
            except Exception as e:
                print(f"Ошибка при подписи: {e}")
        
        elif choice == '3':
            filename = input("Введите имя файла для проверки: ")
            signature_file = input("Введите имя файла с подписью: ")
            elgamal.verify_signature(filename, signature_file)
        
        elif choice == '4':
            print("1. Сохранить открытый ключ")
            print("2. Сохранить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                elgamal.save_public_key()
            elif key_choice == '2':
                elgamal.save_private_key()
        
        elif choice == '5':
            print("1. Загрузить открытый ключ")
            print("2. Загрузить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                filename = input("Введите имя файла: ")
                elgamal.load_public_key(filename)
            elif key_choice == '2':
                filename = input("Введите имя файла: ")
                elgamal.load_private_key(filename)
        
        elif choice == '6':
            break
        
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()