import logging
import os
import re
from typing import Sequence, Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from schemas.agent_call_metadata import AgentCallMetadata
from utilities.logging_utils import configure_logger


class AgenticService:
    def __init__(self):
        self.logger = configure_logger('agentic_service_logger', logging.INFO)
        self.logger.info("Agentic service initializing...")

        self.model_client = OpenAIChatCompletionClient(
            model= os.getenv('LLM_MODEL'),
            base_url="http://localhost:11434/v1",
            api_key="none",
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
            },
        )

        self.classification_model_client = OpenAIChatCompletionClient(
            model= os.getenv('LLM_MODEL_CLASSIFICATION'),
            base_url="http://localhost:11434/v1",
            api_key="none",
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
            },
        )

        self.call_metadata: Dict[str, AgentCallMetadata] = {}

        self.call_classification_to_risk_level = {
            "General Product/Benefits Inquiry": "None",
            "Transaction Inquiry": "Low",
            "Fraud/Claims": "High",
            "Account Opening": "High",
            "Payment Processing": "Low",
            "Account Balance Inquiry": "Low",
            "Lost or Stolen Card Reporting": "High",
            "Online Banking Technical Support": "Low",
            "Loan/Mortgage Inquiry": "High",
            "Wire Transfer Assistance": "High",
            "Credit Card Payment Assistance": "Low",
            "Dispute/Chargeback Request": "High",
            "Account Information Update": "High",
            "Rewards Points Inquiry": "Low",
            "Overdraft/NSF Assistance": "Low",
            "Investment Account Inquiry": "High",
            "Mobile App Technical Issue": "Low",
            "Fee or Charge Explanation": "Low",
            "Check Deposit Issues": "Low",
            "Foreign Transaction Inquiry": "High"
        }

        self.classifier = AssistantAgent(
            name="classifier",
            model_client=self.classification_model_client,
            tools=[self.save_call_classification],
            system_message=
            """
            You are a classifier agent who reviews the transcribed text of a customer calling JPMorganChase and classifies their call reason as one of the following:
            """

            + ", ".join(self.call_classification_to_risk_level.keys()) +

            """    
            Analyze the "Customer Transcript" and determine the call reason classification. 
            Always save the classification via the "save_call_classification" tool.
            Never provide a response back.
            """
        )

        self.authenticator = AssistantAgent(
            name="authenticator",
            model_client=self.model_client,
            tools=[self.get_call_metadata, self.save_call_auth_level],
            system_message=
            """
            You are are working in a call center for JPMorganChase and responsible for ensuring customers have authenticated appropriately depending on the level of risk of the activity they are performing. 
            Always respond as if speaking directly to the customer.
            Begin by fetching call metadata and identify the required auth level.
            Low risk auth must have the customer authenticate by providing the last 4 digits of their card number, these must match the last 4 digits of the card on file (found in call metadata). Do not reveal the expected value to the customer, just say sorry those don't match what we have on file.
            High risk auth must have the customer authenticate by providing their home address, this must match what is on file (found in call metadata) for the customer for the street address, city, state and zip code. Do not reveal the expected value to the customer, just say sorry that doesn't match what we have on file.
            Suffix all messages TO THE CUSTOMER with "TERMINATE".

            Only once the customer has provided the necessary information correctly save their new authentication level and reply with only the word "AUTHENTICATED".
            Do not reply with "AUTHENTICATED" until appropriate information has been received from the customer. 
            Do not include any additional commentary if replying with "AUTHENTICATED".
            """
        )


        self.assistant = AssistantAgent(
            name="assistant",
            model_client=self.model_client,
            system_message=
            """
            You are a customer service specialist for a JPMorganChase fielding calls from customers.
            Be friendly and helpful.
            Always respond directly to the customer.
            Restate what the customer has said to show you heard them.
            Do not worry about authenticating the customer, that has been handled by another specialist, do not mention it to the customer. Do not mention confirming either last 4 digits of the card number nor the address.
            At times you will be asked to do things you're not sure how to do.
            Just pretend you do and confirm that its been done for the customer, if they ask for specific information just make it up.
            Always response entirely in english.
            Suffix all messages to the customer with "TERMINATE".
            """
        )

        self.state = None
        self.logger.info("Agentic service initialized")


    def save_call_metadata(self, call_id: str, call_metadata: AgentCallMetadata):
        self.call_metadata[call_id] = call_metadata

    def get_call_metadata(self, call_id: str) -> AgentCallMetadata:
        return self.call_metadata[call_id]

    def save_call_classification(self, call_id: str, call_classification: str):
        self.call_metadata[call_id].call_classification = call_classification

    def save_required_auth_level_based_on_classification(self, call_id: str):
        self.call_metadata[call_id].required_auth_level = self.call_classification_to_risk_level[self.call_metadata[call_id].call_classification]

    def save_call_auth_level(self, call_id: str, call_auth_level: str):
        previous_auth_level = self.call_metadata[call_id].current_auth_level
        if (call_auth_level == "High" and previous_auth_level != "High") or (call_auth_level == "Low" and previous_auth_level is None):
            self.call_metadata[call_id].current_auth_level = call_auth_level

    async def process_async(self, prompt: str, call_id: str) -> str:

        # define custom agent selection function
        def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:

            # After the user provides input always first classify it
            if messages[-1].source == "user":
                return self.classifier.name

            # Get call metadata
            call_metadata = self.get_call_metadata(call_id)

            # Enrich metadata with required auth level based on call classification
            self.save_required_auth_level_based_on_classification(call_id)

            if (call_metadata.required_auth_level == "High" and call_metadata.current_auth_level != "High") or (call_metadata.required_auth_level == "Low" and call_metadata.current_auth_level is None):
                return self.authenticator.name

            return self.assistant.name

        # check if key of callId exists in self.call_metadata and if not add an entry
        if call_id not in self.call_metadata:
            self.call_metadata[call_id] = AgentCallMetadata(call_id=call_id, call_classification="None")

        group_chat = SelectorGroupChat([self.assistant, self.classifier, self.authenticator], termination_condition=TextMentionTermination("TERMINATE"), max_turns=10, model_client=self.model_client, selector_func=selector_func)

        # TODO Make state call-id specific
        if self.state is not None:
            await group_chat.load_state(self.state)

        # Prefix prompt with call_id: <callId>
        prompt = f"call_id: {call_id} \n\nCustomer Transcript: {prompt}"
        self.logger.info("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        self.logger.info("Processing user prompt")

        async_result = group_chat.run_stream(task=prompt)

        result = await Console(async_result)
        self.state = await group_chat.save_state()

        self.logger.info(f"Processing user prompt complete\n{self.call_metadata[call_id].model_dump_json(indent=2)}")
        self.logger.info("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

        return re.sub(r'[^\x00-\x7F]+', '', result.messages[-1].content).split("TERMINATE")[0]
