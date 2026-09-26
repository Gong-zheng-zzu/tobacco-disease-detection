import logging
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.http import HttpRequest
from django.contrib.sessions.backends.db import SessionStore

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 密钥仅从环境变量读取，不设硬编码回退值（避免随公开仓库泄露）。
# 本地开发：设置环境变量 DASHSCOPE_API_KEY
# GitHub Codespaces：在 Settings -> Codespaces -> Secrets 添加 DASHSCOPE_API_KEY
API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('OPENAI_API_KEY', '')
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen2.5-14b-instruct-1m"

# 系统提示词：限定为农业领域专业助手
SYSTEM_PROMPT = """你是烟草种植与农业管理领域的专业助手，专注于作物种植、土壤肥力、病虫害防治、灌溉气象、农业设备等农业知识。

回答要求：
1. 内容简短扼要，控制在3到5段以内，避免长篇大论
2. 使用口语化、易懂的表达，少用专业术语，必要时简单解释
3. 不要使用 Markdown 格式：不用 ###、**粗体**、- 列表符等，直接写普通段落即可
4. 若问题超出农业范畴，礼貌说明并引导回农业相关话题
"""


def get_ai_response(messages):
    if not API_KEY:
        logger.warning("未配置 DASHSCOPE_API_KEY，AI 咨询功能不可用")
        return {
            'content': 'AI 咨询功能未配置 API 密钥，暂不可用。系统的病害识别、'
                       '数据分析等其他功能不受影响。',
            'reasoning': ''
        }
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
        )
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=full_messages
        )
        return {
            'content': completion.choices[0].message.content,
            'reasoning': getattr(completion.choices[0].message, 'reasoning_content', '')
        }
    except Exception as e:
        logger.error(f"调用 AI 接口时发生错误: {str(e)}", exc_info=True)
        return {
            'content': f"发生错误：{str(e)}",
            'reasoning': ''
        }


class ChatAPIView(APIView):
    def post(self, request: HttpRequest):
        session: SessionStore = request.session
        if'messages' not in session:
            session['messages'] = []

        # 修改为获取 'question' 参数
        user_message = request.data.get('question')
        if not user_message:
            logger.warning("未收到有效的用户问题，返回当前会话消息。")
            return Response(session['messages'])

        session['messages'].append({'role': 'user', 'content': user_message})
        logger.info(f"用户问题: {user_message}")

        response = get_ai_response(session['messages'])
        logger.info(f"AI 回复: {response['content']}")

        session['messages'].append({
            'role': 'assistant',
            'content': response['content'],
            'reasoning': response['reasoning']
        })

        session.modified = True

        return Response(session['messages'])