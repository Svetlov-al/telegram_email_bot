from cryptography.fernet import Fernet


class PasswordCipher:
    """Класс шифрования пароля для обеспечения безопасности хранения в базе и передачи"""

    def __init__(self, key: str):
        self.cipher_suite = Fernet(key.encode())

    def encrypt_password(self, plain_password: str) -> bytes:
        """
        Шифрует переданный пароль.

        Аргументы:
            plain_password (str): Пароль, который необходимо зашифровать.

        Возвращает:
            bytes: Зашифрованный пароль.
        """
        return self.cipher_suite.encrypt(plain_password.encode())

    def decrypt_password(self, encrypted_password: bytes) -> str:
        """
        Расшифровывает переданный зашифрованный пароль.

        Аргументы:
            encrypted_password (bytes): Зашифрованный пароль для расшифровки.

        Возвращает:
            str: Расшифрованный пароль.
        """
        return self.cipher_suite.decrypt(encrypted_password).decode()
