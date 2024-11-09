import hashlib
from pathlib import Path
from typing import BinaryIO, Self

from .common import ensure_path

_DEFAULT_CHUNK_SIZE = 64 * 2**10  # 64 KiB


class FileHash:
    def __init__(self, file: Path | str):
        self._file = ensure_path(file)
        self._hashes: dict[str, str] = {}

    @classmethod
    def new_file(cls, file: Path | str, known_hashes: dict[str, str] = None) -> Self:
        """
        Create a new FileHash instance for the given file

        Args:
            file (Path | str): The path to the file for which to create the FileHash instance.
            known_hashes (dict[str, str], optional): A dictionary of known hash values for the file,
                where keys are hash algorithm names (e.g., 'md5', 'sha256') and values are the corresponding hash values.

        Returns:
            FileHash: A new instance of FileHash initialized with the given file and known hashes.
        """
        instance = cls(file)
        if known_hashes is not None:
            instance._hashes.update(known_hashes)
        return instance

    def _hash(self, stream: BinaryIO, hash_tool) -> str:
        """
        Compute a hash of the given stream using the given hash tool.

        Args:
            stream (BinaryIO): The stream from which to read the data.
            hash_tool: The hash tool to use to compute the hash.

        Returns:
            str: The computed hash value as a hexadecimal string.
        """
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
            hash_name (str): The name of the hash algorithm to use (e.g., 'md5', 'sha256').

        Returns:
            str: The computed or cached hash value as a hexadecimal string.
        """
        if hash_name in self._hashes:
            return self._hashes[hash_name]

        hash_tool = hashlib.new(hash_name)
        with self._file.open("rb") as stream:
            hash = self._hash(stream, hash_tool)
            self._hashes[hash_name] = hash
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
