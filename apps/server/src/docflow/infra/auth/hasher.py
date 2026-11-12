from __future__ import annotations

import hashlib
import hmac
import secrets


class PasswordHasher:
    """Implementa hash e verificação de senhas suportando scrypt (formato BE-04) e Argon2."""

    def __init__(self, n: int = 2**14, r: int = 8, p: int = 1) -> None:
        self.n = n
        self.r = r
        self.p = p

    def hash(self, password: str) -> str:
        """Gera hash scrypt no formato BE-04: scrypt$<salt_hex>$<digest_hex>."""
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=self.n,
            r=self.r,
            p=self.p,
        )
        return f"scrypt${salt.hex()}${digest.hex()}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha plana corresponde ao hash armazenado."""
        if not plain_password or not hashed_password:
            return False

        if hashed_password.startswith("scrypt$"):
            return self._verify_scrypt(plain_password, hashed_password)

        if hashed_password.startswith("$argon2") or hashed_password.startswith("argon2$"):
            return self._verify_argon2(plain_password, hashed_password)

        return False

    def _verify_scrypt(self, plain_password: str, hashed_password: str) -> bool:
        try:
            parts = hashed_password.split("$")
            if len(parts) == 3:
                # Formato BE-04: scrypt$<salt_hex>$<digest_hex>
                salt = bytes.fromhex(parts[1])
                expected_digest = bytes.fromhex(parts[2])
                computed_digest = hashlib.scrypt(
                    plain_password.encode("utf-8"),
                    salt=salt,
                    n=self.n,
                    r=self.r,
                    p=self.p,
                )
                return hmac.compare_digest(computed_digest, expected_digest)
            if len(parts) == 6:
                # Formato parametrizado: scrypt$<n>$<r>$<p>$<salt_hex>$<digest_hex>
                n = int(parts[1])
                r = int(parts[2])
                p = int(parts[3])
                salt = bytes.fromhex(parts[4])
                expected_digest = bytes.fromhex(parts[5])
                computed_digest = hashlib.scrypt(
                    plain_password.encode("utf-8"),
                    salt=salt,
                    n=n,
                    r=r,
                    p=p,
                )
                return hmac.compare_digest(computed_digest, expected_digest)
        except Exception:
            return False
        return False

    def _verify_argon2(self, plain_password: str, hashed_password: str) -> bool:
        try:
            import argon2  # type: ignore[import-not-found]

            ph = argon2.PasswordHasher()
            ph.verify(hashed_password, plain_password)
            return True
        except Exception:
            return False


default_hasher = PasswordHasher()
