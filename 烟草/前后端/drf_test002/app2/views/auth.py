import base64
import io
import random
import string
import uuid

from django.core.cache import cache
from PIL import Image, ImageDraw, ImageFont
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


CAPTCHA_TTL = 300
CAPTCHA_CHARS = string.ascii_uppercase + string.digits


class CaptchaThrottle(AnonRateThrottle):
    scope = 'captcha'


def _captcha_image(code):
    image = Image.new('RGB', (148, 48), '#f4fbf6')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for _ in range(24):
        x1, y1 = random.randrange(148), random.randrange(48)
        x2, y2 = random.randrange(148), random.randrange(48)
        draw.line((x1, y1, x2, y2), fill='#b7d9c0', width=1)
    for index, char in enumerate(code):
        draw.text((14 + index * 24, random.randrange(9, 17)), char, fill='#1e7650', font=font)
    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(output.getvalue()).decode('ascii')


class CaptchaView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [CaptchaThrottle]

    def get(self, request):
        code = ''.join(random.choice(CAPTCHA_CHARS) for _ in range(5))
        captcha_id = uuid.uuid4().hex
        cache.set(f'captcha:{captcha_id}', code, CAPTCHA_TTL)
        return Response({'code': 200, 'msg': '验证码已生成', 'data': {
            'captcha_id': captcha_id,
            'image': _captcha_image(code),
            'expires_in': CAPTCHA_TTL,
        }})
