import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from uuid import UUID

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import BadRequestException, ServiceException


@dataclass(frozen=True)
class TemporaryDocumentFile:
    path: Path
    sha256: str
    size_bytes: int


class DocumentStorageService:
    """Safe local source storage behind a replaceable storage abstraction."""

    chunk_size = 1024 * 1024

    def __init__(self, storage_root: str | Path | None = None) -> None:
        configured_root = storage_root or get_settings().document_storage_dir
        self.storage_root = Path(configured_root).expanduser().resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)

    async def write_temporary(
        self,
        upload: UploadFile,
        *,
        max_size_bytes: int,
    ) -> TemporaryDocumentFile:
        digest = hashlib.sha256()
        size_bytes = 0
        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(
                mode="wb",
                prefix=".upload-",
                suffix=".tmp",
                dir=self.storage_root,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while data := await upload.read(self.chunk_size):
                    size_bytes += len(data)
                    if size_bytes > max_size_bytes:
                        raise BadRequestException(
                            "PDF file is too large. Maximum allowed size is "
                            f"{max_size_bytes // (1024 * 1024)} MB."
                        )
                    digest.update(data)
                    temporary_file.write(data)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            if size_bytes == 0:
                raise BadRequestException("Uploaded PDF file is empty.")

            return TemporaryDocumentFile(
                path=temporary_path,
                sha256=digest.hexdigest(),
                size_bytes=size_bytes,
            )
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        finally:
            await upload.seek(0)

    def build_storage_key(self, document_id: str) -> str:
        normalized_id = str(UUID(document_id))
        return f"documents/{normalized_id}/source.pdf"

    def resolve_storage_key(self, storage_key: str) -> Path:
        key = PurePosixPath(storage_key)
        if (
            key.is_absolute()
            or ".." in key.parts
            or len(key.parts) != 3
            or key.parts[0] != "documents"
            or key.parts[2] != "source.pdf"
        ):
            raise ServiceException("Document storage key is invalid.")
        try:
            UUID(key.parts[1])
        except ValueError as exc:
            raise ServiceException("Document storage key is invalid.") from exc
        candidate = (self.storage_root / Path(*key.parts)).resolve()
        if not candidate.is_relative_to(self.storage_root):
            raise ServiceException("Document storage key is invalid.")
        return candidate

    def finalize(self, temporary: TemporaryDocumentFile, storage_key: str) -> Path:
        temp_path = temporary.path.resolve()
        if not temp_path.is_relative_to(self.storage_root) or not temp_path.is_file():
            raise ServiceException("Temporary document source is unavailable.")

        destination = self.resolve_storage_key(storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(temp_path, destination)
        except OSError as exc:
            raise ServiceException("Failed to persist the document source.") from exc
        return destination

    def read_bytes(self, storage_key: str) -> bytes:
        path = self.resolve_storage_key(storage_key)
        try:
            return path.read_bytes()
        except OSError as exc:
            raise ServiceException("Stored document source is unavailable.") from exc

    def exists(self, storage_key: str) -> bool:
        return self.resolve_storage_key(storage_key).is_file()

    def cleanup_temporary(self, temporary: TemporaryDocumentFile | None) -> None:
        if temporary is None:
            return
        path = temporary.path.resolve()
        if path.is_relative_to(self.storage_root):
            path.unlink(missing_ok=True)
