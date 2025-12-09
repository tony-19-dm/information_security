from lab1 import ferm_test, extended_gcd, fast_pow

p =17
q=7
c=77
N=119
d=5
h=11
r=5

_h = h * fast_pow(r,d,N) % N

_s = fast_pow(_h, c, N)

gcd, ir, _ = extended_gcd(r, N)

s = _s * ir % N

vali = fast_pow(h, c, N)

valis = fast_pow(s, d, N)

print(_h, _s, ir, s, vali, valis)