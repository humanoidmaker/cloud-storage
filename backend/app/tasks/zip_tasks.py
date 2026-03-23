import asyncio
import io
import uuid
import zipfile

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_folder_zip(self, folder_id: str, user_id: str) -> dict:
    """Generate a zip file for a folder download."""
    try:
        from app.database import async_session_factory
        from app.models.file import File
        from app.services.storage_service import StorageService

        from sqlalchemy import and_, select

        storage = StorageService()

        async def _generate() -> str:
            async with async_session_factory() as session:
                # Collect all files in the folder recursively
                files_to_zip: list[tuple[str, str]] = []  # (path, storage_key)
                fid = uuid.UUID(folder_id)

                async def collect_files(current_folder_id: uuid.UUID, path_prefix: str) -> None:
                    result = await session.execute(
                        select(File).where(
                            and_(
                                File.parent_folder_id == current_folder_id,
                                File.owner_id == uuid.UUID(user_id),
                                File.is_trashed == False,
                            )
                        )
                    )
                    items = list(result.scalars().all())
                    for item in items:
                        item_path = f"{path_prefix}/{item.name}" if path_prefix else item.name
                        if item.is_folder:
                            await collect_files(item.id, item_path)
                        elif item.storage_key:
                            files_to_zip.append((item_path, item.storage_key))

                # Get folder name
                folder = await session.get(File, fid)
                folder_name = folder.name if folder else "download"

                await collect_files(fid, "")

                # Create zip in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for file_path, storage_key in files_to_zip:
                        try:
                            content = storage.download_file(storage_key)
                            zf.writestr(file_path, content)
                        except Exception:
                            continue  # Skip files that can't be downloaded

                zip_buffer.seek(0)

                # Upload zip to storage
                zip_key = f"_zips/{user_id}/{folder_id}.zip"
                storage.upload_file(
                    zip_buffer.getvalue(),
                    zip_key,
                    content_type="application/zip",
                )

                return zip_key

        loop = asyncio.new_event_loop()
        try:
            zip_key = loop.run_until_complete(_generate())
        finally:
            loop.close()

        return {"status": "success", "zip_key": zip_key}
    except Exception as exc:
        self.retry(exc=exc)
        return {"status": "error", "error": str(exc)}
