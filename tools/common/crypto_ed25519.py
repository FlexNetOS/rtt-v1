# Tries PyNaCl first, else external 'rtt-sign' binary must exist in PATH.
import base64, shutil, subprocess, tempfile
def sign(priv_b64: str, msg: bytes) -> str:
    try:
        from nacl.signing import SigningKey
        sk = SigningKey(base64.b64decode(priv_b64))
        sig = sk.sign(msg).signature
        return base64.b64encode(sig).decode()
    except Exception:
        exe = shutil.which("rtt-sign")
        if not exe: raise RuntimeError("PyNaCl missing and rtt-sign not found")
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(msg); tf.flush()
            out = subprocess.check_output([exe, "sign", priv_b64, tf.name])
            return out.decode().strip()
