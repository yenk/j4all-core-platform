"""
Documents router for LumiLens API.

Provides endpoints for document upload, processing, and management
with support for various file formats and batch operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import os
import tempfile
from pathlib import Path
import mimetypes

from api.config import Settings, get_settings
from api.core.exceptions import ValidationException, VectorStoreException
from api.services.vector_service import VectorService

logger = logging.getLogger(__name__)
router = APIRouter()


class DocumentInfo(BaseModel):
    """Document information model."""
    id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="Document file type")
    file_size: int = Field(..., description="File size in bytes")
    upload_timestamp: str = Field(..., description="Upload timestamp")
    processing_status: str = Field(..., description="Processing status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")


class BatchUploadResponse(BaseModel):
    """Batch upload response model."""
    total_files: int = Field(..., description="Total number of files uploaded")
    successful_uploads: int = Field(..., description="Number of successful uploads")
    failed_uploads: int = Field(..., description="Number of failed uploads")
    documents: List[DocumentUploadResponse] = Field(..., description="Individual upload results")
    errors: List[str] = Field(default_factory=list, description="Upload errors")


# Supported file types
SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc"
}

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    process_immediately: bool = Form(default=True),
    settings: Settings = Depends(get_settings)
):
    """
    Upload a single document for processing.
    
    Args:
        file: Document file to upload
        process_immediately: Whether to process the document immediately
        settings: Application settings dependency
        
    Returns:
        DocumentUploadResponse: Upload result with document information
        
    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        logger.info("📁 Processing document upload: %s", file.filename)
        
        # Validate file
        await _validate_uploaded_file(file, settings)
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Generate document ID
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Process document if requested
            status = "uploaded"
            message = "Document uploaded successfully"
            
            if process_immediately:
                try:
                    vector_service = VectorService()
                    # Process the single file (implementation depends on file type)
                    await _process_single_document(temp_file_path, file.filename, vector_service)
                    status = "processed"
                    message = "Document uploaded and processed successfully"
                except Exception as e:
                    logger.warning("⚠️ Document processing failed: %s", str(e))
                    status = "processing_failed"
                    message = f"Document uploaded but processing failed: {str(e)}"
            
            return DocumentUploadResponse(
                document_id=doc_id,
                filename=file.filename,
                file_size=len(content),
                status=status,
                message=message
            )
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning("Failed to clean up temp file: %s", str(e))
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error("❌ Document upload failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Document upload failed: {str(e)}"
        )


