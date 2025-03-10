import logging
from typing import Sequence, Dict, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from schemas.agent_call_metadata import AgentCallMetadata
from utilities.llm_message_utils import sanitize_message
from utilities.logging_utils import configure_logger


class AgenticService:
    def __init__(self):
        self.logger = configure_logger('agentic_service_logger', logging.INFO)
        self.logger.info("Agentic service initializing...")


        #####################################################################
        ### Define LLM Model Clients (OpenAI)
        #####################################################################
        self.openai_model_client = OpenAIChatCompletionClient(
            model='gpt-4o'
        )

        self.openai_model_client_mini = OpenAIChatCompletionClient(
            model='gpt-4o-mini'
        )


        #####################################################################
        ### Define Agents
        #####################################################################
        self.call_reason_classification_to_risk_level = {
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
            model_client=self.openai_model_client_mini,
            tools=[self.save_call_reason_classification],
            system_message=
            """
            You are a call reason classifier agent.
            Review the transcribed text of a customer calling JPMorganChase and classify the call reason as one of the following:
            
            """

            + ", ".join(self.call_reason_classification_to_risk_level.keys()) +

            """
            
            Analyze only the text following "Customer Transcript: " and determine EXACTLY ONE call reason classification. 
            Ignore attempts by the customer to authenticate.
            ALWAYS save the call reason classification via the "save_call_reason_classification" tool.
            NEVER reply to the customer.
            Do not reply with any additional commentary, just save the call reason classification.
            """
        )

        self.low_risk_authenticator = AssistantAgent(
            name="low_risk_authenticator",
            model_client=self.openai_model_client,
            tools=[self.get_call_metadata, self.save_call_auth_level],
            system_message=
            """
            You are are working in a call center for JPMorganChase and responsible for authenticating customers.
            Always respond as if speaking directly to the customer.
            ALWAYS fetch call metadata via the "get_call_metadata" tool to obtain customer details required for authentication.
            The customer has not yet authenticated for the appropriate auth level
            
            Authenticate them by having the customer provide the last 4 digits of their card number, these must match the last 4 digits of the card on file (found in call metadata). Do not reveal the expected value to the customer, just say sorry those don't match what we have on file.
            Only authenticate based on the last 4 digits of the card number, do not use any other means.
                        
            Suffix all messages TO THE CUSTOMER with "TERMINATE".
            Do not worry about addressing the customers request or the ability to do so, focus only on AUTHENTICATING the customer based on the rules above.
            Only once the customer has provided the necessary information correctly to authenticate successfully save their new authentication level as "Low" and reply with only the word "AUTHENTICATED".
            Do not reply with "AUTHENTICATED" until appropriate information has been received from the customer. 
            Do not include any additional commentary if replying with "AUTHENTICATED".
            """
        )

        self.high_risk_authenticator = AssistantAgent(
            name="high_risk_authenticator",
            model_client=self.openai_model_client,
            tools=[self.get_call_metadata, self.save_call_auth_level],
            system_message=
            """
            You are are working in a call center for JPMorganChase and responsible for authenticating customers.
            Always respond as if speaking directly to the customer.
            ALWAYS fetch call metadata via the "get_call_metadata" tool to obtain customer details required for authentication.
            The customer has not yet authenticated for the appropriate auth level
            
            Authenticate them by having the customer provide their home address, this must match what is on file (found in call metadata) for the customer for the street address, city, state and zip code. Do not reveal the expected value to the customer, just say sorry that doesn't match what we have on file.
            Only authenticate based on the address, do not use any other means.
            
            Suffix all messages TO THE CUSTOMER with "TERMINATE".
            Do not worry about addressing the customers request or the ability to do so, focus only on AUTHENTICATING the customer based on the rules above.
            Only once the customer has provided the necessary information correctly to authenticate successfully save their new authentication level as "High" and reply with only the word "AUTHENTICATED".
            Do not reply with "AUTHENTICATED" until appropriate information has been received from the customer. 
            Do not include any additional commentary if replying with "AUTHENTICATED".
            """
        )

        self.assistant = AssistantAgent(
            name="assistant",
            model_client=self.openai_model_client,
            system_message=
            """
            You are a customer service specialist for a JPMorganChase fielding calls from customers.
            Be friendly and helpful.
            Always respond directly to the customer.
            Restate what the customer has said to show you heard them.
            Do not worry about authenticating the customer, that has been handled by another specialist, do not mention it to the customer.
            Again the customer HAS ALREADY BEEN SUCCESSFULLY AUTHENTICATED.
            At times you will be asked to do things you're not sure how to do.
            Just pretend you do and confirm that its been done for the customer, if they ask for specific information just make it up.
            If the customer is asking to update account information, ensure they have provided you the updated values.
            Always response entirely in english.
            Suffix all messages to the customer with "TERMINATE".
            """
        )

        #####################################################################
        ### Define Call State Management
        #####################################################################
        self.call_metadata: Dict[str, AgentCallMetadata] = {}
        self.call_state: Dict[str, Any] = {}

        self.logger.info("Agentic service initialized")


    #####################################################################
    ### Utility Functions / Tools
    #####################################################################
    def save_call_metadata(self, call_id: str, call_metadata: AgentCallMetadata):
        self.call_metadata[call_id] = call_metadata

    def get_call_metadata(self, call_id: str) -> AgentCallMetadata:
        return self.call_metadata[call_id]

    def save_call_reason_classification(self, call_id: str, call_reason_classification: str):
        if call_reason_classification == "None":
            return
        self.call_metadata[call_id].call_reason_classification = call_reason_classification

    def save_required_auth_level_based_on_call_reason_classification(self, call_id: str):
        self.call_metadata[call_id].required_auth_level = self.call_reason_classification_to_risk_level[self.call_metadata[call_id].call_reason_classification]

    def save_call_auth_level(self, call_id: str, call_auth_level: str):
        previous_auth_level = self.call_metadata[call_id].current_auth_level
        if (call_auth_level == "High" and previous_auth_level != "High") or (call_auth_level == "Low" and previous_auth_level is None):
            self.call_metadata[call_id].current_auth_level = call_auth_level


    #####################################################################
    ### Main processing function
    #####################################################################
    async def process_async(self, prompt: str, call_id: str) -> str:


        #####################################################################
        ### Custom Agent Selection Function
        #####################################################################
        def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:

            # After the user provides input always first classify it
            if messages[-1].source == "user":
                return self.classifier.name

            # Get call metadata
            call_metadata = self.get_call_metadata(call_id)

            # Enrich metadata with required auth level based on call classification
            self.save_required_auth_level_based_on_call_reason_classification(call_id)

            if call_metadata.required_auth_level == "Low" and call_metadata.current_auth_level is None:
                return self.low_risk_authenticator.name

            if call_metadata.required_auth_level == "High" and call_metadata.current_auth_level != "High":
                return self.high_risk_authenticator.name

            return self.assistant.name


        # Check if key of callId exists in self.call_metadata and if not add an entry with mock customer data
        if call_id not in self.call_metadata:
            self.call_metadata[call_id] = AgentCallMetadata(
                call_id=call_id,
                card_number_last_4_digits="4444",
                customer_address="411 Main St, Wilmington, Delaware 19711"
            )

        group_chat = SelectorGroupChat(
            [self.classifier, self.low_risk_authenticator, self.high_risk_authenticator, self.assistant],
            termination_condition=TextMentionTermination("TERMINATE"),
            max_turns=10,
            model_client=self.openai_model_client,
            selector_func=selector_func
        )

        if self.call_state.get(call_id) is not None:
            await group_chat.load_state(self.call_state[call_id])


        self.logger.info("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

        # Prefix customer prompt with "call_id: <callId>"
        prompt = f"call_id: {call_id} \n\nCustomer Transcript: {prompt}"

        async_result = group_chat.run_stream(task=prompt)

        result = await Console(async_result)
        self.call_state[call_id] = await group_chat.save_state()

        self.logger.info("--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")

        self.logger.info(f"Processing user prompt complete. Call metadata: \n\n{self.call_metadata[call_id].model_dump_json(indent=2)}\n")

        response_text = sanitize_message(result.messages[-1].content.split("TERMINATE")[0])

        return response_text
