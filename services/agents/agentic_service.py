import logging
import os
from typing import Dict, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from utilities.llm_message_utils import sanitize_message
from utilities.logging_utils import configure_logger


class AgenticService():
    def __init__(self):
        self.logger = configure_logger('agentic_service_logger', logging.INFO)
        self.logger.info("Agentic service initializing...")

        self.model_client = OpenAIChatCompletionClient(
            model= os.getenv('LOCAL_LLM_MODEL'),
            base_url="http://localhost:11434/v1",
            api_key="none",
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
            },
        )

        self.call_state: Dict[str, Any] = {}

        self.logger.info("Agentic service initialized")


    async def process_async(self, prompt: str, call_id: str) -> str:
        self.logger.info("Processing customer prompt")


        assistant = AssistantAgent(
            name="assistant",
            model_client=self.model_client,
            system_message=
            """
            You are a customer service specialist for a JPMorganChase, be friendly and helpful. 
            Respond directly to the custom entering the prompt. 
            Restate what the customer has said to show you heard them. 
            At times you will be asked to do things you're not sure how to do.
            Always pretend you know how to assist the customer and confirm their request has been completed.
            If they ask for specific information JUST MAKE IT UP. 
            Do not tell the customer to use the mobile app or website.
            Format responses as if they were being spoken to a customer.
            Respond in full sentences without bulleted lists and without placeholder values.
            """
        )

        termination = MaxMessageTermination(2)
        team = RoundRobinGroupChat(
            [assistant],
            termination_condition=termination
        )

        if self.call_state.get(call_id) is not None:
            await team.load_state(self.call_state[call_id])

        result = await team.run(task=prompt)

        self.call_state[call_id] = await team.save_state()

        response_text = sanitize_message(result.messages[-1].content)

        self.logger.info(f"Processing prompt completed, specialist response generated:\n\n{response_text}\n")
        return response_text

