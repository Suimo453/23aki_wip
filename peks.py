import hashlib
from bls12381 import ecp
from bls12381 import ecp2
from bls12381 import curve
from bls12381 import big
from bls12381.ecp import ECp
from bls12381.ecp2 import ECp2
from bls12381 import pair
from bls12381.fp12 import Fp12
from flask import Flask, request

G2_TAB = []

def init():
    global G2_TAB
    G = ecp2.generator()
    if G.isinf():
        return False
    G2_TAB = pair.precomp(G)
    return True

def BLS_H(m):
    h = hashlib.shake_256()
    h.update(bytes(m, 'utf-8'))
    hm = big.from_bytes(h.digest(curve.EFS))
    HM = ECp()
    while not HM.set(hm):
        hm = hm + 1
    HM = curve.CurveCof * HM

    return HM


import base64
# 鍵ペア（秘密鍵SKと公開鍵PK）を生成する関数

def KeyPairGenerate():
    G = ecp2.generator()
    SK = big.rand(curve.r)
    PK = (SK * G).toBytes(True)

    SK = big.to_bytes(SK)
    SK = base64.b64encode(SK)
    PK = base64.b64encode(PK)

    return (SK, PK)

# PEKS
def PKES(tag,PK):
    _PK = base64.b64decode(PK)
    PK = ecp2.generator()
    PK.fromBytes(_PK)

    G = ecp2.generator()
    r = big.rand(curve.r)
    cipher_tag1 = (r * G).toBytes(True)

    h_tag = BLS_H(tag)
    h_r = r * PK

    cipher_tag2 = pair.ate(h_r,h_tag)
    cipher_tag2 = pair.fexp(cipher_tag2).toBytes()

    cipher_tag = base64.b64encode(cipher_tag1).decode('utf-8') + '.' + base64.b64encode(cipher_tag2).decode('utf-8')
    return cipher_tag

def Trapdoor(s,tag):
    _s = base64.b64decode(s)
    s = big.from_bytes(_s)

    h_tag = BLS_H(tag)
    trapdoor = (s * h_tag).toBytes(True)
    trapdoor = base64.b64encode(trapdoor)
    return trapdoor

def Test(trapdoor,cipher_tag):
    _trapdoor = base64.b64decode(trapdoor)
    trapdoor = ecp.generator()
    trapdoor.fromBytes(_trapdoor)

    cipher_tags = cipher_tag.split('.')
    _cipher_tag1 = base64.b64decode(cipher_tags[0])
    cipher_tag1 = ecp2.generator()
    cipher_tag1.fromBytes(_cipher_tag1)
    
    _cipher_tag2 = base64.b64decode(cipher_tags[1])
    cipher_tag2 = Fp12()
    cipher_tag2.fromBytes(_cipher_tag2)

    trap_tag = pair.ate(cipher_tag1,trapdoor)
    trap_tag = pair.fexp(trap_tag)

    return trap_tag == cipher_tag2

## テキストの暗号化
def encrypt(text, PK):
    _PK = base64.b64decode(PK)
    PK = ecp2.generator()
    PK.fromBytes(_PK)

    text_bytes = bytes(text, 'utf-8')

    r = big.rand(curve.r)
    cipher_text1 = (r * PK).toBytes(True)

    h_text = BLS_H(text)

    cipher_text2 = pair.ate(h_text, r * ecp2.generator())
    cipher_text2 = pair.fexp(cipher_text2).toBytes()

    encrypted_text = base64.b64encode(cipher_text1).decode('utf-8') + '.' + base64.b64encode(cipher_text2).decode('utf-8')
    return encrypted_text

## 暗号文の複合
def decrypt(encrypted_text, SK):
    _SK = base64.b64decode(SK)
    SK = ecp2.generator()
    SK.fromBytes(_SK)
    cipher_parts = encrypted_text.split('.')
    _cipher_text1 = base64.b64decode(cipher_parts[0])
    _cipher_text2 = base64.b64decode(cipher_parts[1])
    cipher_text1 = ecp2.generator()
    cipher_text1.fromBytes(_cipher_text1)
    cipher_text2 = Fp12()
    cipher_text2.fromBytes(_cipher_text2)
    decrypted_text = pair.ate(SK, cipher_text1)
    decrypted_text = pair.fexp(decrypted_text)
    h_decrypted_text = BLS_H(decrypted_text.toBytes())
    original_text_hash = BLS_H("元のテキスト")  # 元のテキストをハッシュ
    if h_decrypted_text == original_text_hash:
        return decrypted_text.toBytes().decode('utf-8')
    

init()
sk,pk  = KeyPairGenerate()

    ## 名前と名字の暗号化
cipher_tag = PKES("検索キーワード部分",pk)
    ## 検索にかけたキーワードの暗号化
trapdoor = Trapdoor(sk,"検索に入力する部分")

test = encrypt("atsu",pk)
print(test)


result = Test(trapdoor,cipher_tag)
print(result)

