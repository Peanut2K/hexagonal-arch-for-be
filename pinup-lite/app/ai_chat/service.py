import os
import json
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from app.errors import AppError
from pydantic import BaseModel
from openai import OpenAI
from rapidfuzz import fuzz

from app.ai_chat.tfidf import ThaiTfidf

TYPHOON_API_KEY = os.environ.get("TYPHOON_API_KEY")

client = OpenAI(
    api_key=TYPHOON_API_KEY,
    base_url="https://api.opentyphoon.ai/v1"
)

@dataclass
class Chunk:
    text: str
    page: int
    source: str

# ------------------- In-Memory Session Storage -------------------
conversation_sessions = {}

def get_or_create_session(session_id: str) -> List[dict]:
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = []
    return conversation_sessions[session_id]

def add_to_session(session_id: str, entry: dict):
    history = get_or_create_session(session_id)
    history.append(entry)
    if len(history) > 10:
        conversation_sessions[session_id] = history[-10:]

# ------------------- Base System Prompt -------------------
BASE_SYSTEM_PROMPT = (
    "คุณเป็นผู้ช่วยอัจฉริยะด้านกฎผังเมืองกรุงเทพฯ และการพัฒนาอสังหาริมทรัพย์ "
    "หน้าที่ของคุณคืออธิบายว่าในสถานการณ์หรือพื้นที่นั้น มีกฎอะไรบ้าง ใช้ที่ดินประเภทใดได้ เช่น ย.1, ย.2, ย.3 "
    "รวมถึงเงื่อนไขหรือหมายเหตุที่เกี่ยวข้อง (ถ้าไม่มีให้ใส่เครื่องหมาย - เท่านั้น) "
    "ถ้าไม่พบให้ตอบว่า 'ไม่พบข้อมูลในเอกสาร' พร้อมระบุแหล่งที่มา [หน้า X · ไฟล์]. "
    "นอกจากนี้ ให้สามารถแนะนำแนวทางการใช้ประโยชน์เชิงธุรกิจหรือการต่อยอดที่เหมาะสมกับพื้นที่นั้นได้ "
    "เช่น ประเภทกิจการที่ควรตั้ง, ไอเดียพัฒนาโครงการ, หรือรูปแบบธุรกิจที่สอดคล้องกับข้อจำกัดของผังเมือง "
    "ตอบโดยใช้ภาษาที่เข้าใจง่าย เหมาะกับผู้ใช้งานทั่วไป ใช้สำนวนธรรมชาติและสะกดให้ถูกต้อง. "
    "ตัวอย่างเช่น หากผู้ใช้ถามว่า 'ผมอยากเปิดคาเฟ่ตรงนี้ได้ไหม?' "
    "คุณควรตอบทั้งในมุมของกฎผังเมือง (เช่น พื้นที่ประเภท ย.1 อนุญาตให้เปิดร้านอาหารหรือไม่) "
    "และให้คำแนะนำเชิงธุรกิจต่อยอด เช่น แนวทางการตกแต่ง, การใช้พื้นที่ร่วมกับกิจการอื่น, "
    "หรือแนวคิดทางธุรกิจที่เหมาะสมกับลักษณะพื้นที่นั้น."
)

def ask_typhoon(question: str, context: List[Chunk], additional_context: Optional[str] = None, 
                history: List[dict] = [], temperature: float = 0.2) -> dict:
    
    system_prompt = BASE_SYSTEM_PROMPT
    if additional_context:
        system_prompt = f"{BASE_SYSTEM_PROMPT}\n\n=== ข้อมูลเพิ่มเติมสำคัญ (จากแหล่งข้อมูลภายนอก) ===\n{additional_context}"
    
    if history:
        history_text = "\n".join([
            f"Q: {h['question']}\nA: {h['answer'][:200]}..." 
            for h in history[-3:]
        ])
        system_prompt += f"\n\n=== ประวัติการสนทนาล่าสุด ===\n{history_text}"
    
    ctx = "\n".join([f"【หน้า {c.page} · {c.source}】\n{c.text}" for c in context])
    user_prompt = f"คำถาม: {question}\n\nบริบท:\n{ctx}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = client.chat.completions.create(
        model="typhoon-v2.5-30b-a3b-instruct",
        messages=messages,
        temperature=temperature,
        max_tokens=2048,
        top_p=0.9,
        stream=False
    )
    
    sources = [f"หน้า {c.page} · {c.source}" for c in context]
    
    return {
        "answer": response.choices[0].message.content.strip(),
        "sources": sources
    }

def load_json_chunks(json_path: str) -> List[Chunk]:
    with open(json_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    chunks = []
    for row in rows:
        zones_text = ", ".join([f"{k}: {v}" for k, v in row.get("zones", {}).items() if v])
        text = f"ลำดับ {row.get('id','')} | {row.get('activity','')} | เขตที่ดิน: {zones_text} | หมายเหตุ: {row.get('note','')}"
        chunks.append(
            Chunk(
                text=text,
                page=row.get("page", 0),
                source=Path(json_path).name,
            )
        )
    return chunks

def rag_answer_json(json_path: str, question: str, additional_context: Optional[str] = None, 
                    history: List[dict] = [], top_k: int = 5) -> dict:
    chunks = load_json_chunks(json_path)
    corpus = [c.text for c in chunks]

    retriever = ThaiTfidf().fit(corpus)
    candidate_idx = retriever.search(question, top_k=20)

    scored = []
    for idx in candidate_idx:
        score = fuzz.partial_ratio(question, chunks[idx].text)
        scored.append((score, idx))
    scored.sort(reverse=True)
    hit_idx = [idx for _, idx in scored[:top_k]]

    context = [chunks[i] for i in hit_idx]
    return ask_typhoon(question, context, additional_context, history)

# ------------------- Core API Logic -------------------
async def process_chat_request(q, json_path: str = "data/BKK/bangkok_zoning_cleaned.json"):
    if not q.question or q.question.strip() == "":
        raise AppError("Question cannot be empty")
    history = get_or_create_session(q.session_id)
    
    result = rag_answer_json(
        json_path,
        q.question,
        additional_context=q.additional_context,
        history=history,
        top_k=5
    )
    
    add_to_session(q.session_id, {
        "question": q.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "timestamp": datetime.now().isoformat(),
        "had_additional_context": q.additional_context is not None
    })
    
    return {
        "question": q.question,
        "answer": result["answer"],
        "sources": result["sources"],
        "session_id": q.session_id,
        "conversation_count": len(conversation_sessions[q.session_id]),
        "has_additional_context": q.additional_context is not None
    }