# [HTTP] /api/ai-chat — session เก็บใน memory ของ service (หายเมื่อ restart)
from fastapi import APIRouter, HTTPException

from app.ai_chat import service as ai_chat_service
from app.ai_chat.schemas import Question
from app.errors import AppError

router = APIRouter(tags=["AI Chat"])

@router.post("/ai-chat/ask")
async def ask_question(q: Question):
    try:
        return await ai_chat_service.process_chat_request(q)
    except AppError:
        raise  # ให้ handler กลางตอบ status เดิม (เช่น 400 คำถามว่าง)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-chat/history/{session_id}")
async def get_history(session_id: str = "default"):
    history = ai_chat_service.get_or_create_session(session_id)
    return {
        "session_id": session_id,
        "history": history,
        "count": len(history)
    }

@router.post("/ai-chat/clear-history/{session_id}")
async def clear_history(session_id: str = "default"):
    if session_id in ai_chat_service.conversation_sessions:
        del ai_chat_service.conversation_sessions[session_id]
    return {"message": "ล้างประวัติการสนทนาเรียบร้อย", "session_id": session_id}

@router.get("/ai-chat/sessions")
async def list_sessions():
    return {
        "sessions": list(ai_chat_service.conversation_sessions.keys()),
        "count": len(ai_chat_service.conversation_sessions)
    }

@router.get("/ai-chat")
async def root():
    return {
        "message": "Bangkok Zoning RAG API with Session-based History",
        "endpoints": {
            "/api/ai-chat/ask": "POST - Ask questions (provide session_id in body)",
            "/api/ai-chat/history/{session_id}": "GET - View conversation history for a session",
            "/api/ai-chat/clear-history/{session_id}": "POST - Clear conversation history for a session",
            "/api/ai-chat/sessions": "GET - List all active sessions",
            "/docs": "GET - API documentation"
        },
        "note": "History is stored in memory and will be lost on server restart"
    }