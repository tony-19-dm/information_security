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
    
    for _ in range(k):
        a = random.randint(2, n - 2)
        if fast_pow(a, n - 1, n) != 1:
            return False
    
    return True

def mod_inverse(a, m):
    """Нахождение обратного элемента по модулю"""
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError(f"Обратный элемент не существует для a={a}, m={m}")
    return x % m