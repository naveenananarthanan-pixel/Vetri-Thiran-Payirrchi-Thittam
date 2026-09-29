"""Gemini integration: turns user inputs into a full legal document."""
from config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiGenerationError(RuntimeError):
    """The Gemini call failed (network, quota, blocked content, empty answer...)."""


class GeminiConfigError(GeminiGenerationError):
    """Setup problem: missing API key or missing SDK."""


SYSTEM_INSTRUCTION = (
    "You are a meticulous legal drafting assistant. You write complete, professionally "
    "structured legal documents in formal English. Use clear numbered sections, defined "
    "terms, and standard clauses appropriate to the document type (recitals, definitions, "
    "obligations, term and termination, confidentiality, governing law, dispute resolution, "
    "severability, entire agreement, and a signature block). Where information was not "
    "supplied, insert a clearly marked placeholder in square brackets such as "
    "[Party Address]. Never invent facts. Output only the document text, starting with the "
    "document title. Do not add commentary, disclaimers or markdown code fences."
)


class GeminiDocumentGenerator:
    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self.model_name = model_name or GEMINI_MODEL
        self.api_key = api_key or GEMINI_API_KEY
        self._backend = None      # "genai" (new SDK) or "legacy" (google-generativeai)
        self._client = None
        self._legacy_model = None

    # ---- lazy setup so the API server can start even before a key is configured
    def _ensure_ready(self):
        if self._backend:
            return
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise GeminiConfigError(
                "GEMINI_API_KEY is not set. Add your key to the .env file and restart the backend."
            )
        try:
            from google import genai  # current SDK: pip install google-genai

            self._client = genai.Client(api_key=self.api_key)
            self._backend = "genai"
        except ImportError:
            try:
                import google.generativeai as legacy  # older SDK from the project docs

                legacy.configure(api_key=self.api_key)
                self._legacy_model = legacy.GenerativeModel(
                    self.model_name, system_instruction=SYSTEM_INSTRUCTION
                )
                self._backend = "legacy"
            except ImportError as exc:
                raise GeminiConfigError(
                    "No Gemini SDK installed. Run: pip install google-genai"
                ) from exc

    @staticmethod
    def build_prompt(document_type: str, parties: str, terms: str, dates: str) -> str:
        term_lines = [t.strip() for t in terms.split(";") if t.strip()]
        terms_block = "\n".join(f"- {t}" for t in term_lines) if term_lines else "- (none supplied)"
        return (
            f"Generate a comprehensive legal document titled '{document_type}'.\n\n"
            f"Involved parties:\n{parties}\n\n"
            f"Effective date: {dates or '[Effective Date]'}\n\n"
            f"Terms and conditions that MUST be reflected as specific clauses:\n{terms_block}\n\n"
            "Ensure a formal legal structure with multiple numbered sections and legal clauses, "
            "and finish with an execution / signature block for every party."
        )

    def generate_document(self, document_type, parties, terms, dates) -> str:
        self._ensure_ready()
        prompt = self.build_prompt(document_type, parties, terms, dates)
        try:
            if self._backend == "genai":
                from google.genai import types

                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION, temperature=0.3
                    ),
                )
            else:
                response = self._legacy_model.generate_content(prompt)
            text = (response.text or "").strip()
        except GeminiGenerationError:
            raise
        except Exception as exc:  # SDK errors: quota, auth, network, safety block...
            raise GeminiGenerationError(f"Gemini request failed: {exc}") from exc

        if not text:
            raise GeminiGenerationError("Gemini returned an empty response. Try rephrasing your input.")
        return text
