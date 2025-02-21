import asyncio

from services.agentic_service import AgenticService

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    agentic_service = AgenticService()

    while True:
        user_input = input("Enter prompt: ")
        asyncio.run(agentic_service.process_async(user_input, "call-id-1"))
