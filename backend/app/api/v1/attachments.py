import mimetypes
import os
import uuid
import zipfile
from io import BytesIO

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.attachment import TicketAttachment
from app.models.audit import AuditLog
from app.models.enums import TicketStatus, UserRole
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.ticket import AttachmentOut


router = APIRouter()


FILE_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "gif": [b"GIF87a", b"GIF89a"],
    "zip": [
        b"PK\x03\x04",
        b"PK\x05\x06",
        b"PK\x07\x08",
    ],
}


def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""

    return filename.rsplit(".", 1)[-1].lower()


def can_access_ticket(user: User, ticket: Ticket) -> bool:
    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.AGENT:
        return (
            ticket.assigned_agent_id == user.id
            or ticket.assigned_agent_id is None
        )

    if user.role == UserRole.CUSTOMER:
        return ticket.customer_id == user.id

    return False


def validate_file_content(ext: str, content: bytes) -> bool:
    if ext in FILE_SIGNATURES:
        return any(
            content.startswith(signature)
            for signature in FILE_SIGNATURES[ext]
        )

    if ext == "txt":
        try:
            content.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False

    if ext in {"doc", "docx", "xls", "xlsx"}:
        if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            return True

        if content.startswith(b"PK\x03\x04"):
            try:
                with zipfile.ZipFile(BytesIO(content)) as archive:
                    return archive.testzip() is None
            except zipfile.BadZipFile:
                return False

        return False

    return False


def validate_file(
    file: UploadFile,
    content: bytes,
) -> tuple[str, str]:

    if len(content) == 0:
        raise ValidationException("Uploaded file is empty")

    if len(content) > settings.max_upload_size_bytes:
        raise ValidationException(
            f"File exceeds maximum size of "
            f"{settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    filename = file.filename or ""
    ext = get_extension(filename)

    if ext not in settings.allowed_extensions_list:
        raise ValidationException(
            f"File extension '{ext}' not allowed"
        )

    if not validate_file_content(ext, content):
        raise ValidationException(
            f"File content does not match the '{ext}' file type"
        )

    client_mime = (file.content_type or "").lower()

    guessed_mime, _ = mimetypes.guess_type(filename)
    guessed_mime = (guessed_mime or "").lower()

    allowed_mimes = settings.allowed_mime_types_list

    if client_mime and client_mime not in allowed_mimes:
        raise ValidationException(
            f"MIME type '{client_mime}' not allowed"
        )

    if guessed_mime and guessed_mime not in allowed_mimes:
        raise ValidationException(
            f"MIME type '{guessed_mime}' not allowed"
        )

    if ext in {"png", "jpg", "jpeg", "gif"}:
        try:
            from PIL import Image

            with Image.open(BytesIO(content)) as image:
                image.verify()

        except Exception:
            raise ValidationException(
                "Uploaded image is invalid or corrupted"
            )

    mime = client_mime or guessed_mime or "application/octet-stream"

    return ext, mime


@router.post(
    "/{ticket_id}/attachments",
    response_model=ResponseModel[AttachmentOut],
    status_code=201,
)
async def upload_attachment(
    ticket_id: int,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException("Access denied")

    if ticket.status == TicketStatus.CLOSED:
        raise ValidationException(
            "Cannot upload attachments to a closed ticket. "
            "Please reopen the ticket first."
        )

    content = await file.read()

    ext, mime = validate_file(file, content)

    stored_name = f"{uuid.uuid4().hex}.{ext}"

    os.makedirs(
        settings.UPLOAD_DIR,
        exist_ok=True,
    )

    path = os.path.join(
        settings.UPLOAD_DIR,
        stored_name,
    )

    try:
        with open(path, "wb") as output_file:
            output_file.write(content)

        attachment = TicketAttachment(
            ticket_id=ticket_id,
            uploaded_by_id=current_user.id,
            file_name=stored_name,
            original_name=file.filename or stored_name,
            file_type=ext,
            mime_type=mime,
            file_size=len(content),
            storage_path=path,
        )

        db.add(attachment)
        db.flush()

        audit_log = AuditLog(
            user_id=current_user.id,
            action="ATTACHMENT_UPLOADED",
            entity="attachment",
            entity_id=attachment.id,
            ip_address=get_client_ip(request),
        )

        db.add(audit_log)

        db.commit()
        db.refresh(attachment)

    except Exception:
        db.rollback()

        if os.path.exists(path):
            os.remove(path)

        raise

    return ResponseModel(
        data=AttachmentOut.model_validate(attachment),
        message="Attachment uploaded",
    )


@router.get(
    "/{ticket_id}/attachments",
    response_model=ResponseModel[list[AttachmentOut]],
)
def list_attachments(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException("Access denied")

    attachments = (
        db.query(TicketAttachment)
        .filter(TicketAttachment.ticket_id == ticket_id)
        .order_by(TicketAttachment.created_at.desc())
        .all()
    )

    return ResponseModel(
        data=[
            AttachmentOut.model_validate(attachment)
            for attachment in attachments
        ]
    )


@router.get(
    "/{ticket_id}/attachments/{attachment_id}/download"
)
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attachment = (
        db.query(TicketAttachment)
        .filter(
            TicketAttachment.id == attachment_id,
            TicketAttachment.ticket_id == ticket_id,
        )
        .first()
    )

    if not attachment:
        raise NotFoundException("Attachment not found")

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException("Access denied")

    if not os.path.exists(attachment.storage_path):
        raise NotFoundException("File not found on storage")

    return FileResponse(
        attachment.storage_path,
        filename=attachment.original_name,
        media_type=attachment.mime_type,
    )


@router.delete(
    "/{ticket_id}/attachments/{attachment_id}",
    response_model=ResponseModel,
)
def delete_attachment(
    ticket_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attachment = (
        db.query(TicketAttachment)
        .filter(
            TicketAttachment.id == attachment_id,
            TicketAttachment.ticket_id == ticket_id,
        )
        .first()
    )

    if not attachment:
        raise NotFoundException("Attachment not found")

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise NotFoundException("Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise ForbiddenException("Access denied")

    if (
        current_user.role != UserRole.ADMIN
        and attachment.uploaded_by_id != current_user.id
    ):
        raise ForbiddenException(
            "You can only delete your own attachments"
        )

    if os.path.exists(attachment.storage_path):
        os.remove(attachment.storage_path)

    db.delete(attachment)
    db.commit()

    return ResponseModel(
        message="Attachment deleted"
    )