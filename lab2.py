import random
import math
from lab1 import fast_pow, ferm_test

def shanks_method(a, y, p):
    k = m = int(p ** 0.5) + 1
    print(k, m)
    A = []
    for j in range(0, m):
        A.append(fast_pow(a, j, p) * y % p)
        # A.append(((a ** j) * y) % p)
    
    B = []
    for i in range(1, k + 1):
        B.append(fast_pow(a, i * m, p))
        # B.append((a ** (i * m)) % p)

    print("\nНумерация с 0")
    print(A)
    print("\nНумерация с 1")
    print(B)


    # Создаем словарь с помощью генератора словаря
    value_to_index = {value: index for index, value in enumerate(A)}

    # Ищем первое совпадение
    for i, value in enumerate(B):
        if value in value_to_index:
            print("\nj i:")
            print(value_to_index[value], i + 1)
            x = (i + 1) * m - value_to_index[value]
            return x
             
def main():
    print("Ввести числа вручную? (y/n): ")
    
    ans = input().strip().lower()
    
    if ans == 'y':
        while True:
            p = int(input("p (простое число) = "))
            if ferm_test(p):
                break
            print("p - не простое, введите p повторно")
        
        while True:
            a = int(input("a (основание, 1 < a < p) = "))
            if 1 < a < p:
                if math.gcd(a, p) == 1:
                    break
                print("a и p должны быть взаимно простыми")
            else:
                print("a должно быть в диапазоне (1, p)")
        
        while True:
            y = int(input("y (значение, 0 < y < p) = "))
            if 0 < y < p:
                break
            print("y должно быть в диапазоне (0, p)")
        
        print(f"\nРешаем: {y} ≡ {a}^x mod {p}")
        
        x = shanks_method(a, y, p)
        
        if x is not None:
            print(f"\nНайденное решение: x = {x}")
            verification = fast_pow(a, x, p)
            print(f"Проверка: {a}^{x} mod {p} = {verification}")
            if verification == y:
                print("Решение верное!")
            else:
                print("Решение неверное!")
        else:
            print("Решение не найдено. Возможно, y не принадлежит подгруппе, порожденной a.")
    
    elif ans == 'n':
        a = random.randint(2, 100000)
        while True:
            p = random.randint(1000001, 1000000000)
            if ferm_test(p):
                break
        
        x_true = random.randint(1, p - 2)
        y = fast_pow(a, x_true, p)
        
        print(f"y = {y}, a = {a}, p = {p}")
        
        x_calculated = shanks_method(a, y, p)
        print(f"\nВычисленный x = {x_calculated}")
        print(f"Истинный x = {x_true}")
        print(f"\n{y} = {a} ^ {x_calculated} mod {p}")
    
    else:
        print("Неверный ввод")

if __name__ == "__main__":
    main()