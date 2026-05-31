"""
LangChain model provider
=========================
get_chat_model() returns a LangChain chat model:

  • If HF_API_TOKEN is set -> a real HuggingFace chat model (works for ANY topic).
  • Otherwise              -> DemoChatModel, an offline LangChain BaseChatModel
                              that serves curated content so the SAME LangChain
                              pipeline runs with zero setup.

Either way the rest of the app builds identical LCEL chains
(prompt | model | parser) — only the model swaps.
"""

import os
import re
import json
from typing import Any, List, Optional

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

import content_bank

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")


# ── Offline demo model (still a real LangChain model) ─────────────────────────
_MARK = re.compile(r"<<(\w+):([^>]*)>>")


class DemoChatModel(BaseChatModel):
    """A LangChain chat model that answers from the offline content bank.

    It reads structured markers embedded in the prompt — <<TASK:...>>,
    <<TOPIC:...>>, <<LEVEL:...>>, <<DIFFICULTY:...>>, <<N:...>> — and returns
    either an explanation (plain text) or a quiz (JSON matching the Quiz schema).
    A real LLM ignores the markers and follows the natural-language instructions.
    """

    @property
    def _llm_type(self) -> str:
        return "demo-offline"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = "\n".join(m.content for m in messages if isinstance(m.content, str))
        marks = {k.upper(): v.strip() for k, v in _MARK.findall(prompt)}
        task = marks.get("TASK", "explain")

        if task == "quiz":
            text = self._make_quiz_json(
                topic=marks.get("TOPIC", "this topic"),
                difficulty=marks.get("DIFFICULTY", "easy"),
                n=int(marks.get("N", "3") or 3),
            )
        else:
            text = content_bank.get_explanation(
                marks.get("TOPIC", "this topic"),
                marks.get("LEVEL", "beginner"),
            )

        msg = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @staticmethod
    def _make_quiz_json(topic: str, difficulty: str, n: int) -> str:
        questions = content_bank.get_questions(topic, difficulty, n)
        return json.dumps(
            {"topic": topic, "difficulty": difficulty, "questions": questions}
        )


# ── Factory ───────────────────────────────────────────────────────────────────
def get_chat_model():
    """Return a real HF chat model if a token is set, else the offline demo model."""
    if HF_API_TOKEN:
        # Real LLM path (any topic). Imported lazily so offline runs need no extras.
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

        endpoint = HuggingFaceEndpoint(
            repo_id=HF_MODEL,
            huggingfacehub_api_token=HF_API_TOKEN,
            task="text-generation",
            max_new_tokens=2000,
            temperature=0.5,
        )
        return ChatHuggingFace(llm=endpoint)

    return DemoChatModel()


def using_real_llm() -> bool:
    return bool(HF_API_TOKEN)
