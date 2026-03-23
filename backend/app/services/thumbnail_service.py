import io
import uuid

from app.services.storage_service import StorageService


class ThumbnailService:
    MAX_SIZE = (300, 300)

    def __init__(self, storage: StorageService | None = None):
        self.storage = storage or StorageService()

    def generate_thumbnail(self, file_content: bytes, mime_type: str) -> bytes | None:
        """Generate a thumbnail for supported file types.
        Returns JPEG bytes for the thumbnail, or None if unsupported/error.
        """
        if not file_content:
            return None

        mime_lower = (mime_type or "").lower()

        try:
            if mime_lower.startswith("image/"):
                return self._thumbnail_from_image(file_content)
            elif mime_lower == "application/pdf":
                return self._thumbnail_from_pdf(file_content)
            else:
                return None
        except Exception:
            return None

    def _thumbnail_from_image(self, content: bytes) -> bytes | None:
        """Generate thumbnail from image bytes."""
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(content))
            # Convert RGBA/P to RGB for JPEG
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img.thumbnail(self.MAX_SIZE, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            return output.getvalue()
        except Exception:
            return None

    def _thumbnail_from_pdf(self, content: bytes) -> bytes | None:
        """Generate thumbnail from PDF first page."""
        try:
            from pdf2image import convert_from_bytes
            from PIL import Image

            images = convert_from_bytes(content, first_page=1, last_page=1, size=self.MAX_SIZE)
            if not images:
                return None

            img = images[0]
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail(self.MAX_SIZE, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            return output.getvalue()
        except Exception:
            return None

    async def generate_and_store(
        self, file_id: uuid.UUID, file_content: bytes, mime_type: str
    ) -> str | None:
        """Generate thumbnail and store it in MinIO. Returns thumbnail key or None."""
        thumb_bytes = self.generate_thumbnail(file_content, mime_type)
        if not thumb_bytes:
            return None

        try:
            key = self.storage.upload_thumbnail(file_id, thumb_bytes)
            return key
        except Exception:
            return None
