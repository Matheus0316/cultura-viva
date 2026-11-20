import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet

def get_cipher_suite():
    # Derivar uma chave de 32 bytes a partir do SECRET_KEY
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)

def encrypt_data(data):
    if not data:
        return data
    try:
        cipher_suite = get_cipher_suite()
        # Garantir que os dados sejam string antes de converter para bytes
        encoded_text = str(data).encode('utf-8')
        encrypted_text = cipher_suite.encrypt(encoded_text)
        return encrypted_text.decode('utf-8')
    except Exception as e:
        print(f"Erro na criptografia: {e}")
        return data

def decrypt_data(data):
    if not data:
        return data
    try:
        cipher_suite = get_cipher_suite()
        decoded_encrypted_text = str(data).encode('utf-8')
        decrypted_text = cipher_suite.decrypt(decoded_encrypted_text)
        return decrypted_text.decode('utf-8')
    except Exception as e:
        # Se falhar a descriptografia (ex: dado não está criptografado), retorna o dado original
        return data
