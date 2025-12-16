import json
import os
import random
import time
from lab1 import extended_gcd, fast_pow, ferm_test

class FiatShamirVisualizer:
    """Визуализация протокола Фиата-Шамира в одной программе"""
    
    def __init__(self):
        self.N = 0
        self.p = 0
        self.q = 0
        self.users_file = "fs_users.json"
        self.keys_file = "fs_keys.json"
        self.users = {}
        self.keys = {}
        self.current_user = None
        self.current_session = None
        self.load_data()
        
    def load_data(self):
        """Загрузка данных из файлов"""
        # Загрузка пользователей
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = f.read()
                    if data:
                        self.users = json.loads(data)
                        print(f"Загружено {len(self.users)} пользователей")
            except:
                print("Ошибка загрузки пользователей, создан новый файл")
                self.users = {}
        
        # Загрузка ключей
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    data = f.read()
                    if data:
                        self.keys = json.loads(data)
                        print(f"Загружено {len(self.keys)} наборов ключей")
            except:
                print("Ошибка загрузки ключей, создан новый файл")
                self.keys = {}
    
    def save_data(self):
        """Сохранение данных в файлы"""
        # Сохранение пользователей
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
        
        # Сохранение ключей
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
    
    def generate_N(self, bits=256):
        """Генерация модуля N = p*q"""
        print("\n" + "="*60)
        print("ГЕНЕРАЦИЯ МОДУЛЯ N")
        print("="*60)
        
        # Генерируем p
        while True:
            self.p = random.getrandbits(bits // 2)
            self.p |= (1 << (bits // 2 - 1)) | 1
            if ferm_test(self.p):
                break
        
        # Генерируем q
        while True:
            self.q = random.getrandbits(bits // 2)
            self.q |= (1 << (bits // 2 - 1)) | 1
            if ferm_test(self.q) and self.q != self.p:
                break
        
        self.N = self.p * self.q
        
        print(f"p = {self.p}")
        print(f"q = {self.q}")
        print(f"N = p * q = {self.N}")
        print(f"Битность N: {self.N.bit_length()} бит")
        
        return self.N
    
    def register_user(self, username):
        """Регистрация нового пользователя"""
        print("\n" + "="*60)
        print(f"РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ: {username}")
        print("="*60)
        
        if username in self.users:
            print(f"✗ Пользователь {username} уже существует!")
            return False
        
        if self.N == 0:
            print("i  Сначала сгенерируйте модуль N!")
            return False
        
        # Шаг 1: Выбираем секретный ключ s (взаимно простое с N)
        print("\n1. ВЫБОР СЕКРЕТНОГО КЛЮЧА s")
        while True:
            s = random.randint(2, self.N - 2)
            if extended_gcd(s, self.N)[0] == 1:
                break
        
        print(f"   Выбрано s = {s}")
        print(f"   Проверка: gcd(s, N) = {extended_gcd(s, self.N)[0]} (должно быть 1)")
        
        # Шаг 2: Вычисляем открытый ключ v = s^2 mod N
        print("\n2. ВЫЧИСЛЕНИЕ ОТКРЫТОГО КЛЮЧА v")
        v = (s * s) % self.N
        print(f"   v = s^2 mod N")
        print(f"   v = {s}^2 mod {self.N} = {v}")
        
        # Сохраняем пользователя
        self.users[username] = {
            'username': username,
            'v': v,
            'registrations': 1
        }
        
        # Сохраняем ключи (в реальной системе s хранится только у пользователя!)
        self.keys[username] = {
            's': str(s),  # Сохраняем как строку
            'N': str(self.N),
            'v': str(v)
        }
        
        self.save_data()
        
        print("\n" + "="*60)
        print(f"✓ ПОЛЬЗОВАТЕЛЬ {username} ЗАРЕГИСТРИРОВАН")
        print("="*60)
        print(f"Секретный ключ s = {s} (СОХРАНИТЕ ЭТОТ КЛЮЧ!)")
        print(f"Открытый ключ v = {v} (отправлен на сервер)")
        
        return True
    
    def simulate_authentication(self, username):
        """Симуляция процесса аутентификации"""
        print("\n" + "="*60)
        print(f"АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЯ: {username}")
        print("="*60)
        
        if username not in self.users:
            print(f"✗ Пользователь {username} не найден!")
            return False
        
        if username not in self.keys:
            print(f"✗ Не найден секретный ключ для пользователя {username}!")
            return False
        
        # Загружаем данные пользователя
        user_data = self.users[username]
        key_data = self.keys[username]
        
        v = int(user_data['v'])
        s = int(key_data['s'])
        N = int(key_data['N'])
        
        print(f"Открытый ключ v = {v}")
        print(f"Модуль N = {N}")
        
        if self.N != 0 and N != self.N:
            print(f"i  Внимание: N из ключей ({N}) отличается от текущего ({self.N})")
            print(f"   Использую N из ключей: {N}")
        
        # Устанавливаем текущие параметры
        current_N = N
        current_v = v
        current_s = s
        
        print(f"\nПАРАМЕТРЫ АУТЕНТИФИКАЦИИ:")
        print(f"  Пользователь: {username}")
        print(f"  Секретный ключ s = {current_s}")
        print(f"  Открытый ключ v = {current_v}")
        print(f"  Модуль N = {current_N}")
        
        # Количество раундов
        t = 20
        print(f"  Количество раундов: {t}")
        print(f"  Вероятность обмана: 1/2^{t} = 1/{2**t}")
        
        successful_rounds = 0
        
        for round_num in range(1, t + 1):
            print(f"\n{'='*50}")
            print(f"РАУНД {round_num}/{t}")
            print(f"{'='*50}")
            
            # Шаг 1: Пользователь выбирает случайное r
            print(f"\n1. ПОЛЬЗОВАТЕЛЬ ВЫБИРАЕТ СЛУЧАЙНОЕ r")
            r = random.randint(1, current_N - 1)
            print(f"   Выбрано r = {r}")
            
            # Вычисляем x = r^2 mod N
            x = (r * r) % current_N
            print(f"   Вычисляем x = r^2 mod N")
            print(f"   x = {r}^2 mod {current_N} = {x}")
            
            # Шаг 2: Сервер выбирает случайный бит e
            print(f"\n2. СЕРВЕР ВЫБИРАЕТ СЛУЧАЙНЫЙ БИТ e")
            e = random.randint(0, 1)
            print(f"   Выбрано e = {e}")
            
            # Шаг 3: Пользователь вычисляет y = r * s^e mod N
            print(f"\n3. ПОЛЬЗОВАТЕЛЬ ВЫЧИСЛЯЕТ y = r * s^e mod N")
            if e == 0:
                y = r % current_N
                print(f"   При e = 0: y = r mod N = {y}")
            else:  # e == 1
                y = (r * current_s) % current_N
                print(f"   При e = 1: y = r * s mod N = {y}")
            
            # Шаг 4: Сервер проверяет y
            print(f"\n4. СЕРВЕР ПРОВЕРЯЕТ y")
            
            if y == 0:
                print(f"   ✗ y = 0! Доказательство отвергнуто.")
                break
            
            # Проверяем: y^2 ≡ x * v^e mod N
            print(f"   Проверяем: y^2 ≡ x * v^e mod N")
            
            # Вычисляем левую часть: y^2 mod N
            left_side = (y * y) % current_N
            print(f"   Левая часть: y^2 mod N = {y}^2 mod {current_N} = {left_side}")
            
            # Вычисляем правую часть: x * v^e mod N
            if e == 0:
                right_side = x % current_N
                print(f"   Правая часть: x * v^0 mod N = x mod N = {right_side}")
            else:
                v_pow_e = (current_v * 1) % current_N  # v^1 = v
                right_side = (x * v_pow_e) % current_N
                print(f"   Правая часть: x * v^1 mod N = {x} * {current_v} mod {current_N} = {right_side}")
            
            # Проверяем равенство
            if left_side == right_side:
                successful_rounds += 1
                print(f"\n   ✓ Раунд {round_num} пройден успешно!")
                print(f"   Успешных раундов: {successful_rounds}/{t}")
            else:
                print(f"\n   ✗ Раунд {round_num} не пройден!")
                print(f"   {left_side} ≠ {right_side}")
                break
            
            # Пауза для наглядности
            time.sleep(0.5)
        
        print(f"\n{'='*60}")
        if successful_rounds == t:
            print(f"✓ АУТЕНТИФИКАЦИЯ УСПЕШНА!")
            print(f"   Все {t} раундов пройдены успешно")
            
            # Обновляем статистику
            self.users[username]['successful_auths'] = self.users[username].get('successful_auths', 0) + 1
            self.save_data()
        else:
            print(f"✗ АУТЕНТИФИКАЦИЯ НЕ УДАЛАСЬ")
            print(f"   Пройдено только {successful_rounds} из {t} раундов")
        
        return successful_rounds == t
    
    def show_user_details(self, username):
        """Показать детали пользователя"""
        if username not in self.users:
            print(f"✗ Пользователь {username} не найден!")
            return False
        
        user_data = self.users[username]
        has_keys = username in self.keys
        
        print(f"\nДЕТАЛИ ПОЛЬЗОВАТЕЛЯ: {username}")
        print(f"{'='*40}")
        print(f"Открытый ключ v: {user_data.get('v', 'Нет')}")
        print(f"Регистраций: {user_data.get('registrations', 0)}")
        print(f"Успешных аутентификаций: {user_data.get('successful_auths', 0)}")
        
        if has_keys:
            key_data = self.keys[username]
            print(f"\nСЕКРЕТНЫЕ КЛЮЧИ (для демонстрации):")
            print(f"  s: {key_data.get('s', 'Нет')}")
            print(f"  N: {key_data.get('N', 'Нет')}")
        else:
            print(f"\ni  Секретные ключи не найдены")
        
        return True
    
    def show_all_users(self):
        """Показать всех пользователей"""
        print(f"\nВСЕ ПОЛЬЗОВАТЕЛИ ({len(self.users)}):")
        print(f"{'='*60}")
        
        if not self.users:
            print("Нет зарегистрированных пользователей")
            return
        
        for username, data in self.users.items():
            print(f"\n👤 {username}:")
            print(f"  Открытый ключ v: {data.get('v', 'Нет')}")
            print(f"  Успешных входов: {data.get('successful_auths', 0)}")
            if username in self.keys:
                print(f"  ✓ Секретный ключ сохранен")
            else:
                print(f"  i  Секретный ключ не найден")
    
    def interactive_mode(self):
        """Интерактивный режим работы"""
        print("="*60)
        print("ВИЗУАЛИЗАЦИЯ ПРОТОКОЛА ФИАТА-ШАМИРА")
        print("="*60)
        print("Доказательство с нулевым разглашением знания")
        
        while True:
            print("\n" + "="*60)
            print("ГЛАВНОЕ МЕНЮ:")
            print("1. Сгенерировать модуль N")
            print("2. Зарегистрировать нового пользователя")
            print("3. Симулировать аутентификацию")
            print("4. Показать всех пользователей")
            print("5. Показать детали пользователя")
            print("7. Тестовый сценарий")
            print("8. Выход")
            
            choice = input("\nВыберите действие: ").strip()
            
            if choice == '1':
                # Генерация модуля N
                bits = input("Введите битность N (рекомендуется 256-512): ").strip()
                try:
                    bits = int(bits) if bits else 256
                    if bits < 128:
                        print("i  Слишком маленькая битность! Использую 128 бит")
                        bits = 128
                    self.generate_N(bits=bits)
                except ValueError:
                    print("✗ Неверный ввод! Использую 256 бит")
                    self.generate_N(bits=256)
            
            elif choice == '2':
                # Регистрация пользователя
                if self.N == 0:
                    print("i  Сначала сгенерируйте модуль N!")
                    continue
                
                username = input("Введите имя пользователя: ").strip()
                if not username:
                    print("✗ Имя пользователя не может быть пустым")
                    continue
                
                self.register_user(username)
            
            elif choice == '3':
                # Аутентификация
                if not self.users:
                    print("✗ Нет зарегистрированных пользователей!")
                    continue
                
                print("\nДоступные пользователи:")
                for username in self.users.keys():
                    print(f"  • {username}")
                
                username = input("\nВведите имя пользователя для аутентификации: ").strip()
                if not username:
                    print("✗ Имя пользователя не может быть пустым")
                    continue
                
                self.simulate_authentication(username)
            
            elif choice == '4':
                # Показать всех пользователей
                self.show_all_users()
            
            elif choice == '5':
                # Показать детали пользователя
                if not self.users:
                    print("✗ Нет зарегистрированных пользователей!")
                    continue
                
                print("\nДоступные пользователи:")
                for username in self.users.keys():
                    print(f"  • {username}")
                
                username = input("\nВведите имя пользователя: ").strip()
                if username:
                    self.show_user_details(username)
            
            elif choice == '7':
                # Тестовый сценарий
                self.test_scenario()
            
            elif choice == '8':
                # Выход
                print("\nСохранение данных...")
                self.save_data()
                print("Выход из программы")
                break
            
            else:
                print("✗ Неверный выбор!")
    
    def test_scenario(self):
        """Запуск тестового сценария"""
        print("\n" + "="*60)
        print("ТЕСТОВЫЙ СЦЕНАРИЙ")
        print("="*60)
        
        # Шаг 1: Генерация N
        print("\n1. ГЕНЕРАЦИЯ МОДУЛЯ N...")
        if self.N == 0:
            self.generate_N(bits=128)  # Маленький для демонстрации
        else:
            print(f"   Использую существующий N = {self.N}")
        
        # Шаг 2: Регистрация тестового пользователя
        print("\n2. РЕГИСТРАЦИЯ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ...")
        test_user = "test_user_" + str(random.randint(1000, 9999))
        
        if test_user in self.users:
            print(f"   Тестовый пользователь {test_user} уже существует")
        else:
            self.register_user(test_user)
        
        # Шаг 3: Аутентификация
        print("\n3. АУТЕНТИФИКАЦИЯ...")
        success = self.simulate_authentication(test_user)
        
        # Шаг 4: Показать результат
        print("\n4. РЕЗУЛЬТАТ ТЕСТА:")
        if success:
            print(f"   ✓ Тест пройден успешно!")
            print(f"   Пользователь {test_user} успешно аутентифицирован")
        else:
            print(f"   ✗ Тест не пройден!")
            print(f"   Аутентификация пользователя {test_user} не удалась")
        
        # Шаг 5: Показать детали
        print("\n5. ДЕТАЛИ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ:")
        self.show_user_details(test_user)
        
        print("\n" + "="*60)
        print("ТЕСТОВЫЙ СЦЕНАРИЙ ЗАВЕРШЕН")
        print("="*60)

def main():
    """Основная функция"""
    try:
        visualizer = FiatShamirVisualizer()
        visualizer.interactive_mode()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")

if __name__ == "__main__":
    main()