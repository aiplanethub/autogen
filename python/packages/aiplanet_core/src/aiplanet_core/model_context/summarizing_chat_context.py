from typing import List, Optional, Dict, Any, Mapping

from pydantic import BaseModel, Field
from typing_extensions import Self

from autogen_core._component_config import Component
from autogen_core.models import (
    LLMMessage, 
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResultMessage
)
from autogen_core.model_context._chat_completion_context import ChatCompletionContext
from autogen_core._cancellation_token import CancellationToken


class SummarizingChatCompletionContextConfig(BaseModel):
    """Configuration for SummarizingChatCompletionContext."""
    
    recent_capacity: int = Field(
        default=10, 
        description="Maximum number of messages in the recent bucket before moving to old bucket"
    )
    old_capacity: int = Field(
        default=20, 
        description="Maximum number of messages in the old bucket before summarizing"
    )
    summarize_prompt: Optional[str] = Field(
        default=None, 
        description="Custom prompt used for summarization"
    )
    model_client: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for the model client used for summarization"
    )
    initial_messages: Optional[List[LLMMessage]] = Field(
        default=None,
        description="Initial messages to populate the context"
    )


class SummarizingChatCompletionContext(ChatCompletionContext, Component[SummarizingChatCompletionContextConfig]):
    """
    A chat completion context that maintains two buckets of messages:
    - Recent bucket: Contains the most recent messages
    - Old bucket: Contains older messages
    
    When the recent bucket reaches capacity, messages are moved to the old bucket.
    When the old bucket reaches capacity, its contents are summarized and replaced
    with a single summary message.
    
    Args:
        recent_capacity (int): Maximum number of messages in the recent bucket
        old_capacity (int): Maximum number of messages in the old bucket
        summarize_prompt (Optional[str]): Custom prompt for summarization
        model_client (Optional[ChatCompletionClient]): Model client for summarization
        initial_messages (Optional[List[LLMMessage]]): Initial messages
    """
    
    component_config_schema = SummarizingChatCompletionContextConfig
    component_provider_override = "aiplanet_core.model_context.SummarizingChatCompletionContext"
    component_type = "chat_completion_context"
    
    def __init__(
        self,
        recent_capacity: int = 10,
        old_capacity: int = 20,
        summarize_prompt: Optional[str] = None,
        model_client: Optional[ChatCompletionClient] = None,
        initial_messages: Optional[List[LLMMessage]] = None,
    ) -> None:
        super().__init__(initial_messages)
        
        if recent_capacity <= 0:
            raise ValueError("recent_capacity must be greater than 0")
        if old_capacity <= 0:
            raise ValueError("old_capacity must be greater than 0")
            
        self._recent_capacity = recent_capacity
        self._old_capacity = old_capacity
        self._recent_messages: List[LLMMessage] = []
        self._old_messages: List[LLMMessage] = []
        self._model_client = model_client
        
        self._summarize_prompt = summarize_prompt or (
            "Summarize the following conversation concisely, capturing the key points, "
            "decisions, and information shared. Keep any critical details that would be "
            "necessary for understanding the rest of the conversation."
        )
        
        # If we have initial messages, distribute them appropriately
        if self._messages:
            self._distribute_initial_messages()

    def _distribute_initial_messages(self) -> None:
        """Distribute initial messages between recent and old buckets."""
        total_messages = len(self._messages)
        
        if total_messages <= self._recent_capacity:
            # All messages fit in recent bucket
            self._recent_messages = self._messages.copy()
            self._old_messages = []
        else:
            # Split messages between buckets
            self._recent_messages = self._messages[-self._recent_capacity:]
            old_bucket_candidates = self._messages[:-self._recent_capacity]
            
            # If old bucket would exceed capacity, summarize it
            if len(old_bucket_candidates) > self._old_capacity and self._model_client is not None:
                # We'll add placeholder summary for now
                self._old_messages = [
                    SystemMessage(content=f"[Summary of {len(old_bucket_candidates)} previous messages]")
                ]
            else:
                self._old_messages = old_bucket_candidates
        
        # Clear the original messages since we've distributed them
        self._messages = []

    async def add_message(self, message: LLMMessage) -> None:
        """Add a message to the context.
        
        Messages are added to the recent bucket. If the recent bucket is full,
        the oldest messages are moved to the old bucket. If the old bucket would
        exceed capacity, it is summarized first.
        
        Args:
            message (LLMMessage): The message to add
        """
        # Add to internal list for compatibility with parent class
        self._messages.append(message)
        
        # Add to recent message bucket
        self._recent_messages.append(message)
        
        # Check if we need to move messages from recent to old
        if len(self._recent_messages) > self._recent_capacity:
            overflow_count = len(self._recent_messages) - self._recent_capacity
            messages_to_move = self._recent_messages[:overflow_count]
            self._recent_messages = self._recent_messages[overflow_count:]
            
            # Check if adding to old bucket would exceed capacity
            if len(self._old_messages) + len(messages_to_move) > self._old_capacity:
                # If we have a model client, summarize old messages
                if self._model_client is not None:
                    await self._summarize_old_bucket()
                else:
                    # If no model client, just keep the most recent messages in old bucket
                    excess = len(self._old_messages) + len(messages_to_move) - self._old_capacity
                    if excess > 0:
                        self._old_messages = self._old_messages[excess:]
            
            # Add overflow messages to old bucket
            self._old_messages.extend(messages_to_move)

    async def get_messages(self) -> List[LLMMessage]:
        """Get all messages in the context.
        
        Returns:
            List[LLMMessage]: All messages, with old messages first, then recent messages
        """
        # Combine old and recent messages
        return self._old_messages + self._recent_messages

    async def clear(self) -> None:
        """Clear all messages from the context."""
        self._messages = []
        self._recent_messages = []
        self._old_messages = []

    async def _summarize_old_bucket(self) -> None:
        """Summarize messages in the old bucket using the model client."""
        if not self._old_messages or not self._model_client:
            return
            
        # Create summarization prompt
        messages = [
            SystemMessage(content=self._summarize_prompt),
            UserMessage(
                content="\n".join([
                    f"{msg.__class__.__name__}: {msg.content}" 
                    for msg in self._old_messages
                ]),
                source="system"
            )
        ]
        
        try:
            # Generate summary
            cancellation_token = CancellationToken()
            result = await self._model_client.create(
                messages=messages,
                cancellation_token=cancellation_token
            )
            
            # Replace old bucket with summary
            summary_content = f"[Summary of previous conversation: {result.content}]"
            self._old_messages = [SystemMessage(content=summary_content)]
            
        except Exception as e:
            # If summarization fails, keep a subset of old messages
            excess = len(self._old_messages) - (self._old_capacity // 2)
            if excess > 0:
                self._old_messages = self._old_messages[excess:]
            
            # Add error note
            self._old_messages.insert(
                0, 
                SystemMessage(content=f"[Failed to summarize {excess} previous messages: {str(e)}]")
            )

    def _to_config(self) -> SummarizingChatCompletionContextConfig:
        """Convert the context to a configuration.
        
        Returns:
            SummarizingChatCompletionContextConfig: The configuration
        """
        model_client_config = None
        if self._model_client:
            model_client_config = self._model_client.dump_component().model_dump()
            
        return SummarizingChatCompletionContextConfig(
            recent_capacity=self._recent_capacity,
            old_capacity=self._old_capacity,
            summarize_prompt=self._summarize_prompt,
            model_client=model_client_config,
            initial_messages=self._initial_messages
        )

    @classmethod
    def _from_config(cls, config: SummarizingChatCompletionContextConfig) -> Self:
        """Create a context from a configuration.
        
        Args:
            config (SummarizingChatCompletionContextConfig): The configuration
            
        Returns:
            Self: A new context instance
        """
        model_client = None
        if config.model_client:
            from autogen_core.models import ChatCompletionClient
            model_client = ChatCompletionClient.load_component(config.model_client)
            
        return cls(
            recent_capacity=config.recent_capacity,
            old_capacity=config.old_capacity,
            summarize_prompt=config.summarize_prompt,
            model_client=model_client,
            initial_messages=config.initial_messages
        )

    async def save_state(self) -> Mapping[str, Any]:
        """Save the state of the context.
        
        Returns:
            Mapping[str, Any]: The state
        """
        from autogen_core.model_context._chat_completion_context import ChatCompletionContextState
        
        # Save recent and old messages as separate lists
        return {
            "messages": self._messages,
            "recent_messages": self._recent_messages,
            "old_messages": self._old_messages
        }

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """Load the state of the context.
        
        Args:
            state (Mapping[str, Any]): The state
        """
        if "messages" in state:
            self._messages = state["messages"]
        if "recent_messages" in state:
            self._recent_messages = state["recent_messages"]
        if "old_messages" in state:
            self._old_messages = state["old_messages"]