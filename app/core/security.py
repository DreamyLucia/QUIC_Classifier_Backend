import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from app.core.config import settings


class RSAUtil:
    """RSA 加密解密工具类"""

    _private_key = None
    _public_key = None

    @classmethod
    def _load_private_key(cls):
        """加载私钥（只加载一次）"""
        if cls._private_key is None:
            with open(settings.PRIVATE_KEY_PATH, 'rb') as f:
                cls._private_key = RSA.import_key(f.read())
        return cls._private_key

    @classmethod
    def _load_public_key(cls):
        """加载公钥（只加载一次）"""
        if cls._public_key is None:
            with open(settings.PUBLIC_KEY_PATH, 'rb') as f:
                cls._public_key = RSA.import_key(f.read())
        return cls._public_key

    @classmethod
    def get_public_key_pem(cls) -> str:
        """
        获取公钥字符串

        Returns:
            PEM 格式的公钥字符串
        """
        public_key = cls._load_public_key()
        return public_key.export_key().decode('utf-8')

    @classmethod
    def decrypt_password(cls, encrypted_password: str) -> str:
        """
        用私钥解密前端传来的密码

        Args:
            encrypted_password: base64 编码的加密密码

        Returns:
            解密后的明文密码
        """
        try:
            private_key = cls._load_private_key()
            cipher = PKCS1_v1_5.new(private_key)

            # base64 解码
            encrypted_data = base64.b64decode(encrypted_password)

            # 解密（sentinel 用于处理解密失败）
            sentinel = None
            decrypted = cipher.decrypt(encrypted_data, sentinel)

            if decrypted is None:
                raise ValueError("解密失败，可能是密钥不匹配")

            return decrypted.decode('utf-8')

        except Exception as e:
            print(f"RSA 解密失败: {e}")
            raise ValueError("密码解密失败")