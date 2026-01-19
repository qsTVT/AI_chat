import json
import uuid

from django.http import JsonResponse, StreamingHttpResponse

from ollama_Qwen.ollama_Qwen import chat as ollama_chat


def chat(request):
    quesion = json.loads(request.POST.get("messages"))
    text = quesion["question"]
    session_id = request.headers.get("X-Chat-Session-ID")
    dst = ollama_chat(text, session_id)
    return StreamingHttpResponse(dst, content_type="text/plain")


def get_session(request):
    session_id = request.headers.get("X-Chat-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
        print("创建session_id:", session_id)
    return JsonResponse({
        "code": 200,
        "data": session_id,
    })

