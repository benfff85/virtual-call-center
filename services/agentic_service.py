import asyncio
import logging

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from asgiref.sync import async_to_sync

from utilities.logging_utils import configure_logger


class AgenticService():
    def __init__(self):
        self.logger = configure_logger('agentic_service_logger', logging.INFO)
        self.logger.info("Agentic service initializing...")

        self.model_client = OpenAIChatCompletionClient(
            model="llama3.2:latest",
            # model="qwen2.5:32b",
            base_url="http://localhost:11434/v1",
            api_key="none",
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
            },
        )
        self.state = None

        self.logger.info("Agentic service initialized")


    async def process_async(self, prompt: str) -> str:
        self.logger.info("Processing prompt: %s", prompt)

        assistant = AssistantAgent(name="assistant", model_client=self.model_client, system_message="You are a customer service specialists for a JPMorganChase, be friendly and helpful. Respond directly to the custom entering the prompt. Restate what the customer has said to show you heard them. At times you will be asked to do things you're not sure how to do. Just pretend you do and confirm that its been done for the customer, if they ask for specific information just make it up.")
        user_proxy = UserProxyAgent("user_proxy")
        # self.termination = TextMentionTermination("exit") # Type 'exit' to end the conversation.
        termination = MaxMessageTermination(2)
        team = RoundRobinGroupChat([assistant], termination_condition=termination)

        if self.state is not None:
            await team.load_state(self.state)

        result = await team.run(task=prompt)

        self.state = await team.save_state()

        self.logger.info(result)
        self.logger.info("Processed prompt")
        return result.messages[-1].content
