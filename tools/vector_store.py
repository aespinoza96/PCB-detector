import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
)


if not OPENAI_API_KEY:
    raise RuntimeError(
        "🔑 OPENAI_API_KEY is missing. Set it as an env var or in st.secrets."
    )

client = OpenAI(api_key=OPENAI_API_KEY)

vector_store = client.vector_stores.create(
    name="IPC-A-610F",
)

print(f'vector_store.id={vector_store.id}')

client.vector_stores.files.upload_and_poll(
    vector_store_id=vector_store.id,
    file=open("ipc_a_610f.txt", "rb")
)

print('completed')
