"""
AI Analysis Service

Phase 3: Scoped, schema-validated AI qualitative analysis.

This service provides qualitative insights using Google Gemini LLM.
Each method addresses ONE concern only and returns schema-validated JSON.

Key Constraints:
- AI does NOT assign scores or ratings
- AI does NOT make final judgments
- Output must strictly match defined schemas
- Retry once on schema validation failure
- Return structured error on persistent failure
"""

import json
import asyncio
from pathlib import Path
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.schemas.models import (
    DocumentationQualityResult,
    CodeClarityResult,
    TechStackResult,
    RecruiterFeedbackResult,
    AIAnalysisError,
    CombinedAIInsights,
)


# Type variable for generic schema validation
T = TypeVar("T", bound=BaseModel)


class AIAnalysisService:
    """
    AI-powered qualitative analysis service using Google Gemini.
    
    Each method:
    - Loads a specific prompt template
    - Constructs input payload
    - Invokes LLM with strict JSON output
    - Validates response against Pydantic schema
    - Retries once on validation failure
    - Returns structured error on persistent failure
    """
    
    # Default model configuration
    DEFAULT_MODEL = "gemini-1.5-flash"
    DEFAULT_TEMPERATURE = 0.3  # Low temperature for consistency
    DEFAULT_TIMEOUT = 30  # seconds
    
    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        temperature: float | None = None,
        timeout: int | None = None,
    ):
        """
        Initialize AI Analysis Service.
        
        Args:
            api_key: Google API key for Gemini
            model: Model name (default: gemini-1.5-flash)
            temperature: LLM temperature (default: 0.3)
            timeout: Request timeout in seconds (default: 30)
        """
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=api_key,
            temperature=self.temperature,
            timeout=self.timeout,
        )
        
        # Prompts directory
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
    
    def _load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from file."""
        prompt_path = self.prompts_dir / f"{prompt_name}.prompt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from LLM response.
        
        Handles cases where LLM wraps JSON in markdown code blocks.
        """
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()
    
    def _validate_response(
        self, 
        response_text: str, 
        schema: Type[T]
    ) -> T | AIAnalysisError:
        """
        Parse and validate LLM response against schema.
        
        Returns validated model or error object.
        """
        try:
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
            return schema.model_validate(data)
        except json.JSONDecodeError as e:
            return AIAnalysisError(
                type="SCHEMA_VALIDATION_FAILED",
                message=f"Invalid JSON: {str(e)}"
            )
        except ValidationError as e:
            return AIAnalysisError(
                type="SCHEMA_VALIDATION_FAILED",
                message=f"Schema validation failed: {str(e)}"
            )
    
    async def _invoke_with_retry(
        self,
        system_prompt: str,
        user_input: str,
        schema: Type[T],
    ) -> T | AIAnalysisError:
        """
        Invoke LLM with retry logic.
        
        - First attempt with provided input
        - On schema failure, retry once
        - On timeout or persistent failure, return error
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]
        
        for attempt in range(2):  # Max 2 attempts
            try:
                response = await asyncio.wait_for(
                    self.llm.ainvoke(messages),
                    timeout=self.timeout
                )
                
                # Handle response content - can be str or list for multimodal
                content = response.content
                if isinstance(content, list):
                    # Extract text from list of content parts
                    text_parts = [
                        part if isinstance(part, str) else part.get("text", "")
                        for part in content
                    ]
                    content = "".join(text_parts)
                
                result = self._validate_response(content, schema)
                
                if isinstance(result, AIAnalysisError):
                    if attempt == 0:
                        # Add retry instruction for second attempt
                        messages.append(HumanMessage(
                            content="Your previous response was not valid JSON matching the required schema. "
                                    "Please return ONLY valid JSON with no markdown or explanation."
                        ))
                        continue
                    return result
                
                return result
                
            except asyncio.TimeoutError:
                return AIAnalysisError(
                    type="TIMEOUT",
                    message=f"LLM request timed out after {self.timeout} seconds"
                )
            except Exception as e:
                return AIAnalysisError(
                    type="UNKNOWN",
                    message=f"Unexpected error: {str(e)}"
                )
        
        return AIAnalysisError(
            type="UNKNOWN",
            message="Max retries exceeded"
        )
    
    async def analyze_documentation(
        self,
        repo_name: str,
        owner: str,
        readme: str | None,
    ) -> DocumentationQualityResult | AIAnalysisError:
        """
        Analyze documentation quality.
        
        Prompt: documentation_quality.prompt
        Focus: README clarity and usefulness
        """
        system_prompt = self._load_prompt("documentation_quality")
        
        user_input = json.dumps({
            "repo_name": repo_name,
            "owner": owner,
            "readme": readme,
        }, indent=2)
        
        return await self._invoke_with_retry(
            system_prompt,
            user_input,
            DocumentationQualityResult
        )
    
    async def analyze_code_clarity(
        self,
        repo_name: str,
        languages: dict[str, int],
        files: list[dict],
    ) -> CodeClarityResult | AIAnalysisError:
        """
        Analyze code clarity signals from structure.
        
        Prompt: code_clarity.prompt
        Focus: Folder structure, naming, maintainability signals
        """
        system_prompt = self._load_prompt("code_clarity")
        
        user_input = json.dumps({
            "repo_name": repo_name,
            "languages": languages,
            "files": files,
        }, indent=2)
        
        return await self._invoke_with_retry(
            system_prompt,
            user_input,
            CodeClarityResult
        )
    
    async def analyze_tech_stack(
        self,
        repo_name: str,
        languages: dict[str, int],
        files: list[dict],
        readme: str | None,
    ) -> TechStackResult | AIAnalysisError:
        """
        Explain tech stack usage.
        
        Prompt: tech_stack_analysis.prompt
        Focus: Technologies used and how they work together
        """
        system_prompt = self._load_prompt("tech_stack_analysis")
        
        user_input = json.dumps({
            "repo_name": repo_name,
            "languages": languages,
            "files": files,
            "readme": readme,
        }, indent=2)
        
        return await self._invoke_with_retry(
            system_prompt,
            user_input,
            TechStackResult
        )
    
    async def get_recruiter_feedback(
        self,
        repo_name: str,
        owner: str,
        languages: dict[str, int],
        files: list[dict],
        readme: str | None,
        rule_engine_summary: dict,
    ) -> RecruiterFeedbackResult | AIAnalysisError:
        """
        Get recruiter-style feedback.
        
        Prompt: recruiter_feedback.prompt
        Focus: Professional, constructive hiring perspective
        """
        system_prompt = self._load_prompt("recruiter_feedback")
        
        user_input = json.dumps({
            "repo_name": repo_name,
            "owner": owner,
            "languages": languages,
            "files": files,
            "readme": readme,
            "rule_engine_summary": rule_engine_summary,
        }, indent=2)
        
        return await self._invoke_with_retry(
            system_prompt,
            user_input,
            RecruiterFeedbackResult
        )
    
    async def run_all_analyses(
        self,
        repo_name: str,
        owner: str,
        languages: dict[str, int],
        files: list[dict],
        readme: str | None,
        rule_engine_summary: dict,
    ) -> CombinedAIInsights:
        """
        Run all four AI analyses in parallel.
        
        Returns combined results with any errors captured.
        """
        # Run all analyses concurrently
        results = await asyncio.gather(
            self.analyze_documentation(repo_name, owner, readme),
            self.analyze_code_clarity(repo_name, languages, files),
            self.analyze_tech_stack(repo_name, languages, files, readme),
            self.get_recruiter_feedback(
                repo_name, owner, languages, files, readme, rule_engine_summary
            ),
            return_exceptions=True,
        )
        
        # Process results
        doc_result, code_result, tech_result, recruiter_result = results
        errors: list[AIAnalysisError] = []
        
        # Handle documentation result
        documentation = None
        if isinstance(doc_result, DocumentationQualityResult):
            documentation = doc_result
        elif isinstance(doc_result, AIAnalysisError):
            errors.append(doc_result)
        elif isinstance(doc_result, Exception):
            errors.append(AIAnalysisError(
                type="UNKNOWN",
                message=f"Documentation analysis error: {str(doc_result)}"
            ))
        
        # Handle code clarity result
        code_clarity = None
        if isinstance(code_result, CodeClarityResult):
            code_clarity = code_result
        elif isinstance(code_result, AIAnalysisError):
            errors.append(code_result)
        elif isinstance(code_result, Exception):
            errors.append(AIAnalysisError(
                type="UNKNOWN",
                message=f"Code clarity analysis error: {str(code_result)}"
            ))
        
        # Handle tech stack result
        tech_stack = None
        if isinstance(tech_result, TechStackResult):
            tech_stack = tech_result
        elif isinstance(tech_result, AIAnalysisError):
            errors.append(tech_result)
        elif isinstance(tech_result, Exception):
            errors.append(AIAnalysisError(
                type="UNKNOWN",
                message=f"Tech stack analysis error: {str(tech_result)}"
            ))
        
        # Handle recruiter feedback result
        recruiter_feedback = None
        if isinstance(recruiter_result, RecruiterFeedbackResult):
            recruiter_feedback = recruiter_result
        elif isinstance(recruiter_result, AIAnalysisError):
            errors.append(recruiter_result)
        elif isinstance(recruiter_result, Exception):
            errors.append(AIAnalysisError(
                type="UNKNOWN",
                message=f"Recruiter feedback error: {str(recruiter_result)}"
            ))
        
        return CombinedAIInsights(
            documentation=documentation,
            code_clarity=code_clarity,
            tech_stack=tech_stack,
            recruiter_feedback=recruiter_feedback,
            errors=errors,
        )
