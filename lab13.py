import hashlib
import random
from lab1 import ferm_test, extended_gcd, fast_pow

class BlindSignatureVoting:
    def __init__(self):
        # Серверные параметры (RSA)
        self.p = 0
        self.q = 0
        self.n = 0
        self.phi = 0
        self.d = 0  # закрытый ключ сервера (для подписи)
        self.c = 0  # открытый ключ сервера (для проверки)
        
        # Клиентские параметры
        self.client_n = 0  # бюллетень клиента
        self.client_r = 0  # ослепляющий множитель
        self.client_h = 0  # хеш бюллетеня
        self.client_blinded_h = 0  # ослепленный хеш
        self.client_s = 0  # подпись после снятия ослепления
        self.vote = ""  # голос клиента
        self.vote_options = {1: "Да", 2: "Нет", 3: "Воздержался"}

        self.steps = []
    
    def generate_server_keys(self):
        """Генерация ключей сервера (RSA)"""
        # Генерируем простые числа p и q
        while True:
            self.p = random.randint(2**511, 2**512)  # 512-битные простые
            if ferm_test(self.p):
                break
        
        while True:
            self.q = random.randint(2**511, 2**512)
            if ferm_test(self.q) and self.q != self.p:
                break
        
        # Вычисляем параметры
        self.n = self.p * self.q
        self.phi = (self.p - 1) * (self.q - 1)
        
        # Выбираем c (открытый ключ)
        while True:
            self.c = random.randint(2, self.phi - 1)
            if extended_gcd(self.c, self.phi)[0] == 1:
                break
        
        # Вычисляем d (закрытый ключ): c * d ≡ 1 mod φ
        gcd, x, _ = extended_gcd(self.c, self.phi)
        self.d = x % self.phi
        if self.d < 0:
            self.d += self.phi
        
        self.steps.append("=== СЕРВЕР: Ключи сгенерированы ===")
        self.steps.append(f"p = {self.p}")
        self.steps.append(f"q = {self.q}")
        self.steps.append(f"n = p * q = {self.n}")
        self.steps.append(f"φ(n) = (p-1)*(q-1) = {self.phi}")
        self.steps.append(f"Открытый ключ (c) = {self.c}")
        self.steps.append(f"Закрытый ключ (d) = {self.d}")
        self.steps.append(f"Проверка: c * d mod φ = {self.c * self.d % self.phi} (должно быть 1)")
        
        print("\n".join(self.steps[-7:]))
        return True
    
    def client_create_ballot(self, vote_choice, rnd_number=None):
        """Клиент создает бюллетень"""
        if vote_choice not in self.vote_options:
            print("✗ Неверный выбор голоса!")
            return False
        
        self.vote = self.vote_options[vote_choice]
        
        # Если не задан случайный номер, генерируем
        if rnd_number is None:
            rnd_number = random.randint(1, 2**20)
        
        # Формируем бюллетень: n = rnd || v || служебная информация
        # Используем формат: "RND:XXXXX|VOTE:Y|TIME:ZZZ"
        service_info = f"TIME:{random.randint(1000, 9999)}"
        ballot_str = f"RND:{rnd_number}|VOTE:{vote_choice}|{service_info}"
        
        # Преобразуем строку в число (n <= 1024 бит)
        self.client_n = int.from_bytes(ballot_str.encode(), byteorder='big')
        # Убедимся, что n < n (серверное)
        if self.client_n >= self.n:
            self.client_n = self.client_n % self.n
        
        self.steps.append("\n=== КЛИЕНТ: Создание бюллетеня ===")
        self.steps.append(f"Случайный номер: {rnd_number}")
        self.steps.append(f"Голос: {self.vote} ({vote_choice})")
        self.steps.append(f"Служебная информация: {service_info}")
        self.steps.append(f"Бюллетень (строка): {ballot_str}")
        self.steps.append(f"Бюллетень (число n): {self.client_n}")
        self.steps.append(f"Проверка: n < n_сервера? {self.client_n < self.n}")
        
        print("\n".join(self.steps[-7:]))
        return True
    
    def client_generate_blinding_factor(self):
        """Клиент генерирует ослепляющий множитель r"""
        # Генерируем r такой, что gcd(r, n) = 1
        while True:
            self.client_r = random.randint(2, self.n - 1)
            if extended_gcd(self.client_r, self.n)[0] == 1:
                break
        
        self.steps.append("\n=== КЛИЕНТ: Генерация ослепляющего множителя ===")
        self.steps.append(f"r = {self.client_r}")
        self.steps.append(f"Проверка: gcd(r, n) = {extended_gcd(self.client_r, self.n)[0]} (должно быть 1)")
        
        print("\n".join(self.steps[-3:]))
        return True
    
    def client_compute_hash(self):
        """Клиент вычисляет хеш бюллетеня"""
        # Вычисляем h = SHA3(n)
        ballot_bytes = str(self.client_n).encode()
        hash_obj = hashlib.sha3_256(ballot_bytes)
        hash_hex = hash_obj.hexdigest()
        
        # Преобразуем хеш в число
        self.client_h = int(hash_hex, 16) % self.n
        
        self.steps.append("\n=== КЛИЕНТ: Вычисление хеша бюллетеня ===")
        self.steps.append(f"n (для хеширования): {self.client_n}")
        self.steps.append(f"SHA3-256(n) (hex): {hash_hex}")
        self.steps.append(f"h = SHA3(n) mod n = {self.client_h}")
        self.steps.append(f"Проверка: h < n? {self.client_h < self.n}")
        
        print("\n".join(self.steps[-5:]))
        return True
    
    def client_blind_hash(self):
        """Клиент ослепляет хеш"""
        # Вычисляем _h = h * (r^c) mod n
        r_pow_c = fast_pow(self.client_r, self.c, self.n)
        self.client_blinded_h = (self.client_h * r_pow_c) % self.n
        
        self.steps.append("\n=== КЛИЕНТ: Ослепление хеша ===")
        self.steps.append(f"h = {self.client_h}")
        self.steps.append(f"r = {self.client_r}")
        self.steps.append(f"c (открытый ключ сервера) = {self.c}")
        self.steps.append(f"r^c mod n = {r_pow_c}")
        self.steps.append(f"_h = h * (r^c) mod n = {self.client_blinded_h}")
        
        print("\n".join(self.steps[-6:]))
        return True
    
    def server_blind_sign(self):
        """Сервер подписывает ослепленный хеш"""
        if self.client_blinded_h == 0:
            print("✗ Нет ослепленного хеша для подписи!")
            return 0
        
        # Сервер вычисляет _s = _h ^ d mod n
        server_blinded_signature = fast_pow(self.client_blinded_h, self.d, self.n)
        
        self.steps.append("\n=== СЕРВЕР: Подпись ослепленного хеша ===")
        self.steps.append(f"_h (от клиента) = {self.client_blinded_h}")
        self.steps.append(f"d (закрытый ключ сервера) = {self.d}")
        self.steps.append(f"_s = _h ^ d mod n = {server_blinded_signature}")
        
        print("\n".join(self.steps[-4:]))
        return server_blinded_signature
    
    def client_unblind_signature(self, server_blinded_signature):
        """Клиент снимает ослепление с подписи"""
        # Находим обратный элемент r_inv: r * r_inv ≡ 1 mod n
        gcd, r_inv, _ = extended_gcd(self.client_r, self.n)
        r_inv = r_inv % self.n
        if r_inv < 0:
            r_inv += self.n
        
        # Вычисляем s = _s * r_inv mod n
        self.client_s = (server_blinded_signature * r_inv) % self.n
        
        self.steps.append("\n=== КЛИЕНТ: Снятие ослепления ===")
        self.steps.append(f"_s (от сервера) = {server_blinded_signature}")
        self.steps.append(f"r = {self.client_r}")
        self.steps.append(f"r_inv mod n = {r_inv}")
        self.steps.append(f"Проверка: r * r_inv mod n = {self.client_r * r_inv % self.n} (должно быть 1)")
        self.steps.append(f"s = _s * r_inv mod n = {self.client_s}")
        self.steps.append(f"Ожидаемое: h^d mod n = {fast_pow(self.client_h, self.d, self.n)}")
        
        print("\n".join(self.steps[-7:]))
        return True
    
    def server_verify_signature(self):
        """Сервер проверяет подписанный бюллетень"""
        # Вычисляем хеш бюллетеня
        ballot_bytes = str(self.client_n).encode()
        hash_obj = hashlib.sha3_256(ballot_bytes)
        hash_hex = hash_obj.hexdigest()
        h = int(hash_hex, 16) % self.n
        
        # Проверяем: SHA3(n) = s^c mod n
        s_pow_c = fast_pow(self.client_s, self.c, self.n)
        
        self.steps.append("\n=== СЕРВЕР: Проверка подписи ===")
        self.steps.append(f"n (бюллетень) = {self.client_n}")
        self.steps.append(f"SHA3(n) = {h}")
        self.steps.append(f"s (подпись от клиента) = {self.client_s}")
        self.steps.append(f"c (открытый ключ) = {self.c}")
        self.steps.append(f"s^c mod n = {s_pow_c}")
        self.steps.append(f"Проверка: SHA3(n) == s^c mod n? {h == s_pow_c}")
        
        is_valid = (h == s_pow_c)
        
        if is_valid:
            self.steps.append("✓ Подпись верна! Бюллетень принят.")
        else:
            self.steps.append("✗ Подпись неверна! Бюллетень отклонен.")
        
        print("\n".join(self.steps[-7:]))
        return is_valid
    
    def run_full_voting_process(self, vote_choice):
        """Запуск полного процесса голосования"""
        self.steps = []
        
        print("\n" + "="*60)
        print("НАЧАЛО ПРОЦЕССА СЛЕПОЙ ПОДПИСИ ДЛЯ ГОЛОСОВАНИЯ")
        print("="*60)
        
        # Шаг 1: Сервер генерирует ключи
        self.generate_server_keys()
        
        # Шаг 2: Клиент создает бюллетень
        self.client_create_ballot(vote_choice)
        
        # Шаг 3: Клиент генерирует ослепляющий множитель
        self.client_generate_blinding_factor()
        
        # Шаг 4: Клиент вычисляет хеш
        self.client_compute_hash()
        
        # Шаг 5: Клиент ослепляет хеш
        self.client_blind_hash()
        
        # Шаг 6: Сервер подписывает ослепленный хеш
        blinded_signature = self.server_blind_sign()
        
        # Шаг 7: Клиент снимает ослепление
        self.client_unblind_signature(blinded_signature)
        
        # Шаг 8: Сервер проверяет подпись
        is_valid = self.server_verify_signature()
        
        print("\n" + "="*60)
        print("ИТОГ ПРОЦЕССА:")
        print(f"Голос: {self.vote}")
        print(f"Бюллетень: {self.client_n}")
        print(f"Подпись: {self.client_s}")
        print(f"Валидность: {'✓ ПРИНЯТО' if is_valid else '✗ ОТКЛОНЕНО'}")
        print("="*60)
        
        return is_valid
    
    def show_all_steps(self):
        """Показать все шаги процесса"""
        print("\n" + "="*60)
        print("ПОЛНАЯ ИСТОРИЯ ПРОЦЕССА:")
        print("="*60)
        for i, step in enumerate(self.steps, 1):
            print(f"{i:2}. {step}")
    
    def save_ballot_to_file(self, filename="ballot.txt"):
        """Сохранение бюллетеня в файл"""
        with open(filename, 'w') as f:
            f.write("=== БЮЛЛЕТЕНЬ ДЛЯ ГОЛОСОВАНИЯ ===\n")
            f.write(f"Голос: {self.vote}\n")
            f.write(f"Бюллетень (n): {self.client_n}\n")
            f.write(f"Подпись (s): {self.client_s}\n")
            f.write(f"Открытый ключ сервера (c): {self.c}\n")
            f.write(f"Модуль (n_сервера): {self.n}\n")
        
        print(f"Бюллетень сохранен в файл: {filename}")

