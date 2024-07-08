import binascii
import pyaes

from .encryptor import Encryptor


class AesEncryptor(Encryptor):
    __key: bytes

    def __init__(self: "AesEncryptor", key: bytes) -> None:
        self.__key = key

    def decrypt(self: Encryptor, cipher_text: str) -> str:
        aes: pyaes.AESModeOfOperationCTR = pyaes.AESModeOfOperationCTR(self.__key)
        return aes.decrypt(binascii.unhexlify(cipher_text)).decode("utf-8")

    def encrypt(self: "AesEncryptor", plain_text: str) -> str:
        aes: pyaes.AESModeOfOperationCTR = pyaes.AESModeOfOperationCTR(self.__key)
        return binascii.hexlify(aes.encrypt(plain_text)).decode("utf-8")
