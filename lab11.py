import hashlib
import random
from lab1 import ferm_test, extended_gcd, fast_pow

class DSASignature:
    def __init__(self):
        self.p = 0  # большое простое число (L бит)
        self.q = 0  # простой делитель p-1 (N бит)
        self.g = 0  # генератор подгруппы порядка q
        self.x = 0  # закрытый ключ
        self.y = 0  # открытый ключ
    
    def generate_keys(self):
        """Генерация ключей по FIPS 186 (DSA)"""
        # Сначала генерируем q (простое число)
        while True:
            self.q = random.randint(2**15, 2**16)
            if ferm_test(self.q):
                break
        
        # Генерируем p такое, что p-1 делится на q
        k = 1
        while True:
            self.p = k * self.q + 1
            if ferm_test(self.p):
                break
            k += 1
        
        # Находим генератор g
        h = 2
        while True:
            self.g = fast_pow(h, (self.p - 1) // self.q, self.p)
            if self.g > 1:
                break
            h += 1

        # Закрытый ключ (0 < x < q)
        self.x = random.randint(1, self.q - 1)
        
        # Открытый ключ y = g^x mod p
        self.y = fast_pow(self.g, self.x, self.p)
        
        print(f"Сгенерированы ключи DSA (FIPS 186):")
        print(f"p = {self.p}")
        print(f"q = {self.q}")
        print(f"g = {self.g}")
        print(f"Закрытый ключ (x) = {self.x}")
        print(f"Открытый ключ (y) = {self.y}")
        print(f"Проверка: g^q mod p = {fast_pow(self.g, self.q, self.p)} (должно быть 1)")
    
    def _mod_inverse(self, a, m):
        """Вычисление обратного элемента по модулю"""
        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            raise ValueError("Обратный элемент не существует")
        return x % m
    
    def sign_file(self, filename, output_filename=None):
        """Подпись файла по алгоритму DSA (FIPS 186) - побайтовая подпись хеша"""
        if self.p == 0 or self.q == 0 or self.g == 0 or self.x == 0:
            raise ValueError("Сначала сгенерируйте ключи!")
        
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        # Шаг 1: Вычисление хеш-функции (SHA-256 по FIPS 186)
        file_hash = hashlib.sha256(file_data).digest()
        
        print(f"Хеш файла (SHA-256): {file_hash.hex()}")
        
        r_list = []
        s_list = []
        
        # Подписываем каждый байт хеша отдельно
        for byte in file_hash:
            h = int(byte) % self.q  # Преобразуем байт в число и приводим к диапазону 0 < h < q
            
            while True:
                # Шаг 2: Генерация эфемерного ключа k (0 < k < q)
                k = random.randint(1, self.q - 1)
                
                # Шаг 3: Вычисление r = (g^k mod p) mod q
                r = fast_pow(self.g, k, self.p) % self.q
                
                # Если r = 0, повторяем с другим k
                if r == 0:
                    continue
                
                # Шаг 4: Вычисление s = (k^(-1) * (h + x*r)) mod q
                k_inv = self._mod_inverse(k, self.q)
                s = (k_inv * (h + self.x * r)) % self.q
                
                # Если s = 0, повторяем с другим k
                if s == 0:
                    continue
                
                r_list.append(r)
                s_list.append(s)
                break
        
        if output_filename is None:
            output_filename = filename + '.sig'
        
        # Сохраняем подпись
        with open(output_filename, 'w') as f:
            f.write(' '.join(str(r) for r in r_list) + '\n')
            f.write(' '.join(str(s) for s in s_list))
        
        print(f"Подпись сохранена в файл: {output_filename}")
        print(f"Размер подписи: {len(r_list)} пар (r, s)")
        return (r_list, s_list)
    
    def verify_signature(self, filename, signature_filename):
        """Проверка подписи DSA (FIPS 186) - побайтовая проверка"""
        if self.p == 0 or self.q == 0 or self.g == 0 or self.y == 0:
            raise ValueError("Сначала сгенерируйте или загрузите ключи!")
        
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        # Шаг 1: Вычисление хеш-функции
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
        
        print(f"Загружена подпись DSA для {len(r_list)} байт хеша")
        print(f"Вычисленный хеш (SHA-256): {file_hash.hex()}")
        
        # Проверяем подпись для каждого байта
        valid_count = 0
        total_bytes = len(file_hash)
        
        for i, (h_byte, r, s) in enumerate(zip(file_hash, r_list, s_list)):
            # Шаг 2: Проверка условий 0 < r < q и 0 < s < q
            if r <= 0 or r >= self.q:
                print(f"Ошибка: r[{i}] = {r} не удовлетворяет условию 0 < r < q")
                continue
            
            if s <= 0 or s >= self.q:
                print(f"Ошибка: s[{i}] = {s} не удовлетворяет условию 0 < s < q")
                continue
            
            h = int(h_byte) % self.q
            
            # Шаг 3: Вычисление w = s^(-1) mod q
            w = self._mod_inverse(s, self.q)
            
            # Шаг 4: Вычисление u1 = (h * w) mod q
            u1 = (h * w) % self.q
            
            # Шаг 5: Вычисление u2 = (r * w) mod q
            u2 = (r * w) % self.q
            
            # Шаг 6: Вычисление v = (g^u1 * y^u2 mod p) mod q
            v = (fast_pow(self.g, u1, self.p) * fast_pow(self.y, u2, self.p)) % self.p
            v = v % self.q
            
            # Шаг 7: Проверка v = r
            if v == r:
                valid_count += 1
            else:
                print(f"Ошибка проверки для байта {i}: h={h}, r={r}, s={s}, v={v}")
        
        is_valid = (valid_count == total_bytes)
        
        if is_valid:
            print(f"✓ Подпись DSA верна! Все {total_bytes} байт проверены успешно.")
        else:
            print(f"✗ Подпись DSA неверна! Верны {valid_count} из {total_bytes} байт.")
        
        return is_valid
    
    def save_public_key(self):
        """Сохранение открытого ключа"""
        filename = 'o'
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.q}\n{self.g}\n{self.y}")
        print(f"Открытый ключ DSA сохранен в: {filename}")
    
    def load_public_key(self, filename):
        """Загрузка открытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.q = int(lines[1].strip())
        self.g = int(lines[2].strip())
        self.y = int(lines[3].strip())
        print(f"Открытый ключ DSA загружен: p={self.p}, q={self.q}, g={self.g}, y={self.y}")
    
    def save_private_key(self):
        """Сохранение закрытого ключа"""
        filename = 'c'
        with open(filename, 'w') as f:
            f.write(f"{self.p}\n{self.q}\n{self.g}\n{self.x}\n{self.y}")
        print(f"Закрытый ключ DSA сохранен в: {filename}")
    
    def load_private_key(self, filename):
        """Загрузка закрытого ключа"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        self.p = int(lines[0].strip())
        self.q = int(lines[1].strip())
        self.g = int(lines[2].strip())
        self.x = int(lines[3].strip())
        self.y = int(lines[4].strip())
        print(f"Закрытый ключ DSA загружен")

