"""
InsightFlow AI — Chat API Route

Endpoint: POST /api/chat
Connects: Streamlit → FastAPI → Nemotron Service → OpenRouter → NVIDIA Nemotron 3 Ultra

Sub-Phase 6.5: Dataset-aware context injection (rich CSV sample + column stats).
Sub-Phase 6.6: Multi-turn conversation history with token-safe trimming.

How history works:
  - The system prompt (with full dataset context) is always injected ONCE as the
    first message. It is NOT duplicated on every turn.
  - The history (previous user+assistant turns) is appended after the system prompt.
  - To avoid hitting token limits on long conversations, history is trimmed to the
    last MAX_HISTORY_TURNS pairs (user+assistant = 1 pair).
  - The current user message is appended last.

Message structure sent to Nemotron:
  [system: InsightFlow prompt + dataset context (once)]
  [user: turn 1]
  [assistant: turn 1 reply]
  [user: turn 2]
  [assistant: turn 2 reply]
  ...
  [user: CURRENT question]
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.nemotron_service import generate_response, SYSTEM_PROMPT
from backend.services import rag_service as rs

router = APIRouter()

# Maximum number of past conversation turns to keep in context.
# 1 turn = 1 user message + 1 assistant reply.
# Keep this low to avoid token limit errors on free tier.
MAX_HISTORY_TURNS = 6


# ── Request / Response Schemas ────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str    # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """
    Request body for POST /api/chat.

    Fields:
    - message:         The current user question.
    - filename:        The uploaded CSV filename (basename). Backend loads the
                       actual dataset and injects rich context into the system prompt.
    - dataset_context: Fallback metadata string (used when filename is not given).
    - history:         All previous messages in the conversation (full list).
                       Backend trims to the last MAX_HISTORY_TURNS pairs automatically.
    """
    message: str
    filename: str = ""
    dataset_context: str = ""
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    """Response body from POST /api/chat."""
    response: str
    model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    context_type: str = "none"    # "rich" | "metadata" | "none"
    history_turns: int = 0        # how many past turns were included


# ── Helpers ───────────────────────────────────────────────────────────────────

def _trim_history(history: list[ChatMessage], max_turns: int) -> list[dict]:
    """
    Convert history to dicts and trim to the last `max_turns` pairs.

    A "pair" is one user message + one assistant reply (= 2 messages).
    We always keep complete pairs so the AI doesn't see a dangling user message.

    Args:
        history: List of ChatMessage objects (alternating user/assistant).
        max_turns: Maximum number of complete pairs to keep.

    Returns:
        List of dicts [{"role": ..., "content": ...}] trimmed to max_turns pairs.
    """
    msgs = [{"role": m.role, "content": m.content} for m in history]

    # Keep only the last (max_turns * 2) messages (pairs of user+assistant)
    max_msgs = max_turns * 2
    if len(msgs) > max_msgs:
        msgs = msgs[-max_msgs:]

    return msgs


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Chat with InsightFlow AI Assistant",
    description="""
    Send a message to NVIDIA Nemotron 3 Ultra via OpenRouter.

    **Dataset-aware (Sub-Phase 6.5):** Provide `filename` to inject real data context —
    column stats, top categories, and up to 500 actual CSV rows into the system prompt.

    **Multi-turn (Sub-Phase 6.6):** Provide `history` (all previous messages) for
    follow-up questions. The backend trims to the last 6 conversation turns automatically
    to stay within token limits.

    Examples of what the AI can answer:
    - "What is the highest profitable action movie?" → reads actual rows
    - "What about its budget?" → uses history to understand "it"
    - "Compare that to the top comedy movie" → cross-turn reference
    """,
    tags=["Agentic AI"],
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint — routes user messages to NVIDIA Nemotron 3 Ultra
    with dataset context and multi-turn history.
    """
    try:
        # ── 1. Build dataset context (Metadata + RAG) ──
        context_block = ""
        context_type = "none"

        # Always inject the dataset schema and summary first
        if request.dataset_context:
            context_block += "=== DATASET SCHEMA & OVERVIEW ===\n"
            context_block += request.dataset_context + "\n\n"
            context_type = "metadata"

        # Then inject the RAG semantic retrieval rows
        if request.filename:
            rag_context = rs.query_dataset(request.filename, request.message)
            if rag_context:
                context_block += "=== SEMANTIC RAG RETRIEVAL (Relevant Rows) ===\n"
                context_block += rag_context + "\n"
                context_type = "rag_retrieval"

        # ── 2. System prompt — injected ONCE at the top, not repeated per turn ──
        system_content = SYSTEM_PROMPT
        if context_block:
            system_content += f"\n\n{context_block}"

        # Add multi-turn instruction to system prompt
        system_content += (
            "\n\nIMPORTANT: You are in a multi-turn conversation. "
            "Use the conversation history above to understand references like "
            "'that movie', 'it', 'those columns', 'the previous result', etc. "
            "Always maintain context across turns."
        )

        # ── 3. Build message chain ────────────────────────────────────────────
        messages = [{"role": "system", "content": system_content}]

        # Trim history to last MAX_HISTORY_TURNS pairs (token-safe)
        trimmed_history = _trim_history(request.history, MAX_HISTORY_TURNS)
        messages.extend(trimmed_history)

        # Append current user question with a strict format reminder
        strict_reminder = "\n\n(Respond directly with the final answer only. Do not output your internal thought process or reasoning.)"
        messages.append({"role": "user", "content": request.message + strict_reminder})

        # ── 4. Call Nemotron ──────────────────────────────────────────────────
        answer = generate_response(messages)

        return ChatResponse(
            response=answer,
            context_type=context_type,
            history_turns=len(trimmed_history) // 2,
        )

    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(e)}"
        )
