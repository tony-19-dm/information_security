# server.py
import json
import os
import socket
import threading
import random
from common_functions import fast_pow

class FiatShamirServer:
    """Серверная часть протокола Фиата-Шамира"""
    
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.N = 0
        self.p = 0
        self.q = 0
        self.users_file = "server_users.json"
        self.users = {}
        self.clients = {}  # Текущие подключения
        self.sessions = {}  # Активные сессии аутентификации
        self.load_users()
        self.generate_N(bits=256)  # Генерируем N при запуске
        
    def generate_N(self, bits=512):
        """Генерация модуля N = p*q"""
        print("СЕРВЕР: Генерация модуля N...")
        
        import random
        from common_functions import ferm_test
        
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
        
        print(f"СЕРВЕР: p = {self.p}")
        print(f"СЕРВЕР: q = {self.q}")
        print(f"СЕРВЕР: N = p*q = {self.N}")
        print(f"СЕРВЕР: Битность N: {self.N.bit_length()} бит")
        
        return self.N
    
    def load_users(self):
        """Загрузка пользователей из файла"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = f.read()
                    if data:
                        self.users = json.loads(data)
                        print(f"СЕРВЕР: Загружено {len(self.users)} пользователей")
                    else:
                        self.users = {}
                        print("СЕРВЕР: Файл пользователей пуст")
            except json.JSONDecodeError:
                print("СЕРВЕР: Ошибка чтения JSON, создан новый файл")
                self.users = {}
            except Exception as e:
                print(f"СЕРВЕР: Ошибка загрузки пользователей: {e}")
                self.users = {}
        else:
            self.users = {}
            print("СЕРВЕР: Файл пользователей не найден, создан новый")
    
    def save_users(self):
        """Сохранение пользователей в файл"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            print(f"СЕРВЕР: Пользователи сохранены в {self.users_file}")
        except Exception as e:
            print(f"СЕРВЕР: Ошибка сохранения пользователей: {e}")
    
    def register_user(self, username, v):
        """Регистрация пользователя с открытым ключом v"""
        if username in self.users:
            print(f"СЕРВЕР: Пользователь {username} уже существует!")
            return False
        
        # Проверяем v
        try:
            v = int(v)
            if v <= 1 or v >= self.N:
                print(f"СЕРВЕР: v должно быть в диапазоне (1, N-1)")
                return False
        except:
            print(f"СЕРВЕР: Неверный формат v")
            return False
        
        self.users[username] = {
            'username': username,
            'v': v,
            'login_attempts': 0,
            'successful_logins': 0
        }
        
        self.save_users()
        print(f"СЕРВЕР: Пользователь {username} зарегистрирован с v={v}")
        return True
    
    def create_session(self, username, client_address):
        """Создание новой сессии аутентификации"""
        if username not in self.users:
            return None
        
        # Генерируем уникальный ID сессии
        session_id = f"{client_address[0]}:{client_address[1]}:{username}:{random.randint(1000, 9999)}"
        
        self.sessions[session_id] = {
            'username': username,
            'v': self.users[username]['v'],
            'current_round': 0,
            'successful_rounds': 0,
            'total_rounds': 20,
            'x_received': None,
            'e_sent': None,
            'client_address': client_address,
            'created_at': time.time()
        }
        
        print(f"СЕРВЕР: Создана сессия {session_id} для {username}")
        return session_id
    
    def get_session(self, session_id):
        """Получение сессии по ID"""
        return self.sessions.get(session_id)
    
    def cleanup_old_sessions(self):
        """Очистка старых сессий"""
        current_time = time.time()
        old_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['created_at'] > 300:
                old_sessions.append(session_id)
        
        for session_id in old_sessions:
            del self.sessions[session_id]
            print(f"СЕРВЕР: Удалена устаревшая сессия {session_id}")
    
    def handle_client(self, client_socket, client_address):
        """Обработка подключения клиента"""
        print(f"СЕРВЕР: Подключился клиент {client_address}")
        
        try:
            # Отправляем клиенту параметры сервера
            server_params = {
                'action': 'server_params',
                'N': self.N,
                'total_rounds': 20
            }
            self.send_json(client_socket, server_params)
            
            while True:
                # Получаем сообщение от клиента
                data = self.receive_json(client_socket)
                if not data:
                    print(f"СЕРВЕР: Клиент {client_address} отключился")
                    break
                
                action = data.get('action')
                print(f"СЕРВЕР: Получено действие '{action}' от {client_address}")
                
                if action == 'register':
                    # Регистрация нового пользователя
                    username = data.get('username', '')
                    v = data.get('v', 0)
                    
                    if not username:
                        response = {'action': 'register_response', 'success': False, 'message': 'Не указано имя пользователя'}
                    else:
                        if self.register_user(username, v):
                            response = {'action': 'register_response', 'success': True, 'message': f'Пользователь {username} зарегистрирован'}
                        else:
                            response = {'action': 'register_response', 'success': False, 'message': f'Ошибка регистрации пользователя {username}'}
                    
                    self.send_json(client_socket, response)
                
                elif action == 'start_auth':
                    # Начало аутентификации
                    username = data.get('username', '')
                    
                    if not username:
                        response = {'action': 'auth_response', 'success': False, 'message': 'Не указано имя пользователя'}
                        self.send_json(client_socket, response)
                        continue
                    
                    if username not in self.users:
                        response = {'action': 'auth_response', 'success': False, 'message': f'Пользователь {username} не найден'}
                        self.send_json(client_socket, response)
                        continue
                    
                    # Создаем сессию
                    session_id = self.create_session(username, client_address)
                    if not session_id:
                        response = {'action': 'auth_response', 'success': False, 'message': 'Ошибка создания сессии'}
                        self.send_json(client_socket, response)
                        continue
                    
                    response = {
                        'action': 'auth_started',
                        'success': True,
                        'session_id': session_id,
                        'v': self.users[username]['v'],
                        'total_rounds': 20
                    }
                    self.send_json(client_socket, response)
                
                elif action == 'send_x':
                    # Получение x от клиента
                    session_id = data.get('session_id', '')
                    x = data.get('x', 0)
                    
                    session = self.get_session(session_id)
                    if not session:
                        response = {'action': 'error', 'message': 'Сессия не найдена или устарела'}
                        self.send_json(client_socket, response)
                        continue
                    
                    try:
                        x = int(x)
                        if x <= 0 or x >= self.N:
                            response = {'action': 'error', 'message': 'x должно быть в диапазоне (1, N-1)'}
                            self.send_json(client_socket, response)
                            continue
                    except:
                        response = {'action': 'error', 'message': 'Неверный формат x'}
                        self.send_json(client_socket, response)
                        continue
                    
                    # Сохраняем x
                    session['x_received'] = x
                    
                    # Генерируем случайный бит e
                    e = random.randint(0, 1)
                    session['e_sent'] = e
                    
                    response = {
                        'action': 'challenge',
                        'e': e,
                        'round': session['current_round'] + 1,
                        'session_id': session_id
                    }
                    self.send_json(client_socket, response)
                
                elif action == 'send_y':
                    # Получение y от клиента
                    session_id = data.get('session_id', '')
                    y = data.get('y', 0)
                    
                    session = self.get_session(session_id)
                    if not session:
                        response = {'action': 'error', 'message': 'Сессия не найдена или устарела'}
                        self.send_json(client_socket, response)
                        continue
                    
                    try:
                        y = int(y)
                        if y == 0:
                            response = {
                                'action': 'auth_result',
                                'success': False,
                                'message': 'y = 0, доказательство отвергнуто',
                                'current_round': session['current_round'],
                                'successful_rounds': session['successful_rounds']
                            }
                            self.send_json(client_socket, response)
                            # Удаляем сессию
                            if session_id in self.sessions:
                                del self.sessions[session_id]
                            continue
                    except:
                        response = {'action': 'error', 'message': 'Неверный формат y'}
                        self.send_json(client_socket, response)
                        continue
                    
                    # Проверяем: y^2 ≡ x * v^e mod N
                    x = session['x_received']
                    v = session['v']
                    e = session['e_sent']
                    
                    left_side = (y * y) % self.N
                    right_side = (x * fast_pow(v, e, self.N)) % self.N
                    
                    session['current_round'] += 1
                    
                    if left_side == right_side:
                        session['successful_rounds'] += 1
                        
                        if session['current_round'] < session['total_rounds']:
                            # Продолжаем раунды
                            response = {
                                'action': 'round_result',
                                'success': True,
                                'message': f'Раунд {session["current_round"]} пройден',
                                'current_round': session['current_round'],
                                'successful_rounds': session['successful_rounds'],
                                'session_id': session_id
                            }
                        else:
                            # Все раунды завершены
                            success = session['successful_rounds'] == session['total_rounds']
                            
                            if success:
                                # Обновляем статистику пользователя
                                self.users[session['username']]['successful_logins'] = self.users[session['username']].get('successful_logins', 0) + 1
                                self.save_users()
                                print(f"СЕРВЕР: Успешная аутентификация пользователя {session['username']}")
                            
                            response = {
                                'action': 'auth_result',
                                'success': success,
                                'message': 'Аутентификация завершена',
                                'current_round': session['current_round'],
                                'successful_rounds': session['successful_rounds'],
                                'total_rounds': session['total_rounds']
                            }
                            
                            # Удаляем завершенную сессию
                            if session_id in self.sessions:
                                del self.sessions[session_id]
                    else:
                        response = {
                            'action': 'auth_result',
                            'success': False,
                            'message': f'Раунд {session["current_round"]} не пройден',
                            'current_round': session['current_round'],
                            'successful_rounds': session['successful_rounds']
                        }
                        
                        # Удаляем сессию при неудаче
                        if session_id in self.sessions:
                            del self.sessions[session_id]
                    
                    self.send_json(client_socket, response)
                
                elif action == 'list_users':
                    # Запрос списка пользователей
                    users_list = []
                    for username, data in self.users.items():
                        users_list.append({
                            'username': username,
                            'v': data['v'],
                            'logins': data.get('successful_logins', 0)
                        })
                    
                    response = {
                        'action': 'users_list',
                        'users': users_list
                    }
                    self.send_json(client_socket, response)
                
                elif action == 'disconnect':
                    print(f"СЕРВЕР: Клиент {client_address} отключился")
                    break
                
                else:
                    print(f"СЕРВЕР: Неизвестное действие '{action}' от {client_address}")
                    response = {'action': 'error', 'message': f'Неизвестное действие: {action}'}
                    self.send_json(client_socket, response)
        
        except json.JSONDecodeError as e:
            print(f"СЕРВЕР: Ошибка JSON от клиента {client_address}: {e}")
        except Exception as e:
            print(f"СЕРВЕР: Ошибка с клиентом {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"СЕРВЕР: Соединение с {client_address} закрыто")
            
            # Очищаем сессии этого клиента
            self.cleanup_client_sessions(client_address)
    
    def cleanup_client_sessions(self, client_address):
        """Очистка сессий для указанного клиента"""
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session['client_address'] == client_address:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            print(f"СЕРВЕР: Удалена сессия {session_id} для отключенного клиента")
    
    def send_json(self, sock, data):
        """Отправка JSON данных через сокет"""
        try:
            message = json.dumps(data).encode('utf-8')
            sock.sendall(len(message).to_bytes(4, 'big'))
            sock.sendall(message)
            return True
        except Exception as e:
            print(f"СЕРВЕР: Ошибка отправки данных: {e}")
            return False
    
    def receive_json(self, sock):
        """Получение JSON данных через сокет"""
        try:
            # Получаем длину сообщения
            length_bytes = sock.recv(4)
            if not length_bytes:
                return None
            
            length = int.from_bytes(length_bytes, 'big')
            if length > 1000000:  # Защита от больших сообщений
                print(f"СЕРВЕР: Слишком большое сообщение: {length} байт")
                return None
            
            # Получаем данные
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    return None
                data += chunk
            
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            return None
        except ConnectionResetError:
            return None
        except Exception as e:
            print(f"СЕРВЕР: Ошибка получения данных: {e}")
            return None
    
    def start(self):
        """Запуск сервера"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(1)  # Таймаут для accept
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"СЕРВЕР: Запущен на {self.host}:{self.port}")
            print(f"СЕРВЕР: N = {self.N}")
            print(f"СЕРВЕР: Ожидание подключений...")
            
            import time
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    client_socket.settimeout(30)  # Таймаут для операций клиента
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    # Очищаем старые сессии
                    self.cleanup_old_sessions()
                    
                except socket.timeout:
                    # Таймаут accept, продолжаем цикл
                    continue
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"СЕРВЕР: Ошибка accept: {e}")
                
        except KeyboardInterrupt:
            print("\nСЕРВЕР: Остановка сервера...")
        except Exception as e:
            print(f"СЕРВЕР: Ошибка: {e}")
        finally:
            server_socket.close()
            print("СЕРВЕР: Сервер остановлен")

import time  # Добавляем импорт времени

if __name__ == "__main__":
    server = FiatShamirServer()
    server.start()