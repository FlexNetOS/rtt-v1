#!/usr/bin/env python3
import sys, base64, subprocess, shutil
def sign(priv_b64: str, msg: bytes) -> str:
    try:
        from nacl.signing import SigningKey
        sk = SigningKey(base64.b64decode(priv_b64))
        sig = sk.sign(msg).signature
        return base64.b64encode(sig).decode()
    except Exception:
        exe = shutil.which("rtt-sign")
        if not exe: raise SystemExit("No nacl and no rtt-sign CLI")
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(msg); tf.flush()
            out = subprocess.check_output([exe, "sign", priv_b64, tf.name])
            return out.decode().strip()
def verify(pub_b64: str, msg: bytes, sig_b64: str) -> bool:
    try:
        from nacl.signing import VerifyKey
        vk = VerifyKey(base64.b64decode(pub_b64))
        vk.verify(msg, base64.b64decode(sig_b64))
        return True
    except Exception:
        exe = shutil.which("rtt-sign")
        if not exe: return False
        import tempfile, subprocess
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(msg); tf.flush()
            try:
                out = subprocess.check_output([exe, "verify", pub_b64, tf.name, sig_b64])
                return out.decode().strip().startswith("OK")
            except subprocess.CalledProcessError:
                return False
