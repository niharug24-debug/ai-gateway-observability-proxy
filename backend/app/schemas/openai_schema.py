"""
OpenAI-Compatible Chat Completion Pydantic Schemas.
Enables 100% transparent interception of standard LLM provider requests.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message author (system, user, assistant, function, tool)")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="The contents of the message")
    name: Optional[str] = Field(None, description="An optional name for the participant")


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="ID of the model to use (e.g. gpt-4o, gpt-4o-mini, gemini-1.5-flash)")
    messages: List[ChatMessage] = Field(..., description="A list of messages comprising the conversation so far")
    temperature: Optional[float] = Field(1.0, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling probability")
    n: Optional[int] = Field(1, description="How many chat completion choices to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream back partial progress chunks")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    user: Optional[str] = Field(None, description="A unique identifier representing your end-user")


class UsageInfo(BaseModel):
    prompt_tokens: int = Field(0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(0, description="Number of tokens in the generated completion")
    total_tokens: int = Field(0, description="Total number of tokens used in the request")


class ChatCompletionMessage(BaseModel):
    role: str = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatCompletionMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo
    system_fingerprint: Optional[str] = "fp_gateway_cache_v1"
