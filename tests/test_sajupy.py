"""Tests for sajupy library"""

import pytest
import json
from datetime import datetime
import sys
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sajupy import (
    SajuCalculator,
    calculate_saju,
    solar_to_lunar,
    lunar_to_solar,
    get_lunar_month_info
)


class TestSajuCalculator:
    """SajuCalculator 클래스 테스트"""
    
    def test_initialization(self):
        """초기화 테스트"""
        calculator = SajuCalculator()
        assert calculator is not None
        assert calculator.data is not None
        assert len(calculator.heavenly_stems) == 10
        assert len(calculator.earthly_branches) == 12
    
    def test_basic_calculation(self):
        """기본 사주 계산 테스트"""
        calculator = SajuCalculator()
        result = calculator.calculate_saju(1990, 10, 10, 14, 30)
        
        assert 'year_pillar' in result
        assert 'month_pillar' in result
        assert 'day_pillar' in result
        assert 'hour_pillar' in result
        assert len(result['year_pillar']) == 2
        assert len(result['month_pillar']) == 2
        assert len(result['day_pillar']) == 2
        assert len(result['hour_pillar']) == 2
    
    def test_minute_calculation(self):
        """분 단위 계산 테스트"""
        calculator = SajuCalculator()
        result1 = calculator.calculate_saju(1990, 10, 10, 14, 0)
        result2 = calculator.calculate_saju(1990, 10, 10, 14, 59)
        
        # 같은 시간대면 시주가 같아야 함
        assert result1['hour_pillar'] == result2['hour_pillar']
    
    def test_zi_time_handling(self):
        """자시 처리 테스트"""
        calculator = SajuCalculator()
        
        # 조자시 방식 (기본값)
        result_23 = calculator.calculate_saju(1990, 10, 10, 23, 30, early_zi_time=True)
        result_00 = calculator.calculate_saju(1990, 10, 10, 0, 30, early_zi_time=True)
        
        assert result_23['hour_branch'] == '子'
        assert result_00['hour_branch'] == '子'
        assert result_23.get('zi_time_type') == '夜子時'
        assert result_00.get('zi_time_type') == '早子時'
    
    def test_solar_time_correction(self):
        """태양시 보정 테스트"""
        calculator = SajuCalculator()
        
        # 서울 경도로 테스트
        result = calculator.calculate_saju(
            1990, 10, 10, 14, 30,
            longitude=126.9780,
            use_solar_time=True,
            utc_offset=9
        )
        
        assert 'solar_correction' in result
        assert result['solar_correction'] is not None
        assert 'correction_minutes' in result['solar_correction']
        assert 'solar_time' in result['solar_correction']
    
    def test_datetime_input(self):
        """datetime 객체 입력 테스트"""
        calculator = SajuCalculator()
        dt = datetime(1990, 10, 10, 14, 30)
        result = calculator.calculate_saju_from_datetime(dt)
        
        assert result['birth_date'] == "1990-10-10"
        assert result['birth_time'] == "14:30"


class TestConversionFunctions:
    """변환 함수 테스트"""
    
    def test_solar_to_lunar(self):
        """양력→음력 변환 테스트"""
        result_str = solar_to_lunar(2024, 1, 1)
        result = json.loads(result_str)
        
        assert 'lunar_year' in result
        assert 'lunar_month' in result
        assert 'lunar_day' in result
        assert 'is_leap_month' in result
        assert result['solar_date'] == "2024-01-01"
    
    def test_lunar_to_solar(self):
        """음력→양력 변환 테스트"""
        result_str = lunar_to_solar(2023, 11, 20)
        result = json.loads(result_str)
        
        assert 'solar_year' in result
        assert 'solar_month' in result  
        assert 'solar_day' in result
        assert 'solar_date' in result
        assert 'lunar_date' in result
    
    def test_lunar_month_info(self):
        """음력 월 정보 조회 테스트"""
        result_str = get_lunar_month_info(2023, 2)
        result = json.loads(result_str)
        
        assert 'lunar_year' in result
        assert 'lunar_month' in result
        assert 'has_leap_month' in result
        assert 'regular_month_days' in result


class TestMainFunctions:
    """메인 함수 테스트"""
    
    def test_calculate_saju_function(self):
        """calculate_saju 함수 테스트"""
        result_str = calculate_saju(1990, 10, 10, 14, 30)
        result = json.loads(result_str)
        
        assert isinstance(result_str, str)
        assert 'year_pillar' in result
        assert 'month_pillar' in result
        assert 'day_pillar' in result
        assert 'hour_pillar' in result
    
    def test_calculate_saju_with_city(self):
        """도시명으로 계산 테스트"""
        result_str = calculate_saju(
            1990, 10, 10, 14, 30,
            city="Seoul",
            use_solar_time=True
        )
        result = json.loads(result_str)
        
        assert 'solar_correction' in result
        assert result['solar_correction']['city'] == "Seoul"
    
    def test_invalid_input_handling(self):
        """잘못된 입력 처리 테스트"""
        calculator = SajuCalculator()
        
        # 범위 밖 년도
        with pytest.raises(ValueError):
            calculator.calculate_saju(1850, 10, 10, 14, 30)
        
        # 잘못된 월
        with pytest.raises(ValueError):
            calculator.calculate_saju(1990, 13, 10, 14, 30)
        
        # 잘못된 시간
        with pytest.raises(ValueError):
            calculator.calculate_saju(1990, 10, 10, 25, 30)


class TestHourCalculation:
    """시주 계산 테스트"""
    
    def test_hour_branches(self):
        """시간별 지지 테스트"""
        calculator = SajuCalculator()
        
        test_cases = [
            (0, 30, '子'),   # 00:30
            (1, 30, '丑'),   # 01:30
            (3, 30, '寅'),   # 03:30
            (5, 30, '卯'),   # 05:30
            (7, 30, '辰'),   # 07:30
            (9, 30, '巳'),   # 09:30
            (11, 30, '午'),  # 11:30
            (13, 30, '未'),  # 13:30
            (15, 30, '申'),  # 15:30
            (17, 30, '酉'),  # 17:30
            (19, 30, '戌'),  # 19:30
            (21, 30, '亥'),  # 21:30
            (23, 30, '子'),  # 23:30
        ]
        
        for hour, minute, expected_branch in test_cases:
            result = calculator.calculate_saju(1990, 10, 10, hour, minute)
            assert result['hour_branch'] == expected_branch, \
                f"Hour {hour}:{minute} should have branch {expected_branch}, got {result['hour_branch']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 