from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf import settings
import requests
from django.http import HttpResponse 
import pprint
from datetime import datetime, timedelta


def get_exchange_rates(search_date):
    # API 키와 URL을 설정
    API_KEY = settings.EXCHANGE_API_KEY
    URL = f'https://www.koreaexim.go.kr/site/program/financial/exchangeJSON'

    # 날짜를 'YYYYMMDD' 형식으로 변환
    search_date_str = search_date.strftime('%Y%m%d')

    params = {
        'authkey': API_KEY,
        'searchdate': search_date_str,
        'data': 'AP01'
    }

    response = requests.get(URL, params=params)
    if response.status_code == 200:
        exchange_data = response.json()
        if exchange_data:  # 데이터가 비어 있지 않으면 반환
            return exchange_data
        else:  # 데이터가 비어 있으면 전날 데이터를 가져옴
            previous_date = search_date - timedelta(days=1)
            return get_exchange_rates(previous_date)
    else:
        return None


@api_view(['POST'])
def calculate_exchange(request):
    if request.method == 'POST':
        try:
            data = request.data
            input_country = data.get('inputcountry')
            output_country = data.get('outputcountry')
            amount = float(data.get('money'))
            
            # 오늘 날짜의 환율 데이터 가져오기
            today = datetime.today()
            exchange_data = get_exchange_rates(today)
            if exchange_data is None:
                return Response({'error': 'Failed to fetch exchange rates'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # available_currencies = [item["cur_nm"] for item in exchange_data]   # 환율 데이터의 모든 cur_nm 값 출력

            # 입력통화 및 출력통화에 해당하는 환율 찾기
            input_rate = next((item for item in exchange_data if item["cur_nm"].strip() == input_country.strip()), None)
            output_rate = next((item for item in exchange_data if item["cur_nm"].strip() == output_country.strip()), None)

            if input_rate and output_rate:
                input_rate_value = float(input_rate['kftc_deal_bas_r'].replace(',', ''))
                output_rate_value = float(output_rate['kftc_deal_bas_r'].replace(',', ''))

                # JPY(100), IDR(100) 같은 경우를 처리
                if "(100)" in input_rate['cur_unit']:
                    input_rate_value /= 100
                if "(100)" in output_rate['cur_unit']:
                    output_rate_value /= 100

                # 환율 계산
                result = (amount / output_rate_value) * input_rate_value
                # 계산된 환율 보내기
                return Response({'result': result}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid currency code'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)