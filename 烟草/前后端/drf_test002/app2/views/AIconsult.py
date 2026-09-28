import os
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework.views import APIView

API_KEY = os.getenv('DASHSCOPE_API_KEY') or os.getenv('OPENAI_API_KEY', '')
AI_MODEL = os.getenv('DASHSCOPE_MODEL', 'qwen-plus')

def get_demo_response(messages):
    question = (messages[-1].get('content', '') if messages else '').strip().lower()
    if question in ('你好', '您好', 'hello', 'hi', '在吗', '嗨'):
        content = '您好，我是烟草种植助手。您可以直接询问施肥、灌溉、病害识别、烟青虫防治或无人机作业。也可以点击上方示例问题开始测试。'
    elif any(word in question for word in ('无人机', '面追肥', '施药', '喷药')):
        content = '无人机作业前先确认风速、温度和田块边界，避开高温和大风。追肥要按长势分区，喷药要按登记剂量和安全间隔执行，并保留作业记录。'
    elif any(word in question for word in ('缺钾', '叶薄', '叶片薄')):
        content = '缺钾常见表现是下部叶片边缘发黄、叶片薄而脆，严重时出现焦边。建议先结合土壤检测确认，再少量多次补充钾肥，避免一次过量。'
    elif any(word in question for word in ('病害', '花叶', '野火', '白星', '黑胫', '根腐')):
        content = '发现病斑后先隔离清除重病叶，改善通风排湿，避免叶面长时间积水。用药请以当地植保部门登记药剂和标签剂量为准，并严格遵守安全间隔期。'
    elif any(word in question for word in ('灌溉', '浇水', '滴灌', '沟灌')):
        content = '烟田灌溉以少量、均匀、见干见湿为原则。沙土可适当增加次数，黏土要延长间隔；雨后先排水，再根据土壤湿度决定是否补水。'
    elif any(word in question for word in ('施肥', '追肥', '氮磷钾', '基肥')):
        content = '施肥应结合土壤肥力和生育期安排，基肥适量、追肥分次。长势过旺时减少氮肥，缺钾地块优先补钾，并在施肥后记录用量和日期。'
    else:
        content = '请告诉我地块、生育期、症状和近期天气，我会从水肥管理、病虫害防治和田间作业三个方面给出建议。'
    return {'content': content, 'reasoning': ''}

def get_ai_response(messages):
    if not API_KEY:
        return get_demo_response(messages)
    try:
        from openai import OpenAI
        result = OpenAI(api_key=API_KEY, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1').chat.completions.create(model=AI_MODEL, messages=messages, timeout=45)
        return {'content': result.choices[0].message.content, 'reasoning': ''}
    except Exception:
        return get_demo_response(messages)

class ChatAPIView(APIView):
    def post(self, request: HttpRequest):
        session: SessionStore = request.session
        session.setdefault('messages', [])
        question = request.data.get('question')
        if question:
            session['messages'].append({'role': 'user', 'content': question})
            answer = get_ai_response(session['messages'])
            session['messages'].append({'role': 'assistant', **answer})
            session.modified = True
        return Response(session['messages'])
