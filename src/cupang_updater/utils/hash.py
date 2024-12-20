import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Self

from .common import ensure_path

_DEFAULT_CHUNK_SIZE = 64 * 2**10  # 64 KiB


@dataclass
class Hashes:
    """
    Attributes:
        md5 (str): The MD5 hash of the file.
        sha1 (str): The SHA-1 hash of the file.
        sha256 (str): The SHA-256 hash of the file.
        sha512 (str): The SHA-512 hash of the file.
    """

    md5: str = field(default=None)
    sha1: str = field(default=None)
    sha256: str = field(default=None)
    sha512: str = field(default=None)


class FileHash:
    def __init__(self, file: str | Path | IO[bytes]):
        self._file: Path | IO[bytes] = (
            ensure_path(file) if isinstance(file, str | Path) else file
        )
        self._hashes: Hashes = Hashes()

    @classmethod
    def with_known_hashes(
        cls, file: str | Path | IO[bytes], known_hashes: Hashes
    ) -> Self:
        """
        Create a new FileHash instance for the given file

        Args:
            file (str | Path | IO[bytes]): The path to the file for which to create the
                FileHash instance.
            known_hashes (dict[str, str], optional): A dictionary of known hash values
                for the file, where keys are hash algorithm names
                (e.g., 'md5', 'sha256') and values are the corresponding hash values.

        Returns:
            FileHash: A new instance of FileHash initialized with the given file
                and known hashes.
        """
        instance = cls(file)
        instance._hashes = known_hashes
        return instance

    @classmethod
    def dummy(cls) -> Self:
        return cls(__file__)

    def _hash(self, stream: IO[bytes], hash_tool) -> str:
        """
        Compute the hash of the given stream using the specified hash tool.

        Args:
            stream (IO[bytes]): The stream to read data from.
            hash_tool: The hashing tool to use for computing the hash.

        Returns:
            str: The computed hash value as a hexadecimal string.
        """
        stream.seek(0)
        while True:
            data = stream.read(_DEFAULT_CHUNK_SIZE)
            if not data:
                break
            hash_tool.update(data)
        return hash_tool.hexdigest()

    def _get_hash(self, hash_name: str) -> str:
        """
        Get or compute the hash value for the specified hash algorithm.

        Args:
            hash_name (str): The name of the hash algorithm to use
                (e.g., 'md5', 'sha256').

        Returns:
            str: The computed or cached hash value as a hexadecimal string.
        """
        if getattr(self._hashes, hash_name, None) is not None:
            return getattr(self._hashes, hash_name)

        hash_tool = hashlib.new(hash_name)
        if isinstance(self._file, str | Path):
            with self._file.open("rb") as stream:
                hash = self._hash(stream, hash_tool)
                setattr(self._hashes, hash_name, hash)
        else:
            hash = self._hash(self._file, hash_tool)
            setattr(self._hashes, hash_name, hash)
        return hash

    @property
    def md5(self) -> str:
        """
        Computes and returns the MD5 hash value of the file.

        Returns:
            str: The computed hash value as a hexadecimal string.
        """
        return self._get_hash("md5")

    @property
    def sha1(self) -> str:
        """
        Computes and returns the SHA-1 hash value of the file as a string.

        Returns:
            str: The computed hash value as a hexadecimal string.
        """
        return self._get_hash("sha1")

    @property
    def sha256(self) -> str:
        """
        Computes and returns the SHA-256 hash value of the file.

        Returns:
            str: The computed hash value as a hexadecimal string.
        """
        return self._get_hash("sha256")

    @property
    def sha512(self) -> str:
        """
        Computes and returns the SHA-512 hash value of the file.

        Returns:
            str: The computed hash value as a hexadecimal string.
        """
        return self._get_hash("sha512")
