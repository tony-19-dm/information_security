# client.py
import json
import os
import socket
import random
import time
from common_functions import extended_gcd, fast_pow, ferm_test

class FiatShamirClient:
    """Клиентская часть протокола Фиата-Шамира"""
    
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.N = 0
        self.s = 0  # Секретный ключ
        self.v = 0  # Открытый ключ
        self.username = ""
        self.session_id = ""
        self.keys_file = "client_keys.json"
        self.loaded_keys = {}
        self.current_session = {}
        self.socket = None
        self.connected = False
        
    def connect(self):
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Таймаут 10 секунд
            self.socket.connect((self.host, self.port))
            print(f"КЛИЕНТ: Подключен к серверу {self.host}:{self.port}")
            self.connected = True
            
            # Получаем параметры сервера
            server_params = self.receive_json()
            if server_params and server_params.get('action') == 'server_params':
                self.N = server_params['N']
                print(f"КЛИЕНТ: Получен модуль N = {self.N}")
                return True
            else:
                print("КЛИЕНТ: Не получил параметры сервера")
                self.connected = False
                return False
            
        except socket.timeout:
            print(f"КЛИЕНТ: Таймаут подключения к серверу")
            self.connected = False
            return False
        except ConnectionRefusedError:
            print(f"КЛИЕНТ: Сервер недоступен")
            self.connected = False
            return False
        except Exception as e:
            print(f"КЛИЕНТ: Ошибка подключения: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Отключение от сервера"""
        if self.socket:
            try:
                self.send_json({'action': 'disconnect'})
            except:
                pass
            self.socket.close()
            self.connected = False
            print("КЛИЕНТ: Отключен от сервера")
    
    def send_json(self, data):
        """Отправка JSON данных на сервер"""
        try:
            message = json.dumps(data).encode('utf-8')
            self.socket.sendall(len(message).to_bytes(4, 'big'))
            self.socket.sendall(message)
            return True
        except Exception as e:
            print(f"КЛИЕНТ: Ошибка отправки данных: {e}")
            return False
    
    def receive_json(self, timeout=5):
        """Получение JSON данных от сервера с таймаутом"""
        try:
            self.socket.settimeout(timeout)
            
            # Получаем длину сообщения
            length_bytes = self.socket.recv(4)
            if not length_bytes:
                print("КЛИЕНТ: Сервер закрыл соединение")
                return None
            
            length = int.from_bytes(length_bytes, 'big')
            
            # Получаем данные
            data = b''
            while len(data) < length:
                chunk = self.socket.recv(min(4096, length - len(data)))
                if not chunk:
                    print("КЛИЕНТ: Неполные данные от сервера")
                    return None
                data += chunk
            
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            print(f"КЛИЕНТ: Таймаут получения данных от сервера")
            return None
        except Exception as e:
            print(f"КЛИЕНТ: Ошибка получения данных: {e}")
            return None
        finally:
            self.socket.settimeout(None)
    
    def generate_keys(self, username):
        """Генерация новых ключей для пользователя"""
        if self.N == 0:
            print("КЛИЕНТ: Сначала подключитесь к серверу!")
            return False
        
        self.username = username
        
        # Выбираем s, взаимно простое с N
        while True:
            self.s = random.randint(2, self.N - 2)
            if extended_gcd(self.s, self.N)[0] == 1:
                break
        
        # Вычисляем v = s^2 mod N
        self.v = (self.s * self.s) % self.N
        
        print(f"КЛИЕНТ: Сгенерированы ключи для {username}:")
        print(f"  Секретный ключ s = {self.s}")
        print(f"  Открытый ключ v = s^2 mod N = {self.v}")
        
        return True
    
    def load_keys(self):
        """Загрузка ключей из файла"""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    self.loaded_keys = json.load(f)
                print(f"КЛИЕНТ: Загружено {len(self.loaded_keys)} наборов ключей")
                return True
            except Exception as e:
                print(f"КЛИЕНТ: Ошибка загрузки ключей: {e}")
                self.loaded_keys = {}
        else:
            print("КЛИЕНТ: Файл ключей не найден")
        return False
    
    def save_keys(self):
        """Сохранение ключей в файл"""
        if self.username and self.s != 0:
            # Загружаем существующие ключи
            self.load_keys()
            
            # Обновляем ключи текущего пользователя
            self.loaded_keys[self.username] = {
                's': str(self.s),
                'N': str(self.N),
                'v': str(self.v)
            }
            
            try:
                with open(self.keys_file, 'w') as f:
                    json.dump(self.loaded_keys, f, indent=2)
                
                print(f"КЛИЕНТ: Ключи для {self.username} сохранены в {self.keys_file}")
                return True
            except Exception as e:
                print(f"КЛИЕНТ: Ошибка сохранения ключей: {e}")
                return False
        return False
    
    def get_user_keys(self, username):
        """Получение ключей пользователя из сохраненных"""
        if not self.load_keys():
            return False
            
        if username in self.loaded_keys:
            keys = self.loaded_keys[username]
            self.username = username
            self.s = int(keys['s'])  # Конвертируем обратно в int
            self.N = int(keys['N'])
            self.v = int(keys['v'])
            
            # Проверяем, что N совпадает с серверным
            if hasattr(self, 'server_N') and self.N != self.server_N:
                print(f"КЛИЕНТ: Внимание! N из сохраненных ключей отличается от серверного")
                print(f"  Сохраненный N: {self.N}")
                print(f"  Серверный N: {self.server_N}")
                print(f"  Обновляю N на серверный...")
                self.N = self.server_N
                
                # Пересчитываем v с новым N
                self.v = (self.s * self.s) % self.N
                
                # Сохраняем обновленные ключи
                self.save_keys()
            
            print(f"КЛИЕНТ: Загружены ключи для {username}")
            return True
        else:
            print(f"КЛИЕНТ: Ключи для пользователя {username} не найдены")
            return False
    
    def register(self, username):
        """Регистрация нового пользователя на сервере"""
        if not self.connected:
            print("КЛИЕНТ: Не подключен к серверу!")
            return False
        
        if not self.generate_keys(username):
            return False
        
        # Сохраняем ключи перед отправкой
        if not self.save_keys():
            print("КЛИЕНТ: Не удалось сохранить ключи!")
            return False
        
        # Отправляем запрос на регистрацию
        request = {
            'action': 'register',
            'username': username,
            'v': self.v
        }
        
        print(f"КЛИЕНТ: Отправляю запрос на регистрацию...")
        if not self.send_json(request):
            print("КЛИЕНТ: Не удалось отправить запрос")
            return False
        
        # Даем серверу время обработать запрос
        time.sleep(0.5)
        
        response = self.receive_json()
        
        if response:
            if response.get('success'):
                print(f"КЛИЕНТ: {response.get('message', 'Регистрация успешна')}")
                return True
            else:
                print(f"КЛИЕНТ: Ошибка регистрации: {response.get('message', 'Неизвестная ошибка')}")
                return False
        else:
            print("КЛИЕНТ: Не получил ответ от сервера")
            return False
    
    def authenticate(self, username):
        """Аутентификация пользователя"""
        if not self.connected:
            print("КЛИЕНТ: Не подключен к серверу!")
            return False
        
        # Загружаем ключи пользователя
        if not self.get_user_keys(username):
            print(f"КЛИЕНТ: Не удалось загрузить ключи для {username}")
            print("КЛИЕНТ: Сначала зарегистрируйтесь")
            return False
        
        # Начинаем аутентификацию
        request = {
            'action': 'start_auth',
            'username': username
        }
        
        print(f"КЛИЕНТ: Отправляю запрос на аутентификацию...")
        if not self.send_json(request):
            print("КЛИЕНТ: Не удалось отправить запрос")
            return False
        
        response = self.receive_json()
        
        if not response:
            print("КЛИЕНТ: Не получил ответ от сервера на start_auth")
            return False
            
        if not response.get('success'):
            print(f"КЛИЕНТ: Ошибка начала аутентификации: {response.get('message', 'Неизвестная ошибка')}")
            return False
        
        # Сохраняем server_N для проверки
        self.server_N = self.N
        
        # Создаем session_id
        self.session_id = response.get('session_id', '')
        if not self.session_id:
            print("КЛИЕНТ: Не получил session_id от сервера")
            return False
                
        # Получаем параметры аутентификации
        total_rounds = response.get('total_rounds', 20)
        v_from_server = response.get('v')
        
        if v_from_server and v_from_server != self.v:
            print(f"КЛИЕНТ: Внимание! v с сервера отличается от локального")
            print(f"  Локальный v: {self.v}")
            print(f"  Серверный v: {v_from_server}")
            print(f"  Использую серверный v")
            self.v = v_from_server
        
        print(f"КЛИЕНТ: Начинаем {total_rounds} раундов аутентификации")
        
        successful_rounds = 0
        
        for round_num in range(total_rounds):
            print(f"\n--- Раунд {round_num + 1}/{total_rounds} ---")
            
            # Шаг 1: Генерируем r и вычисляем x
            r = random.randint(1, self.N - 1)
            x = fast_pow(r, 2, self.N)
            
            print(f"  r = {r}")
            print(f"  x = r^2 mod N = {x}")
            
            # Отправляем x на сервер
            request = {
                'action': 'send_x',
                'session_id': self.session_id,
                'x': x
            }
            
            if not self.send_json(request):
                print(f"КЛИЕНТ: Не удалось отправить x")
                return False
            
            # Получаем вызов e от сервера
            response = self.receive_json()
            if not response:
                print(f"КЛИЕНТ: Не получил ответ с вызовом e")
                return False
                
            if response.get('action') != 'challenge':
                print(f"КЛИЕНТ: Неожиданный ответ от сервера: {response}")
                return False
            
            e = response.get('e')
            if e not in [0, 1]:
                print(f"КЛИЕНТ: Неверный вызов e: {e}")
                return False
            
            print(f"  Получен вызов e = {e}")
            
            # Вычисляем y = r * s^e mod N
            if e == 0:
                y = r % self.N
            else:
                y = (r * self.s) % self.N
            
            print(f"  y = r * s^{e} mod N = {y}")
            
            # Отправляем y на сервер
            request = {
                'action': 'send_y',
                'session_id': self.session_id,
                'y': y
            }
            
            if not self.send_json(request):
                print(f"КЛИЕНТ: Не удалось отправить y")
                return False
            
            # Получаем результат раунда
            response = self.receive_json()
            if not response:
                print(f"КЛИЕНТ: Не получил результат раунда")
                return False
            
            action = response.get('action')
            
            if action == 'round_result':
                if response.get('success'):
                    successful_rounds = response.get('successful_rounds', successful_rounds + 1)
                    print(f"  ✓ Раунд пройден (успешно: {successful_rounds}/{total_rounds})")
                else:
                    print(f"  ✗ Раунд не пройден")
                    break
                    
            elif action == 'auth_result':
                # Аутентификация завершена
                success = response.get('success', False)
                successful_rounds = response.get('successful_rounds', successful_rounds)
                
                if success:
                    print(f"\n✓ Аутентификация успешна!")
                    print(f"   Все {total_rounds} раундов пройдены")
                else:
                    print(f"\n✗ Аутентификация не удалась")
                    print(f"   Пройдено {successful_rounds} из {total_rounds} раундов")
                
                return success
                
            else:
                print(f"КЛИЕНТ: Неожиданный ответ: {response}")
                return False
            
            # Небольшая пауза между раундами
            time.sleep(0.1)
        
        print(f"\ni  Аутентификация прервана")
        print(f"   Пройдено {successful_rounds} из {total_rounds} раундов")
        return False
    
    def list_users(self):
        """Запрос списка пользователей с сервера"""
        if not self.connected:
            print("КЛИЕНТ: Не подключен к серверу!")
            return False
        
        request = {
            'action': 'list_users'
        }
        
        if not self.send_json(request):
            print("КЛИЕНТ: Не удалось отправить запрос")
            return False
        
        response = self.receive_json()
        
        if response and response.get('action') == 'users_list':
            users = response.get('users', [])
            print(f"\nЗарегистрированные пользователи ({len(users)}):")
            for user in users:
                print(f"  {user['username']}: v={user['v']}, входов: {user.get('logins', 0)}")
            return True
        else:
            print("КЛИЕНТ: Не получил список пользователей")
            return False

def interactive_client():
    """Интерактивный клиент"""
    client = FiatShamirClient()
    
    print("="*60)
    print("КЛИЕНТ ПРОТОКОЛА ФИАТА-ШАМИРА")
    print("="*60)
    
    while True:
        print("\n" + "="*60)
        print("МЕНЮ КЛИЕНТА:")
        print("1. Подключиться к серверу")
        print("2. Зарегистрировать нового пользователя")
        print("3. Аутентифицироваться")
        print("4. Показать список пользователей на сервере")
        print("5. Показать сохраненные ключи")
        print("6. Отключиться от сервера")
        print("7. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == '1':
            if client.connected:
                print("✓ Уже подключен к серверу")
            elif client.connect():
                print("✓ Успешно подключено к серверу")
            else:
                print("✗ Ошибка подключения")
                print("   Убедитесь, что сервер запущен на localhost:12345")
        
        elif choice == '2':
            if not client.connected:
                print("✗ Сначала подключитесь к серверу!")
                continue
            
            username = input("Введите имя пользователя: ").strip()
            if not username:
                print("✗ Имя пользователя не может быть пустым")
                continue
            
            if client.register(username):
                print("✓ Регистрация успешна!")
                print(f"ВАЖНО: Секретный ключ сохранен в {client.keys_file}")
            else:
                print("✗ Ошибка регистрации")
        
        elif choice == '3':
            if not client.connected:
                print("✗ Сначала подключитесь к серверу!")
                continue
            
            username = input("Введите имя пользователя: ").strip()
            if not username:
                print("✗ Имя пользователя не может быть пустым")
                continue
            
            print(f"\nНачинаем аутентификацию пользователя {username}...")
            if client.authenticate(username):
                print("✓ Доступ разрешен!")
            else:
                print("✗ Доступ запрещен!")
        
        elif choice == '4':
            if not client.connected:
                print("✗ Сначала подключитесь к сервера!")
                continue
            
            print("\nЗапрашиваю список пользователей...")
            if client.list_users():
                print("✓ Список пользователей получен")
            else:
                print("✗ Ошибка получения списка")
        
        elif choice == '5':
            if client.load_keys():
                print(f"\nСохраненные ключи ({len(client.loaded_keys)} пользователей):")
                for username, keys in client.loaded_keys.items():
                    print(f"\n  Пользователь: {username}")
                    print(f"    s = {keys.get('s', 'Нет')}")
                    print(f"    N = {keys.get('N', 'Нет')}")
                    print(f"    v = {keys.get('v', 'Нет')}")
            else:
                print("✗ Нет сохраненных ключей")
        
        elif choice == '6':
            if client.connected:
                client.disconnect()
                print("✓ Отключено от сервера")
            else:
                print("i  Не подключен к серверу")
        
        elif choice == '7':
            if client.connected:
                client.disconnect()
            print("Выход из программы")
            break
        
        else:
            print("✗ Неверный выбор!")

if __name__ == "__main__":
    try:
        interactive_client()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")