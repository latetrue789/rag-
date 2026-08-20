from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import ContainerDependency
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.services.documents import DocumentNotFoundError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(container: ContainerDependency) -> DocumentListResponse:
    documents = container.document_service.list_documents()
    items = [
        DocumentResponse.model_validate(document, from_attributes=True)
        for document in documents
    ]
    return DocumentListResponse(items=items, total=len(items))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, container: ContainerDependency) -> Response:
    try:
        container.document_service.delete_document(document_id)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail="文档不存在") from error
    except Exception as error:
        raise HTTPException(status_code=503, detail="删除向量失败，文档未删除") from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
