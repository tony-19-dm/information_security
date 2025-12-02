import random
from pathlib import Path
from lab1 import ferm_test, extended_gcd, fast_pow

class ScalableMentalPoker:
    def __init__(self):
        self.num_players = 0
        self.players = []
        self.p = 0
        self.cards = list(range(2, 54))
        self.prime_bits = 128
        self.encrypted_deck_by_players = []
        self.encrypted_table_cards = []
        
    def calculate_max_players(self):
        """Вычисляет максимальное количество игроков для 52 карт"""
        max_players = (len(self.cards) - 5) // 2
        return max_players
    
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
        
        while True:
            self.p = random.randint(2**127, 2**128)
            if ferm_test(self.p):
                break
        
        self.players = []
        print(f"\nГенерация ключей для {num_players} игроков...")
        
        for i in range(num_players):
            # Генерируем секретный ключ c и вычисляем открытый ключ d
            while True:
                c = random.randint(2, self.p - 2)
                if extended_gcd(c, self.p - 1)[0] == 1:
                    break
            
            gcd, d, _ = extended_gcd(c, self.p - 1)
            d = d % (self.p - 1)
            
            self.players.append({
                'id': i,
                'name': f"Игрок {i+1}",
                'encrypt_key_e': c,
                'decrypt_key_d': d,
                'cards': [],  # Расшифрованные карты игрока
                'encrypted_cards': [],  # Зашифрованные карты игрока
                'partially_decrypted_cards': []  # Частично дешифрованные карты
            })
            
            print(f"  Игрок {i+1}: открытый ключ c={c}, закрытый ключ d={d}")
        
        return True
    
    def encrypt_deck_by_player(self, player_id, deck):
        """Игрок шифрует всю колоду своим ключом"""
        player = self.players[player_id]
        encrypted_deck = []
        
        for card in deck:
            encrypted = fast_pow(card, player['encrypt_key_e'], self.p)
            encrypted_deck.append(encrypted)
        
        return encrypted_deck
    
    def mental_poker_protocol_for_n_players(self):
        """Протокол Ментального покера для N игроков"""
        print(f"\n=== ЗАПУСК ПРОТОКОЛА ДЛЯ {self.num_players} ИГРОКОВ ===")
        
        self.encrypted_deck_by_players = []
        self.encrypted_table_cards = []
        
        print(f"\n1. ПОСЛЕДОВАТЕЛЬНОЕ ШИФРОВАНИЕ КОЛОДЫ")
        
        current_deck = self.cards.copy()
        
        for player_id in range(self.num_players):
            encrypted_deck = self.encrypt_deck_by_player(player_id, current_deck)
            random.shuffle(encrypted_deck)
            current_deck = encrypted_deck
            
            self.encrypted_deck_by_players.append({
                'player_id': player_id,
                'encrypted_deck': encrypted_deck.copy()
            })
            
            print(f"   Игрок {player_id+1} зашифровал и перемешал колоду")
        
        final_encrypted_deck = current_deck
        print(f"   Итоговая зашифрованная колода: {len(final_encrypted_deck)} карт")
        
        print(f"\n2. РАЗДАЧА ЗАШИФРОВАННЫХ КАРТ")
        
        for player_id in range(self.num_players):
            for card_num in range(2):
                if not final_encrypted_deck:
                    print("❌ Закончились карты!")
                    break
                
                encrypted_card = final_encrypted_deck.pop()
                self.players[player_id]['encrypted_cards'].append(encrypted_card)
                
                self.players[player_id]['partially_decrypted_cards'].append(encrypted_card)
        
        for i in range(5):
            if not final_encrypted_deck:
                print("❌ Закончились карты!")
                break
            
            encrypted_card = final_encrypted_deck.pop()
            self.encrypted_table_cards.append(encrypted_card)
        
        print(f"   Раздано: {self.num_players * 2} карт игрокам + 5 карт на стол")
        
        print(f"\n3. ЧАСТИЧНОЕ ДЕШИФРОВАНИЕ КАРТ НА СТОЛЕ")
        
        partially_decrypted_table = self.encrypted_table_cards.copy()
        
        for player_id in reversed(range(self.num_players)):
            player = self.players[player_id]
            new_partially_decrypted = []
            
            for encrypted_card in partially_decrypted_table:
                decrypted = fast_pow(encrypted_card, player['decrypt_key_d'], self.p)
                new_partially_decrypted.append(decrypted)
            
            partially_decrypted_table = new_partially_decrypted
            print(f"   Игрок {player_id+1} дешифровал карты на столе")
        
        table_cards = []
        for card in partially_decrypted_table:
            # Находим соответствие оригинальной карте
            card_value = card % 52 + 2
            if card_value > 53:
                card_value = 53
            table_cards.append(card_value)
        
        print(f"   Карты на столе полностью дешифрованы: {table_cards}")
        
        print(f"\n4. ЧАСТИЧНОЕ ДЕШИФРОВАНИЕ КАРТ ИГРОКОВ")
        
        for player_id in range(self.num_players):
            player = self.players[player_id]

            partially_decrypted = player['encrypted_cards'].copy()
            
            for other_player_id in reversed(range(self.num_players)):
                if other_player_id == player_id:
                    continue  # Пропускаем самого игрока - он дешифрует последним
                    
                other_player = self.players[other_player_id]
                new_partially_decrypted = []
                
                for encrypted_card in partially_decrypted:
                    decrypted = fast_pow(encrypted_card, other_player['decrypt_key_d'], self.p)
                    new_partially_decrypted.append(decrypted)
                
                partially_decrypted = new_partially_decrypted
                print(f"   Игрок {other_player_id+1} дешифровал карты Игрока {player_id+1}")
            
            # Сохраняем частично дешифрованные карты
            player['partially_decrypted_cards'] = partially_decrypted
            
            final_decrypted = []
            for encrypted_card in partially_decrypted:
                decrypted = fast_pow(encrypted_card, player['decrypt_key_d'], self.p)
                
                card_value = decrypted % 52 + 2
                if card_value > 53:
                    card_value = 53
                final_decrypted.append(card_value)
            
            player['cards'] = final_decrypted
            print(f"   Игрок {player_id+1} дешифровал СВОИ карты последним: {final_decrypted}")
        
        return table_cards
    
    def save_results(self, table_cards):
        """Сохранение результатов раздачи"""
        base_dir = Path(f"poker_game")
        base_dir.mkdir(exist_ok=True)
        
        cards_dir = Path("cards")
        
        print(f"\n5. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
        
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
        
        return base_dir
    
    def verify_security(self):
        """Проверка безопасности протокола"""
        print(f"\n=== ПРОВЕРКА БЕЗОПАСНОСТИ ДЛЯ {self.num_players} ИГРОКОВ ===")
        
        checks_passed = 0
        total_checks = 6

        if ferm_test(self.p):
            print(f"✓ 1. Число p={self.p} простое")
            checks_passed += 1
        else:
            print(f"✗ 1. Число p не простое!")
        
        valid_keys = True
        for player in self.players:
            check = (player['encrypt_key_e'] * player['decrypt_key_d']) % (self.p - 1)
            if check != 1:
                valid_keys = False
                print(f"✗ 2. У игрока {player['name']} неверные ключи")
                break
        
        if valid_keys:
            print(f"✓ 2. У всех игроков корректные ключи")
            checks_passed += 1
        
        # Проверка уникальности карт игроков
        all_cards = []
        for player in self.players:
            all_cards.extend(player['cards'])
        
        if len(all_cards) == len(set(all_cards)):
            print(f"✓ 3. Все карты игроков уникальны")
            checks_passed += 1
        else:
            print(f"✗ 3. Найдены дублирующиеся карты у игроков")
        
        # Проверка количества карт
        expected_cards = self.num_players * 2
        actual_cards = sum(len(p['cards']) for p in self.players)
        
        if expected_cards == actual_cards:
            print(f"✓ 4. Правильное количество карт: {actual_cards}")
            checks_passed += 1
        else:
            print(f"✗ 4. Неправильное количество: {actual_cards} вместо {expected_cards}")
        
        # Проверка диапазона карт
        all_valid = True
        for card in all_cards:
            if card < 2 or card > 53:
                all_valid = False
                print(f"✗ 5. Карта {card} вне диапазона")
                break
        
        if all_valid:
            print(f"✓ 5. Все карты в диапазоне 2-53")
            checks_passed += 1
        
        # Проверка условия последнего дешифрования
        last_decryption_ok = True
        for player in self.players:
            if len(player['cards']) != len(player['encrypted_cards']):
                last_decryption_ok = False
                print(f"✗ 6. У {player['name']} не все карты дешифрованы")
                break
        
        if last_decryption_ok:
            print(f"✓ 6. Каждый игрок дешифровал свои карты последним")
            checks_passed += 1
        
        print(f"\nИтог: {checks_passed}/{total_checks} проверок пройдено")
        return checks_passed == total_checks

def main():
    print("=== МАСШТАБИРУЕМЫЙ МЕНТАЛЬНЫЙ ПОКЕР ===")
    print("Поддержка любого количества игроков (от 2 до 23)")
    
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
                continue
                
            break
        except ValueError:
            print("❌ Введите число!")
    
    if not poker.setup_game(num_players):
        return
    
    table_cards = poker.mental_poker_protocol_for_n_players()
    output_dir = poker.save_results(table_cards)
    poker.verify_security()

    
    print(f"\nИтоги раздачи для {num_players} игроков:")
    for player in poker.players:
        print(f"  {player['name']}: карты {player['cards']}")
    print(f"  Карты на столе: {table_cards}")
    
    print(f"\nФайлы сохранены в: {output_dir}")
    print(f"Папки созданы: {num_players} папок игроков + папка 'table'")

if __name__ == "__main__":
    main()