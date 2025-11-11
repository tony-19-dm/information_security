import random

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
    
    # Проводим k тестов
    for _ in range(k):
        # Выбираем случайное a в диапазоне [2, n-2]
        a = random.randint(2, n - 2)
        # Проверяем условие Ферма: a^(n-1) ≡ 1 mod n
        if fast_pow(a, n - 1, n) != 1:
            return False  # Число составное
    
    return True

def main():
    print("Ввести числа вручную? (y/n): ")
    
    ans = input().strip().lower()
    
    if ans == 'y':
        a = int(input("a = "))

        while a < 1:
            print("a - должно быть положительным")
            a = int(input("a = "))
        
        p = int(input("p = "))
        while not ferm_test(p):
            print("p - не простое, введите p повторно")
            p = int(input("p = "))
        
        x = int(input("x = "))
        while x >= p - 1:
            print("не выполняется условие (1 <= x < p - 1), введите x повторно")
            x = int(input("x = "))
        
        y = fast_pow(a, x, p)
        print(f"\ny = {a} ^ {x} mod {p} = {y}")
    
    elif ans == 'n':
        a = random.randint(1, 100000)
        
        while True:
            p = random.randint(1000000000, 1000000000000000)
            if ferm_test(p):
                break
        
        x = random.randint(1, p - 2)
        
        print(f"a = {a}, x = {x}, p = {p}")
        
        y = fast_pow(a, x, p)
        print(f"y = {a} ^ {x} mod {p} = {y}")
    
    else:
        print("Неверный ввод")

if __name__ == "__main__":
    main()