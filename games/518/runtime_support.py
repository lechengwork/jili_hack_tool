"""Portable local replay helpers (Windows/macOS/Linux)."""
import datetime
import os
from pathlib import Path
import shutil


def chrome_path():
    candidates = [os.environ.get('CHROME', ''),
                  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
    for base in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        if os.environ.get(base):
            candidates.append(str(Path(os.environ[base]) / 'Google/Chrome/Application/chrome.exe'))
    candidates.extend(shutil.which(n) or '' for n in ('google-chrome', 'chromium', 'chromium-browser'))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError('Google Chrome not found. Set CHROME to its executable path.')


def local_certificate(directory):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    cert, key = directory / 'local.crt', directory / 'local.key'
    if cert.exists() and key.exists():
        return cert, key
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    now = datetime.datetime.utcnow()
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
                   .public_key(private.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - datetime.timedelta(days=1))
                   .not_valid_after(now + datetime.timedelta(days=3650))
                   .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), critical=False)
                   .sign(private, hashes.SHA256()))
    key.write_bytes(private.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
    key.chmod(0o600)
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert, key
