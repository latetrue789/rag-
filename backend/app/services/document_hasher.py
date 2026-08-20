from hashlib import sha256
from pathlib import Path


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while block := source.read(block_size):
            digest.update(block)
    return digest.hexdigest()
