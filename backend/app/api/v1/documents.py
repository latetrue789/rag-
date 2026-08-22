import asyncio

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import ContainerDependency
from app.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentScanStatusResponse,
    DocumentScanSummaryResponse,
)
from app.services.documents import (
    DocumentNotFoundError,
    DocumentSourcePresentError,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(container: ContainerDependency) -> DocumentListResponse:
    documents = container.document_service.list_documents()
    items = [
        DocumentResponse.model_validate(document, from_attributes=True)
        for document in documents
    ]
    return DocumentListResponse(items=items, total=len(items))


@router.get("/scan", response_model=DocumentScanStatusResponse)
def get_scan_status(container: ContainerDependency) -> DocumentScanStatusResponse:
    sync = container.folder_sync
    last_scan = (
        DocumentScanSummaryResponse(**sync.last_result.to_dict())
        if sync.last_result is not None
        else None
    )
    return DocumentScanStatusResponse(
        directory="data/documents/",
        subdirectories=["md/", "txt/", "pdf/"],
        interval_seconds=container.settings.document_scan_interval_seconds,
        scanning=sync.is_scanning,
        last_scan=last_scan,
    )


@router.post("/scan", response_model=DocumentScanSummaryResponse)
async def scan_documents(
    container: ContainerDependency,
) -> DocumentScanSummaryResponse:
    result = await asyncio.to_thread(container.folder_sync.scan)
    return DocumentScanSummaryResponse(**result.to_dict())


@router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document(
    document_id: str,
    container: ContainerDependency,
) -> DocumentResponse:
    try:
        document = await asyncio.to_thread(container.folder_sync.retry, document_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=409, detail="源文件不存在，请先放回资料目录") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return DocumentResponse.model_validate(document, from_attributes=True)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, container: ContainerDependency) -> Response:
    try:
        container.document_service.delete_document(document_id)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
    except DocumentSourcePresentError as error:
        raise HTTPException(
            status_code=409,
            detail="请先从 data/documents/ 移除源文件，再确认清除知识库记录",
        ) from error
    except Exception as error:
        raise HTTPException(status_code=503, detail="删除向量失败，文档未删除") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
