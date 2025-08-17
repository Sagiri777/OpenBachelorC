import base64
from .config import config

ENCODED_GADGET = "YW5pbWUucHZ6Lm9ubGluZQ=="
ENCODED_DEFAULT = "Y29tLmh5cGVyZ3J5cGguYXJrbmlnaHRz

if config["use_gadget"]:
    PACKAGE_NAME = base64.b64decode(ENCODED_GADGET).decode('utf-8')
else:
    PACKAGE_NAME = base64.b64decode(ENCODED_DEFAULT).decode('utf-8')
