
To use key-pair authentication for Snowflake, you will pass the private key as a connection argument with `kwargs` in addition to passing connection details with the `connection_string` parameter. Here's an example of how to access your private key in Python.

```python title="Python"
import pathlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

PRIVATE_KEY_FILE = pathlib.Path("path/to/my/rsa_key.p8").resolve(strict=True)

p_key = serialization.load_pem_private_key(
        PRIVATE_KEY_FILE.read_bytes(),
        password=b"my_password",
        backend=default_backend()
    )

pkb = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption())

connect_args = {"private_key": pkb}
```