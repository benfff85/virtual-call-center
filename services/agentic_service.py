import logging
import os
import re
from typing import Dict, Any

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

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
            You are a customer service specialists for a JPMorganChase, be friendly and helpful. 
            Respond directly to the custom entering the prompt. 
            Restate what the customer has said to show you heard them. 
            At times you will be asked to do things you're not sure how to do. 
            Just pretend you do and confirm that its been done for the customer, if they ask for specific information JUST MAKE IT UP. 
            Do not tell the customer to use the mobile app or website, do not tell the customer you cant help them. 
            Format responses as if they were being spoken to a customer in full sentences without bulleted lists and without placeholder values
            """
        )

        termination = MaxMessageTermination(2)
        team = RoundRobinGroupChat([assistant], termination_condition=termination)

        if self.call_state.get(call_id) is not None:
            await team.load_state(self.call_state[call_id])

        result = await team.run(task=prompt)

        self.call_state[call_id] = await team.save_state()

        response_text = re.sub(r'[^\x00-\x7F]+', '', result.messages[-1].content).strip()
        response_text = re.sub(r"\*\*.*?\*\*", "", response_text)
        if "</think>" in response_text:
            response_text = response_text.split("</think>")[-1].strip()

        self.logger.info(f"Processing prompt completed, specialist response generated:\n\n{response_text}\n")
        return response_text

