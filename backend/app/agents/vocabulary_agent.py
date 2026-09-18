import logging
from typing import Any

import truststore

from app.schemas.chat import ChatResponse
from app.tools.vocabulary_agent_tools import VocabularyAgentTools

logger = logging.getLogger(__name__)


class VocabularyAgentError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class VocabularyAgentRunner:
    def __init__(self, api_key: str, model: str, temperature: float = 0.3):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def run(
        self,
        message: str,
        request_id: str,
        tools: VocabularyAgentTools,
        collection_id: str | None = None,
    ) -> ChatResponse:
        if not self.api_key:
            raise VocabularyAgentError(
                "GROQ_NOT_CONFIGURED",
                "Groq is not configured.",
                503,
            )

        truststore.inject_into_ssl()
        try:
            from crewai import Agent, Crew, LLM, Task
            from langchain.tools import StructuredTool
        except (ImportError, ModuleNotFoundError) as exc:
            raise VocabularyAgentError(
                "AGENT_RUNTIME_UNAVAILABLE",
                "The CrewAI runtime is not installed for this Python environment.",
                503,
            ) from exc

        agent_tools = [
            StructuredTool.from_function(tools.list_collections),
            StructuredTool.from_function(tools.get_collection),
            StructuredTool.from_function(tools.explain_term),
            StructuredTool.from_function(tools.save_vocabulary),
            StructuredTool.from_function(tools.search_notion_pages),
            StructuredTool.from_function(tools.append_to_collection_notion),
            StructuredTool.from_function(tools.create_notion_page),
            StructuredTool.from_function(tools.link_collection_to_notion),
            StructuredTool.from_function(tools.create_collection),
        ]
        llm = LLM(
            model=f"groq/{self.model}",
            api_key=self.api_key,
            temperature=self.temperature,
            timeout=30,
            max_tokens=1200,
        )
        agent = Agent(
            role="Vocabulary and Knowledge Assistant",
            goal="Understand reading-related requests and use only the supplied tools to complete them.",
            backstory=(
                "You are LexiShelf's concise reading assistant. Never claim a save, creation, or "
                "Notion update unless the corresponding tool returned success. Never attempt deletion, "
                "page replacement, code execution, or delegation. Ask for clarification when a target "
                "collection is ambiguous."
            ),
            tools=agent_tools,
            llm=llm,
            function_calling_llm=llm,
            allow_delegation=False,
            allow_code_execution=False,
            max_iter=6,
            max_execution_time=45,
            max_retry_limit=1,
            verbose=False,
        )
        collection_context = collection_id or "No collection was selected by the client."
        task = Task(
            description=(
                "Handle this authenticated user's request: {message}\n"
                "Client-selected collection ID: {collection_id}\n"
                "Use tools for all external or persistent actions. A selected collection ID is context, "
                "not proof of ownership; tools enforce ownership. Keep the final answer concise and state "
                "failed actions accurately. When saving vocabulary, always include part of speech, "
                "pronunciation, source sentence, example, synonyms, and usage note, and also include the "
                "explanation text (meaning, simple_explanation, contextual_explanation) and difficulty_level "
                "so the user can see the exact explanation again later."
                " The save_vocabulary tool automatically appends to Notion when its collection is linked. "
                "Use link_collection_to_notion after finding or creating the page that should back a collection."
            ),
            expected_output="A concise user-facing answer grounded in actual tool results.",
            agent=agent,
            tools=agent_tools,
        )
        crew = Crew(
            agents=[agent],
            tasks=[task],
            memory=False,
            cache=False,
            verbose=False,
            max_rpm=20,
        )

        try:
            output: Any = crew.kickoff(
                inputs={"message": message, "collection_id": collection_context}
            )
        except Exception as exc:
            logger.exception(
                "Vocabulary agent execution failed",
                extra={"request_id": request_id, "error_type": type(exc).__name__},
            )
            raise VocabularyAgentError(
                "AGENT_EXECUTION_FAILED",
                "The assistant could not complete this request.",
            ) from exc

        response_message = getattr(output, "raw", None) or str(output)
        if not response_message.strip():
            raise VocabularyAgentError(
                "AGENT_EMPTY_RESPONSE",
                "The assistant returned an empty response.",
            )
        return ChatResponse(
            message=response_message.strip(),
            actions=tools.actions,
            request_id=request_id,
        )