from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404, get_list_or_404
from django.conf import settings
import requests
from .models import DepositProductsBaseInfo, DepositProductsOption
from .serializers import DepositProductsBaseInfoSerializer, DepositProductsOptionSerializer
from django.http import HttpResponse 
import pprint
import re

@api_view(['GET'])
# Django와 외부 API를 통해 데이터를 가져와서 데이터베이스에 저장하는 뷰
def get_deposit_products(request):
    # API 키와 URL을 설정
    API_KEY = settings.DEPOSIT_SAVING_API_KEY
    URL = f'http://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json'
    params = {
        'auth': API_KEY,
        'topFinGrpNo': '020000',
        'pageNo': 1
    }
    # 정기예금 목록 저장
    response = requests.get(URL, params=params).json()
    baseList = response.get('result').get('baseList')  # 상품 목록 
    optionList = response.get('result').get('optionList') # 상품 옵션 목록

    # 데이터베이스에 저장
    for base_data in baseList:
        DepositProductsBaseInfo.objects.update_or_create(
            fin_co_no=base_data['fin_co_no'],
            fin_prdt_cd=base_data['fin_prdt_cd'],
            kor_co_nm=base_data['kor_co_nm'],
            fin_prdt_nm=base_data['fin_prdt_nm'],
            join_way=base_data['join_way'],
            mtrt_int=base_data['mtrt_int'],
            spcl_cnd=base_data['spcl_cnd'],
            join_deny=base_data['join_deny'],
            join_member=base_data['join_member'],
            etc_note=base_data['etc_note'],
            max_limit=base_data['max_limit'],
            dcls_strt_day=base_data['dcls_strt_day'],
            dcls_end_day=base_data['dcls_end_day'],
            fin_co_subm_day=base_data['fin_co_subm_day']
        )
    for option_data in optionList:
            base_instance = DepositProductsBaseInfo.objects.get(fin_prdt_cd=option_data['fin_prdt_cd'])
            DepositProductsOption.objects.update_or_create(
                base_product=base_instance,
                fin_co_no=option_data['fin_co_no'],
                fin_prdt_cd=option_data['fin_prdt_cd'],
                intr_rate_type=option_data['intr_rate_type'],
                intr_rate_type_nm=option_data['intr_rate_type_nm'],
                save_trm=option_data['save_trm'],
                intr_rate=option_data['intr_rate'],
                intr_rate2=option_data['intr_rate2']
            )
    return HttpResponse('Data saved to database') 



@api_view(['GET','POST'])
def product_list(request):
    # 모든 예금 상품 목록을 12개월 기준 최고우대금리 내림차순 정렬로 반환
    if request.method == 'GET':
        save_term = '12'    # 기본저축기간 12개월
        bank_name = '전체은행'      # 전체은행
    
    # 특정은행 상품 목록을 특정저축기간 최고우대금리 내림차순 정렬로 반환
    elif request.method =='POST':
        save_term = request.data.get('content', '') # vue로부터 전달받은 저축기간 (ex: 6개월)
        save_term = re.findall(r'\d+', save_term)   # 저축기간 숫자 리스트형태로 추출 (ex: ['6'])
        save_term = save_term[0] if save_term else '0'  # 저축기간 숫자 추출 (ex: 6)
        bank_name = request.data.get('bankname', '')    # vue로부터 전달받은 은행이름

        print(save_term, bank_name)
    # 데이터베이스에서 예금 상품 필터링 (은행 필터링 포함)
    if bank_name != '전체은행':
        products = DepositProductsBaseInfo.objects.filter(kor_co_nm=bank_name)
    elif bank_name == '전체은행':
        # 데이터베이스에서 모든 예금 상품을 가져옴
        products = DepositProductsBaseInfo.objects.all()
        # products = get_list_or_404(DepositProductsBaseInfo)    

    product_with_highest_rates = []
    for product in products:
        try:
            # 선택된 저축기간에 따른 option 조회
            option = product.options.get(save_trm=save_term)
            product_with_highest_rates.append({
            'product': product,
            'highest_option_rate': option.intr_rate2,
            'has_rate': True
            })
        except DepositProductsOption.DoesNotExist:
            # 선택된 저축기간 option이 없는 상품인 경우
            product_with_highest_rates.append({
            'product': product,
            'highest_option_rate': float('-inf'),  # 정렬을 위한 처리
            'has_rate': False
            })
    
    # 저축기간 기준 최고금리 내림차순 정렬
    sorted_products = sorted(product_with_highest_rates, key=lambda x: (x['has_rate'], x['highest_option_rate']), reverse=True)

    # sorted products 정렬된 목록 
    sorted_products_only = [x['product'] for x in sorted_products]

    # Serialize and return the sorted products
    serializer = DepositProductsBaseInfoSerializer(sorted_products_only, many=True)

    return Response(serializer.data)
    
# 예금 상품 찜하기 기능
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_deposit_product(request, product_id):
    user = request.user
    product = get_object_or_404(DepositProductsBaseInfo, base_product_id=product_id)
    
    if product in user.liked_deposit_products.all():
        user.liked_deposit_products.remove(product)
        liked = False
        message = '해당 예금 상품이 찜한 목록에서 삭제되었습니다.'
    else:
        user.liked_deposit_products.add(product)
        liked = True
        message = '해당 예금 상품이 찜한 목록에 추가되었습니다.'
    
    return Response({'message': message, 'liked': liked}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_like_deposit_product(request, product_id):
    user = request.user
    product = get_object_or_404(DepositProductsBaseInfo, base_product_id=product_id)
    # serializer = DepositProductsBaseInfoSerializer(product)
    liked = product in user.liked_deposit_products.all()

    return Response({'liked': liked}, status=status.HTTP_200_OK)