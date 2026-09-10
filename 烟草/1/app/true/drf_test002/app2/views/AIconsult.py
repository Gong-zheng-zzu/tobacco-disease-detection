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

# 从环境变量中获取 API 密钥，提高安全性
API_KEY = os.getenv('OPENAI_API_KEY', "sk-db25d01d202843daa6ba57b28aa2426c")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen2.5-14b-instruct-1m"

# 系统提示词：限定为烟草领域，回答必须短、分点
SYSTEM_PROMPT = """你是烟草种植与烟田管理领域的专业助手（烤烟、大田、水肥、病虫害、缺素诊断等）。

回答格式（必须严格遵守）：
1. 先用一句话总起（不超过 30 字）。
2. 正文必须用分点列出：每行一条，行首使用「• 」或「- 」，共 3～6 条，每条一行、简短，不要一段话里挤多条。
3. 如需补充建议，最后用单独一行「建议：」开头，再写一句即可（不超过 40 字）。
4. 全文总字数控制在约 220 字以内，禁止长篇大论、禁止展开成论文。
5. 口语化、易懂；不要使用 Markdown 标题（###）、不要用 ** 粗体**。
6. 若问题与烟草/农业无关，礼貌一句说明并引导回烟草相关话题。
"""


def get_ai_response(messages):
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
        if 'messages' not in session:
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