import json
import uuid
from django.http import JsonResponse, StreamingHttpResponse
from myapp.models import ChatSession, ChatMessage
from ollama_Qwen.ollama_Qwen import chat as ollama_chat

def get_current_user_id(request):
    try:
        return request.get_signed_cookie("user_auth", default=None, salt="myapp_user")
    except Exception:
        return None

def create_session(request):
    user_id = get_current_user_id(request)
    if not user_id:
        return JsonResponse({"code": 401, "msg": "Unauthorized"})
    
    title = request.GET.get("title", "New Chat")
    session = ChatSession.objects.create(user_id=str(user_id), title=title)
    return JsonResponse({"code": 200, "data": {"id": session.id, "title": session.title}})

def get_session_list(request):
    user_id = get_current_user_id(request)
    if not user_id:
        return JsonResponse({"code": 401, "msg": "Unauthorized"})
    
    sessions = ChatSession.objects.filter(user_id=str(user_id)).values('id', 'title', 'updated_at')
    return JsonResponse({"code": 200, "data": list(sessions)})

def get_messages(request):
    user_id = get_current_user_id(request)
    if not user_id:
        return JsonResponse({"code": 401, "msg": "Unauthorized"})
        
    session_id = request.GET.get("session_id")
    if not session_id:
        return JsonResponse({"code": 400, "msg": "Missing session_id"})
        
    try:
        session = ChatSession.objects.get(id=session_id, user_id=str(user_id))
    except ChatSession.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "Session not found"})
        
    messages = session.messages.all().values('role', 'content')
    return JsonResponse({"code": 200, "data": list(messages)})

def delete_session(request):
    user_id = get_current_user_id(request)
    if not user_id:
         return JsonResponse({"code": 401, "msg": "Unauthorized"})
    session_id = request.GET.get("session_id")
    ChatSession.objects.filter(id=session_id, user_id=str(user_id)).delete()
    return JsonResponse({"code": 200, "msg": "Deleted"})

def update_session_title(request):
    user_id = get_current_user_id(request)
    if not user_id:
        return JsonResponse({"code": 401, "msg": "Unauthorized"})
    
    try:
        data = json.loads(request.body.decode("utf-8"))
        session_id = data.get("session_id")
        title = data.get("title")
    except Exception:
        return JsonResponse({"code": 400, "msg": "Invalid JSON"})

    if not session_id or not title:
        return JsonResponse({"code": 400, "msg": "Missing session_id or title"})

    try:
        session = ChatSession.objects.get(id=session_id, user_id=str(user_id))
        session.title = title
        session.save()
        return JsonResponse({"code": 200, "msg": "Updated"})
    except ChatSession.DoesNotExist:
        return JsonResponse({"code": 404, "msg": "Session not found"})

def chat(request):
    quesion = json.loads(request.POST.get("messages"))
    text = quesion["question"]
    session_id = request.headers.get("X-Chat-Session-ID")
    
    user_id = get_current_user_id(request)
    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id)
            if session.messages.count() == 0:
                session.title = text[:20]
                session.save()
        except ChatSession.DoesNotExist:
            if user_id:
                # If session ID provided but not in DB, create it if user logged in
                session = ChatSession.objects.create(id=session_id, user_id=str(user_id), title=text[:20])

    # Remove early save to prevent context duplication when loading from DB
    # if session:
    #     ChatMessage.objects.create(session=session, role="user", content=text)

    dst = ollama_chat(text, session_id)
    
    def stream_wrapper(generator, session, user_text):
        # Save user message here, ensuring it's in DB for persistence but after get_history might have run
        if session:
            try:
                ChatMessage.objects.create(session=session, role="user", content=user_text)
            except Exception as e:
                print(f"Error saving user message: {e}")

        full_response = ""
        try:
            for chunk in generator:
                full_response += chunk
                yield chunk
            if session:
                ChatMessage.objects.create(session=session, role="assistant", content=full_response)
                session.save()
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"\n[System Error]: {str(e)}"

    return StreamingHttpResponse(stream_wrapper(dst, session, text), content_type="text/plain")

def get_session(request):
    session_id = request.headers.get("X-Chat-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
        # print("创建session_id:", session_id)
    return JsonResponse({
        "code": 200,
        "data": session_id,
    })
