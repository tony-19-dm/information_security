import os
import random
import struct
from typing import List, Tuple
from lab1 import ferm_test, fast_pow, extended_gcd

def choose_block_size_for_N(N: int) -> int:
    if N <= 2:
        raise ValueError("N слишком мало")
    k = (N.bit_length() - 1) // 8
    if k < 1:
        k = 1
    return k

def rsa_encrypt_block(m: int, N: int, d: int) -> int:
    return fast_pow(m, d, N)

def rsa_decrypt_block(e_val: int, N: int, c: int) -> int:
    return fast_pow(e_val, c, N)

def three_party_protocol():

    print("\n1. Генерация ключей Алисы:")
    while True:
        q_a = random.randint(1000000, 1000000000)
        if ferm_test(q_a):
            p_a = 2 * q_a + 1
            if ferm_test(p_a):
                break
    N_a = p_a * q_a
    phi_a = (p_a - 1) * (q_a - 1)
    while True:
        d_a = random.randint(2, phi_a - 1)
        if extended_gcd(d_a, phi_a)[0] == 1:
            break
    g, xinv, y = extended_gcd(d_a, phi_a)
    c_a = xinv % phi_a
    
    print(f"Алиса: N_a={N_a}, d_a={d_a}, c_a={c_a}")
    
    print("\n2. Генерация ключей Боба:")
    while True:
        q_b = random.randint(1000000, 1000000000)
        if ferm_test(q_b):
            p_b = 2 * q_b + 1
            if ferm_test(p_b):
                break
    N_b = p_b * q_b
    phi_b = (p_b - 1) * (q_b - 1)
    while True:
        d_b = random.randint(2, phi_b - 1)
        if extended_gcd(d_b, phi_b)[0] == 1:
            break
    g, xinv, y = extended_gcd(d_b, phi_b)
    c_b = xinv % phi_b
    
    print(f"Боб: N_b={N_b}, d_b={d_b}, c_b={c_b}")
    
    message = input("\nВведите сообщение для передачи: ").strip()
    message_bytes = message.encode('utf-8')
    
    min_N = min(N_a, N_b)
    block_size = choose_block_size_for_N(min_N)
    print(f"\nРазмер блока: {block_size} байт")

    alice_encrypted = []
    for i in range(0, len(message_bytes), block_size):
        block = message_bytes[i:i+block_size]
        if len(block) < block_size:
            block = block + b'\x00' * (block_size - len(block))
        m = int.from_bytes(block, byteorder='big')
        if m >= N_a:
            raise ValueError(f"Блок слишком велик для N_a")
        e = rsa_encrypt_block(m, N_a, c_a)  # e = m^c_A mod N_a
        alice_encrypted.append(e)
    
    double_encrypted = []
    for e_val in alice_encrypted:
        if e_val >= N_b:
            raise ValueError(f"Промежуточный блок слишком велик для N_b")
        f = rsa_encrypt_block(e_val, N_b, d_b)  # f = e^d_B mod N_b
        double_encrypted.append(f)
    
    bob_decrypted = []
    for f_val in double_encrypted:
        u = rsa_decrypt_block(f_val, N_b, c_b)  # u = f^c_B mod N_b
        bob_decrypted.append(u)
    
    final_decrypted = bytearray()
    for u_val in bob_decrypted:
        w = rsa_decrypt_block(u_val, N_a, d_a)  # w = u^d_A mod N_a
        block_bytes = w.to_bytes(block_size, byteorder='big')
        final_decrypted.extend(block_bytes)
    
    final_message = bytes(final_decrypted).rstrip(b'\x00').decode('utf-8')
    
    print(f"Исходное сообщение: {message}")
    print(f"Полученное сообщение: {final_message}")
    print(f"Совпадение: {message == final_message}")
    
    if message == final_message:
        print("Сообщение передано безопасно.")
    else:
        print("Ошибка!")

if __name__ == "__main__":

    three_party_protocol()