@router.post("/documents/upload-batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    process_immediately: bool = Form(default=True),
    settings: Settings = Depends(get_settings)
):
    """
    Upload multiple documents for batch processing.
    
    Args:
        files: List of document files to upload
        process_immediately: Whether to process documents immediately
        settings: Application settings dependency
        
    Returns:
        BatchUploadResponse: Batch upload results
        
    Raises:
        HTTPException: If batch upload fails
    """
    try:
        logger.info("📁 Processing batch upload of %d files", len(files))
        
        if len(files) > 50:  # Limit batch size
            raise ValidationException("Too many files in batch. Maximum 50 files allowed.")
        
        upload_results = []
        errors = []
        successful_uploads = 0
        
        for file in files:
            try:
                # Process each file individually
                result = await upload_document(
                    file=file,
                    process_immediately=process_immediately,
                    settings=settings
                )
                upload_results.append(result)
                
                if result.status in ["processed", "uploaded"]:
                    successful_uploads += 1
                    
            except Exception as e:
                error_msg = f"Failed to upload {file.filename}: {str(e)}"
                errors.append(error_msg)
                logger.error("❌ %s", error_msg)
                
                # Add failed upload result
                upload_results.append(DocumentUploadResponse(
                    document_id="",
                    filename=file.filename,
                    file_size=0,
                    status="failed",
                    message=str(e)
                ))
        
        return BatchUploadResponse(
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=len(files) - successful_uploads,
            documents=upload_results,
            errors=errors
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error("❌ Batch upload failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.post("/documents/ingest-directory")
async def ingest_documents_directory(
    directory_path: Optional[str] = None,
    settings: Settings = Depends(get_settings)
):
    """
    Ingest all documents from a directory into the vector store.
    
    Args:
        directory_path: Path to directory (uses default if not provided)
        settings: Application settings dependency
        
    Returns:
        dict: Ingestion results
        
    Raises:
        HTTPException: If ingestion fails
    """
    try:
        data_path = directory_path or settings.DATA_PATH
        logger.info("📂 Starting directory ingestion: %s", data_path)
        
        vector_service = VectorService()
        document_count = await vector_service.ingest_documents_from_directory(data_path)
        
        return {
            "message": f"Successfully ingested {document_count} documents",
            "directory_path": data_path,
            "documents_processed": document_count,
            "status": "completed"
        }
        
    except VectorStoreException as e:
        logger.error("❌ Directory ingestion failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Directory ingestion failed: {str(e)}"
        )
    except Exception as e:
        logger.error("❌ Unexpected error during ingestion: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get("/documents/stats")
async def get_document_statistics(settings: Settings = Depends(get_settings)):
    """
    Get statistics about documents in the vector store.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        dict: Document statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        vector_service = VectorService()
        stats = await vector_service.get_collection_stats()
        
        # Add additional statistics
        data_path = Path(settings.DATA_PATH)
        pdf_files = list(data_path.rglob("*.pdf")) if data_path.exists() else []
        
        stats.update({
            "source_files": {
                "pdf_count": len(pdf_files),
                "data_directory": str(data_path),
                "directory_exists": data_path.exists()
            },
            "settings": {
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "max_file_size": settings.MAX_FILE_SIZE
            }
        })
        
        return stats
        
    except Exception as e:
        logger.error("❌ Failed to get document statistics: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/documents/supported-formats")
async def get_supported_formats():
    """
    Get list of supported document formats.
    
    Returns:
        dict: Supported file formats and extensions
    """
    return {
        "supported_extensions": list(SUPPORTED_EXTENSIONS),
        "mime_types": SUPPORTED_MIME_TYPES,
        "max_file_size": get_settings().MAX_FILE_SIZE,
        "max_batch_size": 50
    }


async def _validate_uploaded_file(file: UploadFile, settings: Settings) -> None:
    """
    Validate uploaded file format and size.
    
    Args:
        file: Uploaded file to validate
        settings: Application settings
        
    Raises:
        ValidationException: If file validation fails
    """
    # Check file extension
    if file.filename:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise ValidationException(
                f"Unsupported file type: {file_ext}. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
    else:
        raise ValidationException("Filename is required")
    
    # Check MIME type if available
    if file.content_type and file.content_type not in SUPPORTED_MIME_TYPES:
        # Some browsers might not set correct MIME type, so we'll be lenient
        logger.warning("⚠️ Unexpected MIME type: %s for file: %s", file.content_type, file.filename)
    
    # Check file size (read first to get size, then reset)
    content = await file.read()
    await file.seek(0)  # Reset file pointer
    
    if len(content) > settings.MAX_FILE_SIZE:
        size_mb = len(content) / (1024 * 1024)
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationException(
            f"File too large: {size_mb:.1f}MB. Maximum size: {max_mb:.1f}MB"
        )
    
    if len(content) == 0:
        raise ValidationException("File is empty")


async def _process_single_document(
    file_path: str,
    filename: str,
    vector_service: VectorService
) -> None:
    """
    Process a single document and add to vector store.
    
    Args:
        file_path: Path to the document file
        filename: Original filename
        vector_service: Vector service instance
        
    Raises:
        VectorStoreException: If processing fails
    """
    try:
        # For now, only handle PDF files (matching existing pipeline)
        if not filename.lower().endswith('.pdf'):
            raise VectorStoreException(f"Unsupported file type for processing: {filename}", "process")
        
        # Create temporary directory with the file
        temp_dir = Path(file_path).parent
        
        # Process using existing ingestion logic
        document_count = await vector_service.ingest_documents_from_directory(
            directory_path=str(temp_dir),
            file_extensions=[".pdf"]
        )
        
        logger.info("✅ Processed document: %s (%d chunks)", filename, document_count)
        
    except Exception as e:
        logger.error("❌ Failed to process document %s: %s", filename, str(e))
        raise VectorStoreException(f"Document processing failed: {str(e)}", "process")
