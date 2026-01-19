import os
import sys

# 设置环境变量
os.environ["OLLAMA_MODEL_NAME"] = "qwen3:1.7b"

# 尝试导入 ollama_Qwen
try:
    from ollama_Qwen.ollama_Qwen import chat
    print("导入成功")
    
    # 模拟一次对话
    print("开始对话测试...")
    generator = chat("你好", "test_session_id")
    for chunk in generator:
        print(chunk, end="", flush=True)
    print("\n对话测试结束")
    
except Exception as e:
    print(f"\n发生错误: {e}")
