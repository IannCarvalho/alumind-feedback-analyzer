import json
import logging
from typing import List

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.config import Config

logger = logging.getLogger(__name__)

VALID_SENTIMENTS = {"POSITIVO", "NEGATIVO", "INCONCLUSIVO"}
DEFAULT_SENTIMENT = "INCONCLUSIVO"


class RequestedFeatureModel(BaseModel):
    """One feature requested by the user, as parsed from the LLM output."""

    code: str
    reason: str = ""


class FeedbackAnalysis(BaseModel):
    """Validated shape of the LLM analysis.

    Pydantic normalises the payload: an unknown or missing sentiment becomes
    INCONCLUSIVO, is_spam defaults to False and malformed features are dropped
    rather than blowing up the request.
    """

    sentiment: str = DEFAULT_SENTIMENT
    is_spam: bool = False
    requested_features: List[RequestedFeatureModel] = Field(default_factory=list)

    @field_validator("sentiment", mode="before")
    @classmethod
    def _normalise_sentiment(cls, value: object) -> str:
        if not isinstance(value, str):
            return DEFAULT_SENTIMENT
        upper = value.strip().upper()
        return upper if upper in VALID_SENTIMENTS else DEFAULT_SENTIMENT


def _default_result() -> dict:
    """Canonical safe result used whenever analysis cannot be trusted."""
    return {
        "sentiment": DEFAULT_SENTIMENT,
        "is_spam": False,
        "requested_features": [],
    }


class FeedbackAnalyzer:
    """Service for analyzing feedback using LLM"""

    def __init__(self):
        """Initialize the feedback analyzer"""
        api_key = Config.OPENAI_API_KEY
        model_name = Config.OPENAI_MODEL

        if not api_key:
            raise ValueError("OpenAI API Key not configured")

        # Ask the model to return a JSON object directly. This removes most of
        # the "find the braces in free-form prose" guesswork; the embedded-JSON
        # fallback below still covers models that ignore the hint.
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=0.0,
            openai_api_key=api_key,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

    def analyze_feedback(self, feedback_text):
        """
        Analyzes feedback to determine sentiment and extract requested features

        Args:
            feedback_text (str): Feedback text

        Returns:
            dict: Dictionary with sentiment, is_spam and requested features
        """
        prompt = ChatPromptTemplate.from_template("""
        Você é um assistente especializado em analisar feedbacks de usuários de um
        aplicativo. Seu objetivo é classificar o sentimento do feedback, detectar spam
        e identificar funcionalidades solicitadas.

        Analise o seguinte feedback e forneça:
        1. Classificação de sentimento: "POSITIVO", "NEGATIVO" ou "INCONCLUSIVO"
        2. Identificação se é spam ou não (feedback é spam se não for relacionado ao aplicativo, contiver links suspeitos, for ofensivo sem ser construtivo ou parecer gerado automaticamente)
        3. Identificação das funcionalidades solicitadas pelo usuário, se houver

        Para cada funcionalidade identificada, forneça:
        - Um código único para a funcionalidade (use letras maiúsculas e sublinhado, como EDITAR_PERFIL)
        - Uma razão explicando por que o usuário quer essa funcionalidade

        Retorne APENAS um objeto JSON com as seguintes chaves:
        - sentiment: string (POSITIVO, NEGATIVO ou INCONCLUSIVO)
        - is_spam: booleano (true/false)
        - requested_features: array de objetos com as chaves 'code' e 'reason'

        Feedback: {feedback}
        """)

        chain = prompt | self.llm
        response = chain.invoke({"feedback": feedback_text})

        raw = self._extract_json(response.content)
        if raw is None:
            logger.error("Could not locate JSON in LLM response")
            return _default_result()

        try:
            analysis = FeedbackAnalysis.model_validate(raw)
        except ValidationError as e:
            logger.error(f"LLM analysis failed schema validation: {e}")
            return _default_result()

        return analysis.model_dump()

    @staticmethod
    def _extract_json(content: str):
        """Parse a JSON object out of the model response.

        With response_format=json_object the whole content is already JSON, so
        the direct parse wins. The brace-slice is kept as a defensive fallback
        for models that wrap the JSON in prose.
        """
        if not content:
            return None

        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass

        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(content[start_idx:end_idx])
            except (json.JSONDecodeError, ValueError):
                return None
        return None
