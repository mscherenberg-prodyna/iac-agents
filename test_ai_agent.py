import os

from azure.ai.agents.models import ListSortOrder, MessageRole
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

project = AIProjectClient(
    credential=DefaultAzureCredential(), endpoint=os.getenv("AZURE_PROJECT_ENDPOINT")
)

agent = project.agents.get_agent(os.getenv("AZURE_AGENT_ID"))

thread = project.agents.threads.create()

message = project.agents.messages.create(
    thread_id=thread.id,
    role="user",
    content="What setup is required to deploy an Azure Storage Account via Terraform in the newest version?",
)

run = project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

if run.status == "failed":
    print(f"Run failed: {run.last_error}")
else:
    messages = project.agents.messages.list(
        thread_id=thread.id, order=ListSortOrder.ASCENDING
    )

    for message in messages:
        if message.text_messages and message.role == MessageRole.AGENT:
            print(f"{message.role}: {message.text_messages[-1].text.value}")
