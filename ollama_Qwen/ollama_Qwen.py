import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

# 提示词模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个AI助手，请根据用户提问回答问题"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# 初始化模型
# 确保加载项目根目录下的 .env
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

model_name = os.getenv("OLLAMA_MODEL_NAME", "qwen3:1.7b")
print(f"Loading Ollama model: {model_name}")

llm = ChatOllama(
    model=model_name,
    temperature=0.5,
    top_p=0.9,
    num_predict=2048
)

chain = prompt_template | llm

# session 存储
store = {}

def get_history(session_id):
    if session_id not in store:
        history = ChatMessageHistory()
        try:
            from myapp.models import ChatSession
            # 确保 session_id 是字符串
            session = ChatSession.objects.get(id=str(session_id))
            messages = session.messages.all()
            for msg in messages:
                if msg.role == 'user':
                    history.add_user_message(msg.content)
                else:
                    history.add_ai_message(msg.content)
        except Exception as e:
            print(f"Error loading history for {session_id}: {e}")
        store[session_id] = history
    return store[session_id]

chainbot = RunnableWithMessageHistory(
    chain,
    get_session_history=get_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

def chat(question, session_id):
    try:
        for chunk in chainbot.stream(
            {"question": question},
            config={
                "configurable": {
                    "session_id": str(session_id)
                }
            }
        ):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        print(f"Error in chat generation: {e}")
        yield f"Error: {str(e)}"