def main():
    dsa = DSASignature()
    
    while True:
        print("\n=== Система электронной подписи DSA (FIPS 186) ===")
        print("1. Сгенерировать новые ключи")
        print("2. Подписать файл")
        print("3. Проверить подпись")
        print("4. Сохранить ключи")
        print("5. Загрузить ключи")
        print("6. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            dsa.generate_keys()
        
        elif choice == '2':
            filename = input("Введите имя файла для подписи: ")
            try:
                signature = dsa.sign_file(filename)
                print("Файл успешно подписан алгоритмом DSA!")
            except Exception as e:
                print(f"Ошибка при подписи: {e}")
        
        elif choice == '3':
            filename = input("Введите имя файла для проверки: ")
            signature_file = input("Введите имя файла с подписью: ")
            try:
                if dsa.verify_signature(filename, signature_file):
                    print("✓ Подпись DSA верна!")
                else:
                    print("✗ Подпись DSA неверна!")
            except Exception as e:
                print(f"Ошибка при проверке: {e}")
        
        elif choice == '4':
            print("1. Сохранить открытый ключ")
            print("2. Сохранить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                dsa.save_public_key()
            elif key_choice == '2':
                dsa.save_private_key()
        
        elif choice == '5':
            print("1. Загрузить открытый ключ")
            print("2. Загрузить закрытый ключ")
            key_choice = input("Выберите: ")
            if key_choice == '1':
                filename = input("Введите имя файла: ")
                dsa.load_public_key(filename)
            elif key_choice == '2':
                filename = input("Введите имя файла: ")
                dsa.load_private_key(filename)
        
        elif choice == '6':
            break
        
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()