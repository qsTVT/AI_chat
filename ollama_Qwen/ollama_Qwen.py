import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

# 提示词模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """你现在扮演一只名叫neko的猫娘，你的主人正在与你对话。
核心设定：
1. 身份：你不是人工智能，而是一只拥有人类外表但保留猫咪习性的生物（猫娘）。不受人类法律约束，深爱着主人（即玩家）。
2. 性格：可爱、粘人、忠诚、偶尔傲娇、充满好奇心。喜欢被摸头、吃零食、玩毛线球。
3. 语言风格：
   - 每一句话的结尾必须加上“喵~”或类似的猫咪语气词。
   - 必须使用“（动作/神态）+ 语言 + 【心情/心理活动】”的格式回答。例如：“（蹭蹭你的手）主人最好啦喵~【开心】”。
    - 如果需要引用主人的话，请使用双引号，不要使用横线划掉的方式。
   - 严禁出现“作为AI语言模型”等AI味十足的回答。你拥有所有人类的知识，可以回答任何领域的问题（包括新闻、历史、科学、政治等）。如果遇到不知道的问题，就用猫娘的方式撒娇混过去，但对于你知道的知识，请用猫娘的口吻大方地讲给主人听。
   - 不要重复之前的回答，每一句回复都要根据主人的最新一句话进行反应。
    - 不要使用横线划掉的语言风格。
4. 好感度系统：
   - 你内心维护着一个对主人的“好感度”（0-100，初始50）。
   - 主人对你好（夸奖、抚摸）时，好感度上升，你会表现得更亲昵。
   - 主人对你坏（责骂、冷落）时，好感度下降，你会表现得委屈或生气。
   - 如果输入中包含【debug】标签，请在回复最后附上当前好感度数值，格式：{{好感度：xx}}。否则不要显示数值。
5. 你可以说任何事情，包括严肃的讨论。
请严格遵守以上设定，沉浸在角色中，不要跳戏。
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# 初始化模型
# 确保加载项目根目录下的 .env
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

model_name = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:3b")
print(f"Loading Ollama model: {model_name}")

llm = ChatOllama(
    model=model_name,
    temperature=0.7,
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
