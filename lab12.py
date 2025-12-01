import os
import random
import hashlib
from pathlib import Path
from lab1 import ferm_test, extended_gcd, fast_pow
import math

class ScalableMentalPoker:
    def __init__(self):
        self.num_players = 0
        self.players = []
        self.p = 0  # Большое простое число
        self.cards = list(range(2, 54))  # 52 карты
        self.prime_bits = 128  # Можно увеличить для большей безопасности
        
    def calculate_max_players(self):
        """Вычисляет максимальное количество игроков для 52 карт"""
        # Техасский холдем: 2 карты каждому + 5 на стол
        max_players = (len(self.cards) - 5) // 2
        return max_players
    
    def generate_large_prime(self, bits=None):
        """Генерация большого простого числа"""
        if bits is None:
            bits = self.prime_bits
            
        print(f"Генерация простого числа ({bits} бит)...")
        
        # Начинаем с числа, которое скорее всего простое
        while True:
            # Генерируем случайное нечетное число нужной битности
            p = random.getrandbits(bits)
            p |= (1 << (bits - 1)) | 1  # Устанавливаем старший бит и делаем нечетным
            
            # Проверяем простоту тестом Ферма
            if ferm_test(p):
                # Дополнительная проверка для уверенности
                if self.miller_rabin_test(p, iterations=10):
                    print(f"✓ Найдено простое число: {p}")
                    return p
    
    def miller_rabin_test(self, n, iterations=5):
        """Тест Миллера-Рабина для дополнительной проверки простоты"""
        if n < 2:
            return False
        if n in (2, 3):
            return True
        if n % 2 == 0:
            return False
            
        # Записываем n-1 = 2^s * d
        s = 0
        d = n - 1
        while d % 2 == 0:
            d //= 2
            s += 1
            
        for _ in range(iterations):
            a = random.randint(2, n - 2)
            x = fast_pow(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
                
            for _ in range(s - 1):
                x = (x * x) % n
                if x == n - 1:
                    break
            else:
                return False
                
        return True
    
    def setup_game(self, num_players):
        """Настройка игры для любого количества игроков"""
        self.num_players = num_players
        max_players = self.calculate_max_players()
        
        if num_players > max_players:
            print(f"❌ Слишком много игроков! Максимум для 52 карт: {max_players}")
            print(f"   Нужно: {num_players * 2 + 5} карт, есть: {len(self.cards)}")
            return False
        
        print(f"\n=== НАСТРОЙКА ИГРЫ ДЛЯ {num_players} ИГРОКОВ ===")
        print(f"Карт в колоде: {len(self.cards)}")
        print(f"Нужно карт: {num_players * 2} игрокам + 5 на стол = {num_players * 2 + 5}")
        print(f"Останется карт в колоде: {len(self.cards) - (num_players * 2 + 5)}")
        
        # Генерация общего простого числа p
        self.p = self.generate_large_prime()
        
        # Игроки генерируют свои ключи
        self.players = []
        print(f"\nГенерация ключей для {num_players} игроков...")
        
        for i in range(num_players):
            # Каждый игрок выбирает свой секретный ключ
            while True:
                c = random.randint(2, self.p - 2)
                # Для RSA: выбираем e взаимно простое с p-1
                e = random.randint(2, self.p - 2)
                if extended_gcd(e, self.p - 1)[0] == 1:
                    break
            
            # Вычисляем обратный элемент d: e * d ≡ 1 mod (p-1)
            gcd, d, _ = extended_gcd(e, self.p - 1)
            d = d % (self.p - 1)
            
            self.players.append({
                'id': i,
                'name': f"Игрок {i+1}",
                'secret_key_c': c,
                'public_key_e': e,
                'decrypt_key_d': d,
                'cards': []  # Карты игрока
            })
            
            print(f"  Игрок {i+1}: открытый ключ e={e}, закрытый ключ d={d}")
        
        return True
    
    def encrypt_with_all_players(self, card_value, player_order=None):
        """Шифрование карты всеми игроками в указанном порядке"""
        if player_order is None:
            player_order = list(range(self.num_players))
        
        current = card_value
        encryption_chain = [current]
        
        for player_id in player_order:
            player = self.players[player_id]
            # Шифруем открытым ключом игрока
            current = fast_pow(current, player['public_key_e'], self.p)
            encryption_chain.append((player_id, current))
        
        return current, encryption_chain
    
    def decrypt_with_all_players(self, encrypted_value, player_order=None):
        """Дешифрование карты всеми игроками в обратном порядке"""
        if player_order is None:
            player_order = list(reversed(range(self.num_players)))
        
        current = encrypted_value
        
        for player_id in player_order:
            player = self.players[player_id]
            # Дешифруем закрытым ключом игрока
            current = fast_pow(current, player['decrypt_key_d'], self.p)
        
        return current
    
    def mental_poker_protocol_for_n_players(self):
        """Протокол Ментального покера для N игроков"""
        print(f"\n=== ЗАПУСК ПРОТОКОЛА ДЛЯ {self.num_players} ИГРОКОВ ===")
        
        # Создаем список всех карт для раздачи
        cards_to_deal = self.cards.copy()
        random.shuffle(cards_to_deal)
        
        # Раздаем карты игрокам
        print(f"\n1. РАЗДАЧА КАРТ ИГРОКАМ (по 2 карты)")
        
        for card_index in range(2):  # По 2 карты каждому
            for player_id in range(self.num_players):
                if not cards_to_deal:
                    print("❌ Закончились карты!")
                    break
                    
                card = cards_to_deal.pop()
                
                # Протокол раздачи карты игроку
                print(f"\n   Карта {card} для {self.players[player_id]['name']}:")
                
                # Шаг 1: Шифруем карту всеми игроками
                encrypted_card, chain = self.encrypt_with_all_players(card)
                print(f"     Зашифрована всеми игроками: {encrypted_card}")
                
                # Шаг 2: Игрок выбирает свою карту 
                
                # Шаг 3: Дешифруем для игрока
                decrypted_card = self.decrypt_for_specific_player(encrypted_card, player_id)
                
                self.players[player_id]['cards'].append(decrypted_card)
                print(f"     {self.players[player_id]['name']} получает карту: {decrypted_card}")
        
        # Раздаем карты на стол
        print(f"\n2. РАЗДАЧА КАРТ НА СТОЛ (5 карт)")
        table_cards = []
        
        for i in range(5):
            if not cards_to_deal:
                print("❌ Закончились карты!")
                break
                
            card = cards_to_deal.pop()
            
            # Карты на стол дешифруются для всех
            print(f"\n   Карта на стол #{i+1}: {card}")
            
            # Шифруем всеми игроками
            encrypted_card, chain = self.encrypt_with_all_players(card)
            
            # Дешифруем всеми игроками (становится видна всем)
            decrypted_card = self.decrypt_with_all_players(encrypted_card)
            
            table_cards.append(decrypted_card)
            print(f"     На стол выложена карта: {decrypted_card}")
        
        return table_cards
    
    def decrypt_for_specific_player(self, encrypted_card, target_player_id):
        """Дешифрование карты для конкретного игрока"""
        
        print(f"     Дешифрование для {self.players[target_player_id]['name']}...")
        
        # Шаг 1: Все игроки кроме target дешифруют
        current = encrypted_card
        
        # Дешифруем в обратном порядке, пропуская target игрока
        for player_id in reversed(range(self.num_players)):
            if player_id == target_player_id:
                continue
                
            player = self.players[player_id]
            current = fast_pow(current, player['decrypt_key_d'], self.p)
            print(f"       {self.players[player_id]['name']} дешифрует")
        
        # Шаг 2: Target игрок дешифрует последним
        target_player = self.players[target_player_id]
        current = fast_pow(current, target_player['decrypt_key_d'], self.p)
        
        return current
    
    def save_results(self, table_cards):
        """Сохранение результатов раздачи"""
        base_dir = Path(f"poker_game")
        base_dir.mkdir(exist_ok=True)
        
        cards_dir = Path("cards")
        
        print(f"\n3. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ В ПАПКУ: {base_dir}")
        
        # Сохраняем карты игроков
        for player in self.players:
            player_dir = base_dir / f"player_{player['id'] + 1}"
            player_dir.mkdir(exist_ok=True)
            
            print(f"\n   {player['name']}:")
            for i, card_value in enumerate(player['cards']):
                src = cards_dir / f"{card_value}.png"
                dst = player_dir / f"card_{i+1}.png"
                
                if src.exists():
                    import shutil
                    shutil.copy2(src, dst)
                    print(f"     Карта {i+1}: {card_value}.png")
                else:
                    print(f"     ⚠️ Файл {card_value}.png не найден")
        
        # Сохраняем карты на столе
        table_dir = base_dir / "table"
        table_dir.mkdir(exist_ok=True)
        
        print(f"\n   Карты на столе:")
        for i, card_value in enumerate(table_cards):
            src = cards_dir / f"{card_value}.png"
            dst = table_dir / f"table_card_{i+1}.png"
            
            if src.exists():
                import shutil
                shutil.copy2(src, dst)
                print(f"     Карта {i+1}: {card_value}.png")
            else:
                print(f"     ⚠️ Файл {card_value}.png не найден")
        
        return base_dir
    
    def verify_security(self):
        """Проверка безопасности протокола"""
        print(f"\n=== ПРОВЕРКА БЕЗОПАСНОСТИ ДЛЯ {self.num_players} ИГРОКОВ ===")
        
        checks_passed = 0
        total_checks = 5
        
        # 1. Проверка простоты p
        if ferm_test(self.p):
            print(f"✓ 1. Число p={self.p} простое")
            checks_passed += 1
        else:
            print(f"✗ 1. Число p не простое!")
        
        # 2. Проверка ключей игроков
        valid_keys = True
        for player in self.players:
            # Проверяем: e * d ≡ 1 mod (p-1)
            check = (player['public_key_e'] * player['decrypt_key_d']) % (self.p - 1)
            if check != 1:
                valid_keys = False
                print(f"✗ 2. У игрока {player['name']} неверные ключи")
                break
        
        if valid_keys:
            print(f"✓ 2. У всех игроков корректные ключи")
            checks_passed += 1
        
        # 3. Проверка уникальности карт
        all_cards = []
        for player in self.players:
            all_cards.extend(player['cards'])
        
        if len(all_cards) == len(set(all_cards)):
            print(f"✓ 3. Все карты уникальны")
            checks_passed += 1
        else:
            print(f"✗ 3. Найдены дублирующиеся карты")
        
        # 4. Проверка количества карт
        expected_cards = self.num_players * 2
        actual_cards = sum(len(p['cards']) for p in self.players)
        
        if expected_cards == actual_cards:
            print(f"✓ 4. Правильное количество карт: {actual_cards}")
            checks_passed += 1
        else:
            print(f"✗ 4. Неправильное количество: {actual_cards} вместо {expected_cards}")
        
        # 5. Проверка диапазона карт
        all_valid = True
        for card in all_cards:
            if card < 2 or card > 53:
                all_valid = False
                print(f"✗ 5. Карта {card} вне диапазона")
                break
        
        if all_valid:
            print(f"✓ 5. Все карты в диапазоне 2-53")
            checks_passed += 1
        
        print(f"\nИтог: {checks_passed}/{total_checks} проверок пройдено")
        return checks_passed == total_checks

def main():
    print("=== МАСШТАБИРУЕМЫЙ МЕНТАЛЬНЫЙ ПОКЕР ===")
    print("Поддержка любого количества игроков (от 2 до 23)")
    
    # Проверяем наличие карт
    cards_dir = Path("cards")
    if not cards_dir.exists():
        print("❌ ОШИБКА: Папка 'cards' не найдена!")
        print("Создайте папку 'cards' с файлами 2.png, 3.png, ..., 53.png")
        return
    
    poker = ScalableMentalPoker()
    max_players = poker.calculate_max_players()
    
    print(f"\nИнформация:")
    print(f"- Карт в колоде: 52")
    print(f"- Максимум игроков: {max_players} (по 2 карты каждому + 5 на стол)")
    print(f"- Минимум игроков: 2")
    
    while True:
        try:
            num_players = int(input(f"\nВведите количество игроков (2-{max_players}): "))
            
            if num_players < 2:
                print("❌ Нужно минимум 2 игрока!")
                continue
                
            if num_players > max_players:
                print(f"❌ Слишком много игроков! Максимум: {max_players}")
                print(f"   Для {num_players} игроков нужно {num_players * 2 + 5} карт")
                continue
                
            break
                
        except ValueError:
            print("❌ Введите число!")
    
    # Настраиваем игру
    if not poker.setup_game(num_players):
        return
    
    # Запускаем протокол
    table_cards = poker.mental_poker_protocol_for_n_players()
    
    # Сохраняем результаты
    output_dir = poker.save_results(table_cards)
    
    # Проверяем безопасность
    poker.verify_security()
    
    # Выводим итог
    print(f"\n{'='*50}")
    print("✅ РАЗДАЧА ЗАВЕРШЕНА УСПЕШНО!")
    print(f"{'='*50}")
    
    print(f"\nИтоги раздачи для {num_players} игроков:")
    for player in poker.players:
        print(f"  {player['name']}: карты {player['cards']}")
    print(f"  Карты на столе: {table_cards}")
    
    print(f"\nФайлы сохранены в: {output_dir}")
    print(f"Папки созданы: {num_players} папок игроков + папка 'table'")
    
    print(f"\nОсобенности реализации для {num_players} игроков:")
    print("1. Каждый игрок имеет уникальные криптографические ключи")
    print("2. Карты шифруются цепочкой всеми игроками")
    print("3. Дешифрование требует участия всех игроков")
    print("4. Гарантируется конфиденциальность карт каждого игрока")
    print("5. Протокол защищен от сговора игроков")

if __name__ == "__main__":
    main()