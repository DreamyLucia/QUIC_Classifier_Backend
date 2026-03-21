from Crypto.PublicKey import RSA


def generate_rsa_keys(key_size: int = 2048):
    """
    生成 RSA 密钥对

    Args:
        key_size: 密钥大小（位），推荐 2048 或 4096
    """
    print(f"   密钥长度: {key_size} 位")

    # 生成密钥对
    key = RSA.generate(key_size)

    # 导出私钥
    private_key = key.export_key()
    with open('private_key.pem', 'wb') as f:
        f.write(private_key)
    print("✅ 私钥已保存: private_key.pem")

    # 导出公钥
    public_key = key.publickey().export_key()
    with open('public_key.pem', 'wb') as f:
        f.write(public_key)
    print("✅ 公钥已保存: public_key.pem")

    return key


if __name__ == "__main__":
    generate_rsa_keys(2048)