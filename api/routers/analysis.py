"""
Analysis router for LumiLens API.

Provides endpoints for document analysis, legal insights extraction,
and specialized legal document processing capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from api.config import Settings, get_settings
from api.core.exceptions import ValidationException, VectorStoreException
from api.services.vector_service import VectorService

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisRequest(BaseModel):
    """Document analysis request model."""
    text: str = Field(..., min_length=10, max_length=50000, description="Text to analyze")
    analysis_types: List[str] = Field(
        default=["entities", "summary", "key_points"],
        description="Types of analysis to perform"
    )
    jurisdiction: Optional[str] = Field(default=None, description="Legal jurisdiction for context")
    document_type: Optional[str] = Field(default=None, description="Type of legal document")


class EntityExtraction(BaseModel):
    """Extracted entity model."""
    text: str = Field(..., description="Entity text")
    label: str = Field(..., description="Entity type/label")
    confidence: float = Field(..., description="Confidence score")
    start_pos: int = Field(..., description="Start position in text")
    end_pos: int = Field(..., description="End position in text")


class KeyPoint(BaseModel):
    """Key point extraction model."""
    point: str = Field(..., description="Key point text")
    importance: float = Field(..., description="Importance score")
    category: str = Field(..., description="Point category")
    source_text: str = Field(..., description="Source text excerpt")


class AnalysisResult(BaseModel):
    """Document analysis result model."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    summary: Optional[str] = Field(default=None, description="Document summary")
    entities: List[EntityExtraction] = Field(default_factory=list, description="Extracted entities")
    key_points: List[KeyPoint] = Field(default_factory=list, description="Key points")
    document_type: Optional[str] = Field(default=None, description="Detected document type")
    confidence_score: float = Field(..., description="Overall analysis confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class SimilarDocumentsRequest(BaseModel):
    """Similar documents search request."""
    text: str = Field(..., min_length=10, max_length=10000, description="Text to find similar documents for")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")


class SimilarDocument(BaseModel):
    """Similar document result model."""
    document_id: str = Field(..., description="Document identifier")
    similarity_score: float = Field(..., description="Similarity score")
    excerpt: str = Field(..., description="Relevant text excerpt")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    source_info: Optional[str] = Field(default=None, description="Source document information")


class SimilarDocumentsResponse(BaseModel):
    """Similar documents search response."""
    query: str = Field(..., description="Original query text")
    results: List[SimilarDocument] = Field(..., description="Similar documents found")
    total_results: int = Field(..., description="Total number of results")
    processing_time: float = Field(..., description="Search processing time")
    timestamp: datetime = Field(default_factory=datetime.now)


@router.post("/analysis/analyze", response_model=AnalysisResult)
async def analyze_document(
    request: AnalysisRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Perform comprehensive analysis of legal document text.
    
    This endpoint provides detailed analysis including entity extraction,
    summarization, key point identification, and document classification.
    
    Args:
        request: Analysis request with text and parameters
        settings: Application settings dependency
        
    Returns:
        AnalysisResult: Comprehensive analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        import time
        import uuid
        
        start_time = time.time()
        analysis_id = str(uuid.uuid4())
        
        logger.info("🔍 Starting document analysis (ID: %s)", analysis_id)
        
        # Initialize analysis result
        result = AnalysisResult(
            analysis_id=analysis_id,
            confidence_score=0.0,
            processing_time=0.0
        )
        
        # Perform requested analyses
        if "summary" in request.analysis_types:
            result.summary = await _generate_summary(request.text, settings)
        
        if "entities" in request.analysis_types:
            result.entities = await _extract_entities(request.text)
        
        if "key_points" in request.analysis_types:
            result.key_points = await _extract_key_points(request.text)
        
        if "document_type" in request.analysis_types:
            result.document_type = await _classify_document_type(request.text)
        
        # Calculate processing time and confidence
        result.processing_time = time.time() - start_time
        result.confidence_score = _calculate_confidence_score(result)
        
        # Add metadata
        result.metadata = {
            "text_length": len(request.text),
            "analysis_types": request.analysis_types,
            "jurisdiction": request.jurisdiction,
            "requested_document_type": request.document_type
        }
        
        logger.info("✅ Analysis completed (ID: %s, Time: %.2fs)", analysis_id, result.processing_time)
        
        return result
        
    except Exception as e:
        logger.error("❌ Document analysis failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analysis/similar", response_model=SimilarDocumentsResponse)
async def find_similar_documents(
    request: SimilarDocumentsRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Find documents similar to the provided text.
    
    Uses vector similarity search to find legally relevant documents
    that are similar to the input text.
    
    Args:
        request: Similar documents search request
        settings: Application settings dependency
        
    Returns:
        SimilarDocumentsResponse: Similar documents with scores
        
    Raises:
        HTTPException: If search fails
    """
    try:
        import time
        
        start_time = time.time()
        logger.info("🔍 Searching for similar documents")
        
        # Perform similarity search
        vector_service = VectorService()
        
        # Use similarity search with scores
        results_with_scores = await vector_service.similarity_search_with_scores(
            query=request.text,
            k=request.max_results,
            filter_metadata=request.filters
        )
        
        # Process results
        similar_docs = []
        for doc, score in results_with_scores:
            # Filter by similarity threshold
            if score >= request.similarity_threshold:
                similar_docs.append(SimilarDocument(
                    document_id=doc.metadata.get("id", "unknown"),
                    similarity_score=float(score),
                    excerpt=doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    metadata=doc.metadata,
                    source_info=doc.metadata.get("source", None)
                ))
        
        processing_time = time.time() - start_time
        
        logger.info("✅ Found %d similar documents (Time: %.2fs)", len(similar_docs), processing_time)
        
        return SimilarDocumentsResponse(
            query=request.text,
            results=similar_docs,
            total_results=len(similar_docs),
            processing_time=processing_time
        )
        
    except VectorStoreException as e:
        logger.error("❌ Similar documents search failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    except Exception as e:
        logger.error("❌ Unexpected error in similar documents search: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/generate/brief")
async def generate_brief(case_data: dict = Body(...), settings: Settings = Depends(get_settings)):
    """
    Generate a legal brief from provided case data.
    """
    # TODO: Implement actual brief generation logic
    return {"brief": "This is a generated legal brief.", "case_data": case_data}

@router.get("/analysis/capabilities")
async def get_analysis_capabilities():
    """
    Get available analysis capabilities and supported features.
    
    Returns:
        dict: Available analysis capabilities
    """
    return {
        "analysis_types": [
            {
                "name": "summary",
                "description": "Generate document summary",
                "supported": True
            },
            {
                "name": "entities",
                "description": "Extract legal entities (parties, dates, amounts)",
                "supported": True
            },
            {
                "name": "key_points",
                "description": "Identify key legal points and clauses",
                "supported": True
            },
            {
                "name": "document_type",
                "description": "Classify legal document type",
                "supported": True
            },
            {
                "name": "risk_assessment",
                "description": "Assess legal risks and issues",
                "supported": False,
                "coming_soon": True
            }
        ],
        "supported_document_types": [
            "contract", "agreement", "lease", "employment", "nda",
            "court_filing", "case_law", "statute", "regulation"
        ],
        "supported_jurisdictions": [
            "federal", "california", "new_york", "texas", "florida"
        ],
        "limits": {
            "max_text_length": 50000,
            "max_similarity_results": 20
        }
    }


# Private helper functions

async def _generate_summary(text: str, settings: Settings) -> str:
    """
    Generate document summary using AI.
    
    Args:
        text: Text to summarize
        settings: Application settings
        
    Returns:
        str: Generated summary
    """
    try:
        # TODO: Implement actual AI summarization
        # This is a placeholder implementation
        
        # For now, return a simple summary based on text analysis
        sentences = text.split('.')
        key_sentences = sentences[:3]  # Take first 3 sentences as summary
        
        summary = '. '.join(key_sentences).strip()
        if summary and not summary.endswith('.'):
            summary += '.'
            
        return summary or "Summary not available for this document."
        
    except Exception as e:
        logger.warning("⚠️ Summary generation failed: %s", str(e))
        return "Summary generation failed."


async def _extract_entities(text: str) -> List[EntityExtraction]:
    """
    Extract legal entities from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List[EntityExtraction]: Extracted entities
    """
    try:
        # TODO: Implement actual NER (Named Entity Recognition)
        # This is a placeholder implementation
        
        entities = []
        
        # Simple pattern matching for demonstration
        import re
        
        # Date patterns
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.finditer(date_pattern, text)
        for match in dates:
            entities.append(EntityExtraction(
                text=match.group(),
                label="DATE",
                confidence=0.8,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Currency amounts
        currency_pattern = r'\$[\d,]+\.?\d*'
        amounts = re.finditer(currency_pattern, text)
        for match in amounts:
            entities.append(EntityExtraction(
                text=match.group(),
                label="MONEY",
                confidence=0.9,
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        return entities
        
    except Exception as e:
        logger.warning("⚠️ Entity extraction failed: %s", str(e))
        return []


async def _extract_key_points(text: str) -> List[KeyPoint]:
    """
    Extract key legal points from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List[KeyPoint]: Key points identified
    """
    try:
        # TODO: Implement actual key point extraction
        # This is a placeholder implementation
        
        key_points = []
        
        # Simple sentence-based extraction
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        # Look for sentences with legal keywords
        legal_keywords = ['shall', 'liability', 'breach', 'termination', 'payment', 'obligation']
        
        for i, sentence in enumerate(sentences[:10]):  # Limit to first 10 sentences
            if any(keyword in sentence.lower() for keyword in legal_keywords):
                key_points.append(KeyPoint(
                    point=sentence,
                    importance=0.7,
                    category="legal_provision",
                    source_text=sentence
                ))
        
        return key_points
        
    except Exception as e:
        logger.warning("⚠️ Key points extraction failed: %s", str(e))
        return []


async def _classify_document_type(text: str) -> str:
    """
    Classify the type of legal document.
    
    Args:
        text: Text to classify
        
    Returns:
        str: Document type classification
    """
    try:
        # TODO: Implement actual document classification
        # This is a placeholder implementation
        
        text_lower = text.lower()
        
        # Simple keyword-based classification
        if 'lease' in text_lower or 'tenant' in text_lower or 'landlord' in text_lower:
            return 'lease_agreement'
        elif 'employment' in text_lower or 'employee' in text_lower or 'employer' in text_lower:
            return 'employment_agreement'
        elif 'confidential' in text_lower or 'non-disclosure' in text_lower:
            return 'nda'
        elif 'contract' in text_lower or 'agreement' in text_lower:
            return 'contract'
        elif 'court' in text_lower or 'plaintiff' in text_lower or 'defendant' in text_lower:
            return 'court_document'
        else:
            return 'legal_document'
            
    except Exception as e:
        logger.warning("⚠️ Document classification failed: %s", str(e))
        return 'unknown'


def _calculate_confidence_score(result: AnalysisResult) -> float:
    """
    Calculate overall confidence score for analysis results.
    
    Args:
        result: Analysis result
        
    Returns:
        float: Confidence score between 0 and 1
    """
    try:
        scores = []
        
        # Factor in entity extraction confidence
        if result.entities:
            entity_scores = [e.confidence for e in result.entities]
            scores.append(sum(entity_scores) / len(entity_scores))
        
        # Factor in key points extraction
        if result.key_points:
            key_point_scores = [kp.importance for kp in result.key_points]
            scores.append(sum(key_point_scores) / len(key_point_scores))
        
        # Factor in document type classification confidence
        if result.document_type and result.document_type != 'unknown':
            scores.append(0.8)
        
        # Factor in summary availability
        if result.summary and len(result.summary) > 20:
            scores.append(0.7)
        
        return sum(scores) / len(scores) if scores else 0.5
        
    except Exception:
        return 0.5
