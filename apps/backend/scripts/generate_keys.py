"""Génère la paire de clés RSA (RS256) utilisée pour signer/vérifier les JWT.

Usage:
    python scripts/generate_keys.py
"""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main() -> None:
    keys_dir = Path(__file__).resolve().parent.parent / "keys"
    keys_dir.mkdir(exist_ok=True)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    (keys_dir / "private.pem").write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    (keys_dir / "public.pem").write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    print(f"Clés RSA générées dans {keys_dir}")


if __name__ == "__main__":
    main()
