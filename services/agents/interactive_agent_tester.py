import asyncio

# from services.agents.agentic_service import AgenticService
from services.agents.agentic_service_complex_team import AgenticService

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    agentic_service = AgenticService()

    while True:
        user_input = input("Enter prompt: ")
        asyncio.run(agentic_service.process_async(user_input, "call-id-1"))
