import random
from lab1 import fast_pow, ferm_test

def diffi(Xa, Xb, p, g):
    Ya = fast_pow(g, Xa, p)
    Yb = fast_pow(g, Xb, p)

    print(f"\nYa = {g} ^ {Xa} mod {p} = {Ya}")
    print(f"\nYb = {g} ^ {Xb} mod {p} = {Yb}")

    Zab = fast_pow(Yb, Xa, p)
    Zba = fast_pow(Ya, Xb, p)

    print(f"\nZab = {Yb} ^ {Xa} mod {p} = {Zab}")
    print(f"\nZba = {Ya} ^ {Xb} mod {p} = {Zba}")

    if Zab == Zba:
        print(f"\nКлючи совпадают: {Zab} = {Zba}")
    else:
        print("\nКлючи не совпадают")


def main():
    print("Ввести числа вручную? (y/n): ")
    
    ans = input().strip().lower()
    
    if ans == 'y':
        while True:
            q = int(input("q (простое число) = "))
            if ferm_test(q):
                # Проверяем условие p = 2 * q + 1 и простоту p
                p_candidate = 2 * q + 1
                if ferm_test(p_candidate):
                    p = p_candidate
                    print(f"p = 2*q + 1 = {p} (простое число)")
                    break
                else:
                    print(f"q - простое, но p = 2*q + 1 = {p_candidate} не является простым")
                    print("Введите другое q")
            else:
                print("q - не простое, введите q повторно")
        
        while True:
            g = int(input("g (1 < a < p - 1) = "))
            if 1 < g < p - 1:
                if fast_pow(g, q, p) != 1:
                    break
                print("не выполняется условие g^q mod p != 1")
            else:
                print("g должно быть в диапазоне (1, p - 1)")
        
        while True:
            Xa = int(input("(секретный ключ Алисы) Xa = "))
            if 1 <= Xa < p:
                break
            else:
                print("Xa должно быть в диапазоне [1, p)")

        while True:
            Xb = int(input("(секретный ключ Боба) Xb = "))
            if 1 <= Xb < p:
                break
            else:
                print("Xb должно быть в диапазоне [1, p)")
        
        diffi(Xa, Xb, p, g)
    
    elif ans == 'n':
        # Автоматическая генерация q и p = 2*q + 1 (оба простые)
        while True:
            q = random.randint(1000, 10000)
            if ferm_test(q):
                p_temp = 2 * q + 1
                if ferm_test(p_temp):
                    p = p_temp
                    break
        
        # Генерация g - первообразного корня по модулю p
        while True:
            g = random.randint(2, p - 2)
            if fast_pow(g, q, p) != 1:  # проверка условия g^q mod p != 1
                break
        
        # Генерация секретных ключей
        Xa = random.randint(1, p - 1)
        Xb = random.randint(1, p - 1)
        
        print(f"Сгенерированные параметры:")
        print(f"q = {q} (простое число)")
        print(f"p = 2*q + 1 = {p} (простое число)")
        print(f"g = {g} (первообразный корень)")
        print(f"Xa = {Xa} (секретный ключ Алисы)")
        print(f"Xb = {Xb} (секретный ключ Боба)")
        print()
        
        diffi(Xa, Xb, p, g)
    
    else:
        print("Неверный ввод")


if __name__ == "__main__":
    main()