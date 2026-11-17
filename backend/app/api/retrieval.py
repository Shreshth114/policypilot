"""
Retrieval & Evaluation Endpoints for PolicyPilot.
Provides standalone search endpoint and evaluation benchmark suite.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import SearchRequest, SearchResponse, EvaluationResult
from app.services.search import unified_retrieval
from app.services.evaluation import run_retrieval_evaluation

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
def search_policies(req: SearchRequest, db: Session = Depends(get_db)):
    """
    Direct retrieval endpoint allowing users to compare semantic, keyword,
    and hybrid retrieval with/without HyDE.
    """
    res = unified_retrieval(query=req.query, mode=req.mode, db=db, top_k=req.top_k)
    return SearchResponse(
        query=res["query"],
        mode=res["mode"],
        results=res["results"],
        hyde_passage=res.get("hyde_passage"),
        latency_ms=res["latency_ms"]
    )

@router.post("/evaluate", response_model=EvaluationResult)
def evaluate_retrieval(db: Session = Depends(get_db)):
    """
    Executes the retrieval evaluation benchmark comparing:
    - Semantic
    - Semantic + HyDE
    - Keyword
    - Hybrid
    - Hybrid + HyDE
    Calculates Recall@3, Recall@5, MRR, and Latency.
    """
    eval_data = run_retrieval_evaluation(db=db)
    return EvaluationResult(**eval_data)
