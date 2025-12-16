import random
import json
import os
from pathlib import Path

def extended_gcd(a, b):
    """Нахождение НОД"""
    U = [a, 1, 0]
    V = [b, 0, 1]

    while V[0] != 0:
        q = U[0] // V[0]
        T = [U[0] % V[0], U[1] - q * V[1], U[2] - q * V[2]]
        U = V
        V = T
    return U

def fast_pow(a, x, p):
    """Быстрое возведение в степень"""
    y = 1
    a = a % p
    
    while x > 0:
        if x & 1:
            y = (y * a) % p
        a = (a * a) % p
        x >>= 1
    
    return y

def ferm_test(n):
    """Проверка на простоту"""
    k = 50
    
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False
    
    for _ in range(k):
        a = random.randint(2, n - 2)
        if fast_pow(a, n - 1, n) != 1:
            return False
    
    return True

class FiatShamirServer:
    """Серверная часть протокола Фиата-Шамира"""
    
    def __init__(self):
        self.N = 0  # Модуль N = p*q
        self.p = 0  # Секретное простое p
        self.q = 0  # Секретное простое q
        self.users_file = "users.json"
        self.users = {}
        self.current_session = {}
        
    def generate_N(self, bits=512):
        """Генерация модуля N = p*q"""
        print("СЕРВЕР: Генерация модуля N...")
        
        # Генерируем p
        while True:
            self.p = random.getrandbits(bits // 2)
            self.p |= (1 << (bits // 2 - 1)) | 1  # Делаем нечетным и устанавливаем старший бит
            if ferm_test(self.p):
                break
        
        # Генерируем q
        while True:
            self.q = random.getrandbits(bits // 2)
            self.q |= (1 << (bits // 2 - 1)) | 1
            if ferm_test(self.q) and self.q != self.p:
                break
        
        self.N = self.p * self.q
        
        print(f"СЕРВЕР: p = {self.p}")
        print(f"СЕРВЕР: q = {self.q}")
        print(f"СЕРВЕР: N = p*q = {self.N}")
        print(f"СЕРВЕР: Битность N: {self.N.bit_length()} бит")
        
        return self.N
    
    def register_user(self, username, v):
        """Регистрация пользователя с открытым ключом v"""
        if username in self.users:
            print(f"СЕРВЕР: Пользователь {username} уже существует!")
            return False
        
        # Проверяем, что v в правильном диапазоне
        if v <= 1 or v >= self.N:
            print(f"СЕРВЕР: v должно быть в диапазоне (1, N-1)")
            return False
        
        self.users[username] = {
            'username': username,
            'v': v,  # Открытый ключ: v = s^2 mod N
            'login_attempts': 0
        }
        
        self.save_users()
        print(f"СЕРВЕР: Пользователь {username} зарегистрирован с v={v}")
        return True
    
    def save_users(self):
        """Сохранение пользователей в файл"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
        print(f"СЕРВЕР: Пользователи сохранены в {self.users_file}")
    
    def load_users(self):
        """Загрузка пользователей из файла"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
            print(f"СЕРВЕР: Загружено {len(self.users)} пользователей")
            return True
        return False
    
    def get_user(self, username):
        """Получение информации о пользователе"""
        return self.users.get(username)
    
    def start_authentication(self, username):
        """Начало аутентификации пользователя"""
        if username not in self.users:
            print(f"СЕРВЕР: Пользователь {username} не найден!")
            return None
        
        # Сбрасываем текущую сессию
        self.current_session = {
            'username': username,
            'v': self.users[username]['v'],
            'rounds': 0,
            'successful_rounds': 0,
            'total_rounds': 20,  # Количество раундов t
            'current_round': 0,
            'x_received': None,
            'e_sent': None,
            'y_received': None
        }
        
        print(f"СЕРВЕР: Начало аутентификации для {username}")
        print(f"СЕРВЕР: Открытый ключ v={self.current_session['v']}")
        print(f"СЕРВЕР: Будет проведено {self.current_session['total_rounds']} раундов")
        
        return {
            'N': self.N,
            'v': self.current_session['v'],
            'total_rounds': self.current_session['total_rounds']
        }
    
    def receive_x(self, x):
        """Получение доказательства x от клиента"""
        # Проверяем, что x в правильном диапазоне
        if x <= 0 or x >= self.N:
            print(f"СЕРВЕР: x должно быть в диапазоне (1, N-1)")
            return False
        
        self.current_session['x_received'] = x
        print(f"СЕРВЕР: Получено x = {x}")
        
        # Генерируем случайный бит e (0 или 1)
        e = random.randint(0, 1)
        self.current_session['e_sent'] = e
        print(f"СЕРВЕР: Сгенерирован вызов e = {e}")
        
        return e
    
    def receive_y(self, y):
        """Получение ответа y от клиента и проверка"""
        if y == 0:
            print("СЕРВЕР: y = 0! Доказательство отвергнуто.")
            return False
        
        self.current_session['y_received'] = y
        self.current_session['current_round'] += 1
        
        x = self.current_session['x_received']
        v = self.current_session['v']
        e = self.current_session['e_sent']
        
        # Проверяем: y^2 ≡ x * v^e mod N
        left_side = (y * y) % self.N
        right_side = (x * fast_pow(v, e, self.N)) % self.N
        
        print(f"СЕРВЕР: Проверка раунда {self.current_session['current_round']}:")
        print(f"  y^2 mod N = {left_side}")
        print(f"  x * v^{e} mod N = {right_side}")
        
        if left_side == right_side:
            self.current_session['successful_rounds'] += 1
            print(f"  ✓ Раунд {self.current_session['current_round']} пройден успешно!")
            print(f"  Успешных раундов: {self.current_session['successful_rounds']}/{self.current_session['total_rounds']}")
            return True
        else:
            print(f"  ✗ Раунд {self.current_session['current_round']} не пройден!")
            return False
    
    def is_authenticated(self):
        """Проверка успешности всех раундов"""
        if self.current_session['current_round'] < self.current_session['total_rounds']:
            return False
        
        success = self.current_session['successful_rounds'] == self.current_session['total_rounds']
        
        if success:
            print(f"\nСЕРВЕР: Аутентификация успешна!")
            print(f"СЕРВЕР: Все {self.current_session['total_rounds']} раундов пройдены")
            print(f"СЕРВЕР: Добро пожаловать, {self.current_session['username']}!")
        else:
            print(f"\nСЕРВЕР: Аутентификация не удалась!")
            print(f"СЕРВЕР: Только {self.current_session['successful_rounds']} из {self.current_session['total_rounds']} раундов пройдены")
        
        # Обновляем статистику пользователя
        if self.current_session['username'] in self.users:
            self.users[self.current_session['username']]['login_attempts'] += 1
            if success:
                print(f"СЕРВЕР: Успешных входов: {self.users[self.current_session['username']]['login_attempts']}")
        
        self.save_users()
        return success

class FiatShamirClient:
    """Клиентская часть протокола Фиата-Шамира"""
    
    def __init__(self):
        self.N = 0  # Модуль от сервера
        self.s = 0  # Секретный ключ (известен только клиенту)
        self.v = 0  # Открытый ключ (хранится на сервере)
        self.username = ""
        self.current_session = {}
        
    def generate_keys(self, N, username):
        """Генерация секретного и открытого ключей"""
        self.N = N
        self.username = username
        
        # Выбираем s, взаимно простое с N
        while True:
            self.s = random.randint(2, N - 2)
            if extended_gcd(self.s, N)[0] == 1:
                break
        
        # Вычисляем v = s^2 mod N
        self.v = (self.s * self.s) % N
        
        print(f"КЛИЕНТ: Сгенерированы ключи для {username}:")
        print(f"  Секретный ключ s = {self.s}")
        print(f"  Открытый ключ v = s^2 mod N = {self.v}")
        print(f"  Проверка: gcd(s, N) = {extended_gcd(self.s, N)[0]} (должно быть 1)")
        
        return self.v
    
    def load_keys(self, N, s, username):
        """Загрузка существующих ключей"""
        self.N = N
        self.s = s
        self.username = username
        self.v = (s * s) % N
        
        print(f"КЛИЕНТ: Загружены ключи для {username}:")
        print(f"  s = {s}")
        print(f"  v = {self.v}")
    
    def start_authentication(self, server_params):
        """Начало аутентификации с сервером"""
        self.N = server_params['N']
        self.v = server_params['v']
        total_rounds = server_params['total_rounds']
        
        self.current_session = {
            'total_rounds': total_rounds,
            'current_round': 0,
            'successful_rounds': 0,
            'r_values': [],
            'x_values': [],
            'e_values': [],
            'y_values': []
        }
        
        print(f"КЛИЕНТ: Начало аутентификации для {self.username}")
        print(f"КЛИЕНТ: N = {self.N}")
        print(f"КЛИЕНТ: v = {self.v}")
        print(f"КЛИЕНТ: Будет проведено {total_rounds} раундов")
        
    def generate_x(self):
        """Генерация доказательства x = r^2 mod N"""
        # Выбираем случайное r ∈ [1, N-1]
        r = random.randint(1, self.N - 1)
        
        # Вычисляем x = r^2 mod N
        x = (r * r) % self.N
        
        # Сохраняем для текущего раунда
        self.current_session['r_values'].append(r)
        self.current_session['x_values'].append(x)
        self.current_session['current_round'] += 1
        
        print(f"КЛИЕНТ: Раунд {self.current_session['current_round']}:")
        print(f"  Выбрано r = {r}")
        print(f"  Отправляем x = r^2 mod N = {x}")
        
        return x
    
    def compute_y(self, e):
        """Вычисление ответа y = r * s^e mod N"""
        current_round = self.current_session['current_round'] - 1
        r = self.current_session['r_values'][current_round]
        
        # Сохраняем вызов e
        self.current_session['e_values'].append(e)
        
        # Вычисляем y = r * s^e mod N
        if e == 0:
            y = r % self.N
        else:  # e == 1
            y = (r * self.s) % self.N
        
        self.current_session['y_values'].append(y)
        
        print(f"КЛИЕНТ: Получен вызов e = {e}")
        print(f"КЛИЕНТ: Вычисляем y = r * s^{e} mod N = {y}")
        
        return y
    
    def get_round_info(self, round_num):
        """Получение информации о раунде"""
        if round_num < 0 or round_num >= len(self.current_session['r_values']):
            return None
        
        return {
            'r': self.current_session['r_values'][round_num],
            'x': self.current_session['x_values'][round_num],
            'e': self.current_session['e_values'][round_num],
            'y': self.current_session['y_values'][round_num]
        }

def simulate_protocol():
    """Симуляция полного протокола Фиата-Шамира"""
    print("="*60)
    print("СИМУЛЯЦИЯ ПРОТОКОЛА ФИАТА-ШАМИРА")
    print("="*60)
    
    # Создаем сервер
    server = FiatShamirServer()
    server.load_users()
    
    # Генерируем модуль N
    N = server.generate_N(bits=256)  # Для демонстрации используем 256 бит
    
    # Создаем клиента
    client = FiatShamirClient()
    
    # Регистрация нового пользователя
    username = input("\nВведите имя пользователя для регистрации: ")
    
    # Клиент генерирует ключи
    v = client.generate_keys(N, username)
    
    # Сервер регистрирует пользователя
    if server.register_user(username, v):
        print(f"\n✓ Пользователь {username} успешно зарегистрирован!")
    else:
        print(f"\n❌ Ошибка регистрации пользователя {username}")
        return
    
    # Аутентификация
    print("\n" + "="*60)
    print("НАЧАЛО АУТЕНТИФИКАЦИИ")
    print("="*60)
    
    # Клиент начинает аутентификацию
    server_params = server.start_authentication(username)
    client.start_authentication(server_params)
    
    # Выполняем t раундов
    t = server_params['total_rounds']
    
    for round_num in range(t):
        print(f"\n--- Раунд {round_num + 1}/{t} ---")
        
        # Шаг 1: Клиент выбирает r и отправляет x = r^2 mod N
        x = client.generate_x()
        
        # Шаг 2: Сервер получает x и отправляет вызов e
        e = server.receive_x(x)
        
        # Шаг 3: Клиент вычисляет y = r * s^e mod N
        y = client.compute_y(e)
        
        # Шаг 4: Сервер проверяет y
        if not server.receive_y(y):
            print(f"❌ Раунд {round_num + 1} не пройден!")
            break
    
    # Проверяем успешность аутентификации
    if server.is_authenticated():
        print("\n" + "="*60)
        print("✅ АУТЕНТИФИКАЦИЯ ПРОЙДЕНА УСПЕШНО!")
        print("="*60)
        
        # Показываем детали последнего раунда
        if client.current_session['current_round'] > 0:
            last_round = client.get_round_info(client.current_session['current_round'] - 1)
            if last_round:
                print("\nДетали последнего раунда:")
                print(f"  r = {last_round['r']}")
                print(f"  x = r^2 mod N = {last_round['x']}")
                print(f"  e = {last_round['e']}")
                print(f"  y = r * s^{last_round['e']} mod N = {last_round['y']}")
                
                # Проверяем вручную
                y_sq = (last_round['y'] * last_round['y']) % N
                x_v_e = (last_round['x'] * fast_pow(v, last_round['e'], N)) % N
                print(f"  Проверка: y^2 = {y_sq}, x * v^e = {x_v_e}")
                print(f"  Совпадают: {y_sq == x_v_e}")
    else:
        print("\n" + "="*60)
        print("❌ АУТЕНТИФИКАЦИЯ НЕ УДАЛАСЬ!")
        print("="*60)

def interactive_mode():
    """Интерактивный режим работы"""
    server = FiatShamirServer()
    server.load_users()
    
    if not server.users:
        print("СЕРВЕР: Генерация нового модуля N...")
        server.generate_N(bits=256)
    
    print(f"\nСЕРВЕР: Модуль N = {server.N}")
    print(f"СЕРВЕР: Зарегистрированных пользователей: {len(server.users)}")
    
    while True:
        print("\n" + "="*60)
        print("МЕНЮ ПРОТОКОЛА ФИАТА-ШАМИРА")
        print("="*60)
        print("1. Зарегистрировать нового пользователя")
        print("2. Аутентифицировать существующего пользователя")
        print("3. Показать всех пользователей")
        print("4. Симуляция полного протокола")
        print("5. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == '1':
            # Регистрация нового пользователя
            username = input("Введите имя пользователя: ")
            
            if username in server.users:
                print(f"Пользователь {username} уже существует!")
                continue
            
            print(f"\nГенерация ключей для {username}...")
            
            # Создаем клиента
            client = FiatShamirClient()
            
            # Клиент генерирует ключи
            v = client.generate_keys(server.N, username)
            
            # Показываем ключи пользователю
            print(f"\nКлючи пользователя {username}:")
            print(f"  Секретный ключ s = {client.s} (НИКОМУ НЕ ПОКАЗЫВАЙТЕ!)")
            print(f"  Открытый ключ v = {v} (будет отправлен на сервер)")
            
            # Регистрируем на сервере
            if server.register_user(username, v):
                print(f"\n✓ Пользователь {username} успешно зарегистрирован!")
                print("ВАЖНО: Сохраните свой секретный ключ s для последующих входов!")
            
        elif choice == '2':
            # Аутентификация
            username = input("Введите имя пользователя: ")
            
            if username not in server.users:
                print(f"Пользователь {username} не найден!")
                continue
            
            print(f"\nАутентификация пользователя {username}...")
            
            # Запрашиваем секретный ключ
            try:
                s = int(input("Введите ваш секретный ключ s: "))
            except ValueError:
                print("❌ Неверный формат ключа!")
                continue
            
            # Создаем клиента с загруженным ключом
            client = FiatShamirClient()
            client.load_keys(server.N, s, username)
            
            # Проверяем, что v совпадает
            if client.v != server.users[username]['v']:
                print("❌ Неверный секретный ключ! v не совпадает.")
                continue
            
            # Начинаем аутентификацию
            server_params = server.start_authentication(username)
            client.start_authentication(server_params)
            
            t = server_params['total_rounds']
            all_rounds_successful = True
            
            # Выполняем раунды
            for round_num in range(t):
                print(f"\n--- Раунд {round_num + 1}/{t} ---")
                
                # Клиент отправляет x
                x = client.generate_x()
                
                # Сервер отправляет e
                e = server.receive_x(x)
                
                # Клиент вычисляет y
                y = client.compute_y(e)
                
                # Сервер проверяет
                if not server.receive_y(y):
                    all_rounds_successful = False
                    print(f"❌ Раунд {round_num + 1} не пройден!")
                    break
            
            # Проверяем результат
            if all_rounds_successful and server.is_authenticated():
                print(f"\n✅ Добро пожаловать, {username}!")
            else:
                print(f"\n❌ Аутентификация не удалась!")
            
        elif choice == '3':
            # Показать всех пользователей
            print(f"\nЗарегистрированные пользователи ({len(server.users)}):")
            for username, data in server.users.items():
                print(f"  {username}: v={data['v']}, входов: {data.get('login_attempts', 0)}")
        
        elif choice == '4':
            # Симуляция полного протокола
            simulate_protocol()
        
        elif choice == '5':
            print("Выход из программы")
            break
        
        else:
            print("❌ Неверный выбор!")

def main():
    print("="*60)
    print("ПРОТОКОЛ ДОКАЗАТЕЛЬСТВА С НУЛЕВЫМ ЗНАНИЕМ ФИАТА-ШАМИРА")
    print("="*60)
    print("Реализация клиент-серверной аутентификации")
    print("Стойкость основана на сложности извлечения квадратного корня по модулю N")
    
    interactive_mode()

if __name__ == "__main__":
    main()