def main():
    voting = BlindSignatureVoting()
    
    print("=== СИСТЕМА АНОНИМНОГО ГОЛОСОВАНИЯ СО СЛЕПОЙ ПОДПИСЬЮ ===")
    print("Протокол на основе RSA")
    
    while True:
        print("\n" + "="*60)
        print("МЕНЮ:")
        print("1. Запустить полный процесс голосования")
        print("2. Показать все шаги последнего процесса")
        print("3. Сохранить бюллетень в файл")
        print("4. Выполнить отдельные шаги")
        print("5. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            print("\nВарианты голосования:")
            for key, value in voting.vote_options.items():
                print(f"  {key}. {value}")
            
            try:
                vote_choice = int(input("Выберите вариант голосования (1-3): "))
                if vote_choice not in [1, 2, 3]:
                    print("✗ Неверный выбор!")
                    continue
                
                voting.run_full_voting_process(vote_choice)
                
            except ValueError:
                print("✗ Введите число!")
        
        elif choice == '2':
            if not voting.steps:
                print("✗ Сначала запустите процесс голосования!")
            else:
                voting.show_all_steps()
        
        elif choice == '3':
            if voting.client_n == 0:
                print("✗ Сначала создайте бюллетень!")
            else:
                voting.save_ballot_to_file()
        
        elif choice == '4':
            print("\nОТДЕЛЬНЫЕ ШАГИ:")
            print("1. Сервер: сгенерировать ключи")
            print("2. Клиент: создать бюллетень")
            print("3. Клиент: сгенерировать ослепляющий множитель")
            print("4. Клиент: вычислить хеш бюллетеня")
            print("5. Клиент: ослепить хеш")
            print("6. Сервер: подписать ослепленный хеш")
            print("7. Клиент: снять ослепление")
            print("8. Сервер: проверить подпись")
            
            step_choice = input("Выберите шаг: ")
            
            try:
                if step_choice == '1':
                    voting.generate_server_keys()
                elif step_choice == '2':
                    print("\nВарианты голосования:")
                    for key, value in voting.vote_options.items():
                        print(f"  {key}. {value}")
                    vote = int(input("Выберите вариант голосования: "))
                    voting.client_create_ballot(vote)
                elif step_choice == '3':
                    voting.client_generate_blinding_factor()
                elif step_choice == '4':
                    voting.client_compute_hash()
                elif step_choice == '5':
                    voting.client_blind_hash()
                elif step_choice == '6':
                    sig = voting.server_blind_sign()
                    print(f"Подпись сервера: {sig}")
                elif step_choice == '7':
                    if 'sig' not in locals():
                        sig = int(input("Введите подпись сервера: "))
                    voting.client_unblind_signature(sig)
                elif step_choice == '8':
                    voting.server_verify_signature()
                else:
                    print("✗ Неверный выбор!")
            except Exception as e:
                print(f"✗ Ошибка: {e}")
        
        elif choice == '5':
            print("Выход из программы")
            break
        
        else:
            print("✗ Неверный выбор!")

if __name__ == "__main__":
    main()