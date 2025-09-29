import random
import math
from lab1 import fast_pow, ferm_test, extended_gcd

def Shamir(p, m, Ca, Da, Cb, Db):
    print(f"Исходное сообщение: m = {m}")
    
    x1 = fast_pow(m, Ca, p)
    print(f"Шаг 1: x1 = {m}^{Ca} mod {p} = {x1}")
    
    x2 = fast_pow(x1, Cb, p)
    print(f"Шаг 2: x2 = {x1}^{Cb} mod {p} = {x2}")
    
    x3 = fast_pow(x2, Da, p)
    print(f"Шаг 3: x3 = {x2}^{Da} mod {p} = {x3}")
    
    x4 = fast_pow(x3, Db, p)
    print(f"Шаг 4: x4 = {x3}^{Db} mod {p} = {x4}")
    
    if x4 == m:
        print(f"Сообщение корректно расшифровано: {x4}")
    else:
        print(f"Ошибка! Получено: {x4}, ожидалось: {m}")
    
    return x4


def main():
    print("Ввести числа вручную? (y/n): ")
    
    ans = input().strip().lower()
    
    if ans == 'y':
        while True:
            p = int(input("p (простое число) = "))
            if ferm_test(p):
                break
            else:
                print("p - не простое, введите повторно")

        while True:
            m = int(input("m = "))
            if m < p:
                break
            else:
                print("m должно быть меньше p")
        
        while True:
            Ca = int(input("Ca = "))
            res = extended_gcd(Ca, p - 1)
            if res[0] == 1:
                break
            else:
                print("Ca должно быть взаимно простым с p - 1")

        while True:
            Da = int(input("Da = "))
            if Ca * Da % (p - 1) == 1:
                break
            else:
                print("Da должно быть взаимно обратным с Ca")

        while True:
            Cb = int(input("Cb = "))
            res = extended_gcd(Cb, p - 1)
            if res[0] == 1:
                break
            else:
                print("Cb должно быть взаимно простым с p - 1")

        while True:
            Db = int(input("Db = "))
            if Cb * Db % (p - 1) == 1:
                break
            else:
                print("Db должно быть взаимно обратным с Cb")

        Shamir(p, m, Ca, Da, Cb, Db)
        
    elif ans == 'n':
        while True:
            p = random.randint(1000000, 100000000)
            if ferm_test(p):
                break
        print(f"p = {p}")
        
        m = random.randint(1, p-1)
        print(f"m = {m}")
        
        while True:
            Ca = random.randint(2, p-2)
            res = extended_gcd(Ca, p - 1)
            if res[0] == 1:
                break
        
        Da = res[1]
        if Da < 0:
            Da += (p - 1)
        print(f"Ca = {Ca}, Da = {Da}")
        
        while True:
            Cb = random.randint(2, p-2)
            res = extended_gcd(Cb, p - 1)
            if res[0] == 1:
                break
        
        Db = res[1]
        if Db < 0:
            Db += (p - 1)
        print(f"Cb = {Cb}, Db = {Db}")

        Shamir(p, m, Ca, Da, Cb, Db)
    
    else:
        print("Неверный ввод")


if __name__ == "__main__":
    main()