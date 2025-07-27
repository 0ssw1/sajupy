"""
sajupy - 한국 사주팔자 계산 라이브러리
=====================================

한국 전통 사주팔자를 계산하는 Python 라이브러리입니다.
양력/음력 변환, 태양시 보정, 절기 계산 등을 지원합니다.

Basic usage:
    >>> from sajupy import calculate_saju
    >>> result = calculate_saju(1990, 10, 10, 14, 30)
    >>> print(result)

Classes:
    SajuCalculator: 사주 계산을 위한 메인 클래스

Functions:
    calculate_saju: 사주팔자 계산
    print_saju: 사주팔자 출력
    solar_to_lunar: 양력을 음력으로 변환
    lunar_to_solar: 음력을 양력으로 변환
    get_lunar_month_info: 음력 월 정보 조회
"""

from .core import (
    SajuCalculator,
    calculate_saju,
    print_saju,
    get_saju_details,
    solar_to_lunar,
    lunar_to_solar,
    get_lunar_month_info,
    get_saju_calculator
)

__version__ = "0.1.0"
__author__ = "Suh Seungwan"
__email__ = "suh@yumeta.kr"

__all__ = [
    "SajuCalculator",
    "calculate_saju",
    "print_saju",
    "get_saju_details",
    "solar_to_lunar", 
    "lunar_to_solar",
    "get_lunar_month_info",
    "get_saju_calculator"
] 