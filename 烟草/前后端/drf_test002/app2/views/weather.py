import requests
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView


class WeatherView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            latitude = float(request.query_params.get('latitude', 34.75))
            longitude = float(request.query_params.get('longitude', 113.62))
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError('Invalid coordinates')
        except (TypeError, ValueError):
            return Response({'error': 'Invalid coordinates'}, status=400)

        cache_key = f'weather:{latitude:.2f}:{longitude:.2f}'
        weather = cache.get(cache_key)
        if weather is None:
            try:
                response = requests.get(
                    'https://api.open-meteo.com/v1/forecast',
                    params={
                        'latitude': latitude,
                        'longitude': longitude,
                        'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
                    },
                    timeout=8,
                )
                response.raise_for_status()
                weather = response.json()['current']
                cache.set(cache_key, weather, 600)
            except (requests.RequestException, KeyError, ValueError):
                return Response({'error': 'Weather service unavailable'}, status=503)
        return Response({'current': weather, 'location': '郑州' if not request.query_params.get('latitude') else '当前位置'})
