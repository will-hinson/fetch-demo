from abc import ABCMeta, abstractmethod


class Encryptor(metaclass=ABCMeta):
    @abstractmethod
    def decrypt(self: "Encryptor", cipher_text: str) -> str: ...

    @abstractmethod
    def encrypt(self: "Encryptor", plain_text: str) -> str: ...
