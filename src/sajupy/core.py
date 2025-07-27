import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import os
from pathlib import Path

class SajuCalculator:
    """사주팔자 계산을 위한 클래스"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Parameters:
        -----------
        csv_path : Optional[str]
            사주 데이터가 포함된 CSV 파일 경로 (기본값: 패키지 내장 파일)
        """
        if csv_path is None:
            # 패키지 내부의 CSV 파일 경로 찾기
            package_dir = Path(__file__).parent
            csv_path = package_dir / 'calendar_data.csv'
        self.csv_path = csv_path
        self.data = None
        self._load_data()
        
        # 천간과 지지
        self.heavenly_stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        self.earthly_branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        
        # 시간별 지지 매핑 (23시-01시: 子時, 01시-03시: 丑時, ...)
        self.hour_branch_mapping = {
            (23, 1): '子', (1, 3): '丑', (3, 5): '寅', (5, 7): '卯',
            (7, 9): '辰', (9, 11): '巳', (11, 13): '午', (13, 15): '未',
            (15, 17): '申', (17, 19): '酉', (19, 21): '戌', (21, 23): '亥'
        }
        
        # Geocoder 초기화
        self.geolocator = Nominatim(user_agent="saju_calculator")
    
    def _load_data(self):
        """CSV 파일에서 데이터를 로드합니다."""
        try:
            # 큰 파일이므로 효율적으로 로드
            self.data = pd.read_csv(self.csv_path, 
                                   dtype={'year': int, 'month': int, 'day': int},
                                   parse_dates=False)
            
            # 데이터 범위 확인
            self.min_year = self.data['year'].min()
            self.max_year = self.data['year'].max()
            
            
        except Exception as e:
            print(f"Failed to load data: {e}")
            raise
    
    def _get_longitude_from_city(self, city: str) -> Optional[float]:
        """
        도시 이름으로부터 경도를 조회합니다.
        
        Parameters:
        -----------
        city : str
            도시 이름
            
        Returns:
        --------
        Optional[float]
            경도 값 (실패시 None)
        """
        try:
            location = self.geolocator.geocode(city, timeout=10)
            if location:
                return location.longitude
            else:
                print(f"Warning: Could not find location for '{city}'")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Warning: Geocoding service error - {e}")
            return None
        except Exception as e:
            print(f"Warning: Error during location lookup - {e}")
            return None
    
    def _calculate_solar_time_correction(self, longitude: float, utc_offset: float) -> float:
        """
        경도와 UTC 오프셋에 따른 태양시 보정값을 계산합니다.
        
        Parameters:
        -----------
        longitude : float
            해당 지역의 경도 (동경은 양수, 서경은 음수)
        utc_offset : float
            UTC 오프셋 (예: 한국은 +9, 미국 동부는 -5)
            
        Returns:
        --------
        float
            시간 보정값 (분 단위)
        """
        # UTC 오프셋에 해당하는 표준 경도 계산 (1시간당 15도)
        standard_longitude = utc_offset * 15
        
        # 경도 1도당 4분의 시간 차이
        # 표준 경도보다 동쪽은 시간이 빠르고, 서쪽은 늦음
        correction_minutes = (longitude - standard_longitude) * 4
        return correction_minutes
    
    def _adjust_time_for_solar(self, hour: int, minute: int, correction_minutes: float) -> Tuple[int, int, int]:
        """
        태양시 보정을 적용하여 시간을 조정합니다.
        
        Parameters:
        -----------
        hour : int
            원래 시간
        minute : int
            원래 분
        correction_minutes : float
            보정할 분 (양수면 시간이 빨라짐, 음수면 늦어짐)
            
        Returns:
        --------
        Tuple[int, int, int]
            조정된 (시간, 분, 날짜변경값)
            날짜변경값: -1(전날), 0(당일), 1(다음날)
        """
        total_minutes = hour * 60 + minute + correction_minutes
        date_change = 0
        
        # 날짜가 바뀌는 경우 처리
        if total_minutes < 0:
            total_minutes += 24 * 60
            date_change = -1
        elif total_minutes >= 24 * 60:
            total_minutes -= 24 * 60
            date_change = 1
            
        adjusted_hour = int(total_minutes // 60)
        adjusted_minute = int(total_minutes % 60)
        
        return adjusted_hour, adjusted_minute, date_change
    
    def _adjust_date_for_solar(self, year: int, month: int, day: int, date_change: int) -> Tuple[int, int, int]:
        """태양시 보정으로 인한 날짜 조정"""
        from datetime import date, timedelta
        current_date = date(year, month, day)
        adjusted_date = current_date + timedelta(days=date_change)
        return adjusted_date.year, adjusted_date.month, adjusted_date.day
    
    def _get_hour_branch(self, hour: int, minute: int = 0) -> str:
        """시간과 분을 지지로 변환합니다."""
        # 분을 고려한 시간 계산
        time_value = hour + minute / 60.0
        
        if time_value < 1 or time_value >= 23:
            return '子'
        elif 1 <= time_value < 3:
            return '丑'
        elif 3 <= time_value < 5:
            return '寅'
        elif 5 <= time_value < 7:
            return '卯'
        elif 7 <= time_value < 9:
            return '辰'
        elif 9 <= time_value < 11:
            return '巳'
        elif 11 <= time_value < 13:
            return '午'
        elif 13 <= time_value < 15:
            return '未'
        elif 15 <= time_value < 17:
            return '申'
        elif 17 <= time_value < 19:
            return '酉'
        elif 19 <= time_value < 21:
            return '戌'
        elif 21 <= time_value < 23:
            return '亥'
        
        return '子'  # 기본값
    
    def _calculate_hour_stem(self, day_stem: str, hour: int, minute: int = 0) -> str:
        """일간과 시간을 기반으로 시간의 천간을 계산합니다.
        
        시주 천간 계산법:
        - 甲己일: 甲子시부터 시작
        - 乙庚일: 丙子시부터 시작
        - 丙辛일: 戊子시부터 시작
        - 丁壬일: 庚子시부터 시작
        - 戊癸일: 壬子시부터 시작
        """
        # 일간별 시작 천간 인덱스
        day_stem_to_start = {
            '甲': 0, '己': 0,  # 甲子시부터
            '乙': 2, '庚': 2,  # 丙子시부터
            '丙': 4, '辛': 4,  # 戊子시부터
            '丁': 6, '壬': 6,  # 庚子시부터
            '戊': 8, '癸': 8   # 壬子시부터
        }
        
        # 시간을 지지 인덱스로 변환
        hour_branch = self._get_hour_branch(hour, minute)
        hour_branch_idx = self.earthly_branches.index(hour_branch)
        
        # 시작 천간 인덱스 가져오기
        start_stem_idx = day_stem_to_start.get(day_stem, 0)
        
        # 시간 천간 인덱스 계산
        hour_stem_idx = (start_stem_idx + hour_branch_idx) % 10
        
        return self.heavenly_stems[hour_stem_idx]
    
    def _check_term_time(self, year: int, month: int, day: int, hour: int, minute: int) -> bool:
        """
        주어진 시간이 해당 날짜의 절기 시간을 넘었는지 확인합니다.
        
        Returns:
        --------
        bool
            절기 시간을 넘었으면 True, 아니면 False
        """
        # 해당 날짜의 데이터 가져오기
        result = self.data[(self.data['year'] == year) & 
                          (self.data['month'] == month) & 
                          (self.data['day'] == day)]
        
        if result.empty:
            return True
        
        row = result.iloc[0]
        try:
            term_time = row['term_time']
        except:
            return True
        
        # term_time이 없거나 빈 값이면 절기가 아님
        if pd.isna(term_time) or str(term_time).strip() == '':
            return True
        
        # term_time 파싱 (YYYYMMDDHHMM 형식)
        try:
            term_time_str = str(int(float(str(term_time))))  # 숫자로 저장된 경우 처리
            if len(term_time_str) == 12:
                term_year = int(term_time_str[0:4])
                term_month = int(term_time_str[4:6])
                term_day = int(term_time_str[6:8])
                term_hour = int(term_time_str[8:10])
                term_minute = int(term_time_str[10:12])
                
                # 현재 시간과 절기 시간 비교
                from datetime import datetime
                current_time = datetime(year, month, day, hour, minute)
                term_datetime = datetime(term_year, term_month, term_day, term_hour, term_minute)
                
                return current_time >= term_datetime
        except:
            return True
        
        return True
    
    def _get_previous_month_pillar(self, year: int, month: int, day: int) -> str:
        """이전 월주를 찾아 반환합니다."""
        from datetime import date, timedelta
        current_date = date(year, month, day)
        
        # 최대 35일 전까지 확인 (한 달 이상 거슬러 올라가는 경우는 드물다)
        for i in range(1, 36):
            prev_date = current_date - timedelta(days=i)
            prev_result = self.data[(self.data['year'] == prev_date.year) & 
                                  (self.data['month'] == prev_date.month) & 
                                  (self.data['day'] == prev_date.day)]
            
            if not prev_result.empty:
                prev_row = prev_result.iloc[0]
                try:
                    prev_term_time = prev_row['term_time']
                    # 이전 날짜에 절기가 있으면 그 전날의 월주 반환
                    if pd.notna(prev_term_time) and str(prev_term_time).strip() != '':
                        # 절기 전날의 월주 반환
                        if i > 1:
                            prev_prev_date = current_date - timedelta(days=i-1)
                            prev_prev_result = self.data[(self.data['year'] == prev_prev_date.year) & 
                                                        (self.data['month'] == prev_prev_date.month) & 
                                                        (self.data['day'] == prev_prev_date.day)]
                            if not prev_prev_result.empty:
                                return prev_prev_result.iloc[0]['month_pillar']
                        return prev_row['month_pillar']
                except:
                    pass
        
        # 못 찾은 경우 빈 문자열 반환
        return ""
    
    def _get_month_pillar_considering_term(self, year: int, month: int, day: int, hour: int, minute: int) -> str:
        """
        절기 시간을 고려하여 월주를 결정합니다.
        """
        # 해당 날짜의 데이터 가져오기
        result = self.data[(self.data['year'] == year) & 
                          (self.data['month'] == month) & 
                          (self.data['day'] == day)]
        
        if result.empty:
            return ""
        
        row = result.iloc[0]
        current_month_pillar = row['month_pillar']
        
        try:
            term_time = row['term_time']
            # 절기가 있는 날인지 확인
            if pd.notna(term_time) and str(term_time).strip() != '':
                # 절기 시간을 넘었는지 확인
                if not self._check_term_time(year, month, day, hour, minute):
                    # 절기 시간 이전이면 실제 이전 월주를 찾아야 함
                    # 절월(월을 바꾸는 절기)인지 확인
                    solar_term = row['solar_term_hanja'] if 'solar_term_hanja' in row.index else ''
                    
                    # 절월 목록 (월을 바꾸는 절기)
                    monthly_terms = ['立春', '驚蟄', '淸明', '立夏', '芒種', '小暑', 
                                   '立秋', '白露', '寒露', '立冬', '大雪', '小寒']
                    
                    if solar_term in monthly_terms:
                        # 절월인 경우에만 이전 월주 찾기
                        # 이전 달의 월주를 가져옴
                        from datetime import date, timedelta
                        prev_date = date(year, month, day) - timedelta(days=20)  # 약 20일 전
                        prev_result = self.data[(self.data['year'] == prev_date.year) & 
                                              (self.data['month'] == prev_date.month) & 
                                              (self.data['day'] == prev_date.day)]
                        
                        if not prev_result.empty:
                            return prev_result.iloc[0]['month_pillar']
        except:
            pass
        
        return current_month_pillar
    
    def calculate_saju(self, year: int, month: int, day: int, hour: int, minute: int = 0,
                      city: Optional[str] = None, longitude: Optional[float] = None, 
                      use_solar_time: bool = False, utc_offset: float = 9,
                      early_zi_time: bool = True) -> Dict[str, any]:
        """
        생년월일시분을 입력받아 사주팔자를 계산합니다.
        
        Parameters:
        -----------
        year : int
            출생 년도 (예: 1990)
        month : int
            출생 월 (1-12)
        day : int
            출생 일 (1-31)
        hour : int
            출생 시간 (0-23, 24시간 형식)
        minute : int
            출생 분 (0-59)
        city : Optional[str]
            출생 도시명 (경도 자동 조회)
        longitude : Optional[float]
            경도 직접 입력 (동경은 양수, 서경은 음수)
        use_solar_time : bool
            태양시 보정 사용 여부 (기본값: False)
        utc_offset : float
            UTC 오프셋 (기본값: 9, 한국 표준시)
        early_zi_time : bool
            조자시(早子時) 사용 여부 (기본값: True)
            True: 00:00-01:00을 당일 자시로 계산 (조자시)
            False: 23:00-00:00을 당일 자시로 계산 (야자시)
            
        Returns:
        --------
        Dict[str, any]
            사주팔자 정보를 담은 딕셔너리
        """
        # 입력값 검증
        if not (self.min_year <= year <= self.max_year):
            raise ValueError(f"Year must be between {self.min_year} and {self.max_year}")
        
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        
        if not (1 <= day <= 31):
            raise ValueError("Day must be between 1 and 31")
        
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
            
        if not (0 <= minute <= 59):
            raise ValueError("Minute must be between 0 and 59")
        
        # 원래 시간 저장
        original_hour, original_minute = hour, minute
        original_year, original_month, original_day = year, month, day
        solar_correction_info = None
        
        # 태양시 보정 적용
        if use_solar_time:
            # 경도 결정
            actual_longitude = None
            location_source = None
            
            if longitude is not None:
                # 직접 입력된 경도 사용
                actual_longitude = longitude
                location_source = "manual"
            elif city is not None:
                # 도시 이름으로 경도 조회
                actual_longitude = self._get_longitude_from_city(city)
                location_source = "geocoded"
                
            if actual_longitude is not None:
                correction_minutes = self._calculate_solar_time_correction(actual_longitude, utc_offset)
                hour, minute, date_change = self._adjust_time_for_solar(hour, minute, correction_minutes)
                
                # 태양시 보정으로 날짜가 바뀌는 경우 처리
                if date_change != 0:
                    year, month, day = self._adjust_date_for_solar(year, month, day, date_change)
                
                solar_correction_info = {
                    'city': city,
                    'longitude': round(actual_longitude, 4),
                    'longitude_source': location_source,
                    'utc_offset': utc_offset,
                    'standard_longitude': utc_offset * 15,
                    'correction_minutes': round(correction_minutes, 1),
                    'original_time': f"{original_hour:02d}:{original_minute:02d}",
                    'solar_time': f"{hour:02d}:{minute:02d}"
                }
            else:
                print("Warning: Could not get longitude information, using standard time.")
        
        # 태양시 보정 후의 날짜 저장 (조자시/야자시 처리를 위해)
        solar_adjusted_year, solar_adjusted_month, solar_adjusted_day = year, month, day
        
        # 조자시/야자시 처리
        zi_time_type = None
        date_adjustment = 0
        
        # 23시대 (야자시 가능 시간)
        if hour == 23:
            if early_zi_time:
                # 조자시 방식: 23시는 전날의 자시
                date_adjustment = 0
                zi_time_type = "夜子時"
            else:
                # 야자시 미사용: 23시부터 다음날로 계산
                date_adjustment = 1
                zi_time_type = "子時"
        # 00시대 (조자시 시간)
        elif hour == 0:
            if early_zi_time:
                # 조자시 방식: 00시는 당일의 자시
                date_adjustment = 0
                zi_time_type = "早子時"
            else:
                # 야자시 미사용: 00시는 이미 다음날이므로 조정 불필요
                date_adjustment = 0
                zi_time_type = "子時"
        
        # 시주 계산을 위해 원래 날짜의 일간 먼저 가져오기
        original_result = self.data[(self.data['year'] == original_year) & 
                                  (self.data['month'] == original_month) & 
                                  (self.data['day'] == original_day)]
        
        if original_result.empty:
            raise ValueError(f"Could not find data for the given date: {original_year}-{original_month}-{original_day}")
        
        original_row = original_result.iloc[0]
        original_day_stem = original_row['day_pillar'][0]  # 원래 날짜의 일간
        
        # 날짜 조정 적용
        if date_adjustment != 0:
            from datetime import date, timedelta
            adjusted_date = date(year, month, day) + timedelta(days=date_adjustment)
            year = adjusted_date.year
            month = adjusted_date.month
            day = adjusted_date.day
        
        # 해당 날짜의 데이터 찾기 (조정된 날짜 또는 원래 날짜)
        result = self.data[(self.data['year'] == year) & 
                          (self.data['month'] == month) & 
                          (self.data['day'] == day)]
        
        if result.empty:
            raise ValueError(f"Could not find data for the given date: {year}-{month}-{day}")
        
        row = result.iloc[0]
        
        # 연주, 월주, 일주 가져오기
        year_pillar = row['year_pillar']
        month_pillar = row['month_pillar']
        day_pillar = row['day_pillar']
        
        # 절기 시간 체크하여 월주 결정
        # 태양시 보정된 시간을 기준으로 체크
        month_pillar_with_term = self._get_month_pillar_considering_term(year, month, day, hour, minute)
        if month_pillar_with_term:
            month_pillar = month_pillar_with_term
        
        # 시주 계산용 일간 결정
        if hour == 23:
            # 23시는 항상 다음날 일간으로 시주 계산
            # 태양시 보정 후의 날짜를 기준으로 다음날 데이터 가져오기
            from datetime import date, timedelta
            next_date = date(solar_adjusted_year, solar_adjusted_month, solar_adjusted_day) + timedelta(days=1)
            next_result = self.data[(self.data['year'] == next_date.year) & 
                                  (self.data['month'] == next_date.month) & 
                                  (self.data['day'] == next_date.day)]
            
            if not next_result.empty:
                next_row = next_result.iloc[0]
                day_stem_for_hour = next_row['day_pillar'][0]
            else:
                # 다음날 데이터가 없는 경우 (데이터 범위 끝)
                day_stem_for_hour = original_day_stem
        else:
            # 23시가 아닌 경우: 항상 원래 날짜의 일간 사용
            day_stem_for_hour = original_day_stem
        
        # 시주 계산
        hour_branch = self._get_hour_branch(hour, minute)
        hour_stem = self._calculate_hour_stem(day_stem_for_hour, hour, minute)
        hour_pillar = hour_stem + hour_branch
        
        # 각 주의 천간과 지지 분리
        result_dict = {
            'year_pillar': year_pillar,
            'month_pillar': month_pillar,
            'day_pillar': day_pillar,
            'hour_pillar': hour_pillar,
            'year_stem': year_pillar[0],
            'year_branch': year_pillar[1],
            'month_stem': month_pillar[0],
            'month_branch': month_pillar[1],
            'day_stem': day_pillar[0],
            'day_branch': day_pillar[1],
            'hour_stem': hour_stem,
            'hour_branch': hour_branch,
            'birth_time': f"{original_hour:02d}:{original_minute:02d}",
            'birth_date': f"{original_year}-{original_month:02d}-{original_day:02d}",
            'zi_time_type': zi_time_type,
            'solar_correction': solar_correction_info
        }
        
        # 날짜가 조정된 경우 정보 추가
        if date_adjustment != 0:
            result_dict['date_adjusted'] = True
            result_dict['adjusted_date'] = f"{year}-{month:02d}-{day:02d}"
            result_dict['date_adjustment'] = date_adjustment
        
        return result_dict
    
    def calculate_saju_from_datetime(self, dt: datetime, city: Optional[str] = None, 
                                   longitude: Optional[float] = None,
                                   use_solar_time: bool = False,
                                   utc_offset: float = 9,
                                   early_zi_time: bool = True) -> Dict[str, any]:
        """datetime 객체로부터 사주를 계산합니다."""
        return self.calculate_saju(dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                                 city, longitude, use_solar_time, utc_offset, early_zi_time)
    
    def get_available_cities(self) -> Dict[str, float]:
        """
        [Deprecated] 이제 모든 도시를 지원합니다.
        대신 calculate_saju에서 city 파라미터로 도시 이름을 입력하세요.
        """
        return {
            "notice": "This function is deprecated.",
            "message": "All city names are now supported. Use the city parameter in calculate_saju."
        }

    def solar_to_lunar(self, year: int, month: int, day: int) -> Dict[str, any]:
        """
        양력을 음력으로 변환합니다.
        
        Parameters:
        -----------
        year : int
            양력 년도
        month : int
            양력 월 (1-12)
        day : int
            양력 일 (1-31)
            
        Returns:
        --------
        Dict[str, any]
            음력 날짜 정보 (year, month, day, is_leap_month)
        """
        try:
            # 해당 양력 날짜 찾기
            row = self.data[(self.data['year'] == year) & 
                           (self.data['month'] == month) & 
                           (self.data['day'] == day)]
            
            if len(row) == 0:
                raise ValueError(f"날짜를 찾을 수 없습니다: {year}-{month:02d}-{day:02d}")
            
            row = row.iloc[0]
            lunar_year = int(row['lunar_year'])
            lunar_month = int(row['lunar_month'])
            lunar_day = int(row['lunar_day'])
            
            # 윤달 여부 확인 (같은 음력 년월이 두 번 나타나는지 확인)
            same_lunar_month = self.data[(self.data['lunar_year'] == lunar_year) & 
                                        (self.data['lunar_month'] == lunar_month)]
            
            is_leap_month = False
            if len(same_lunar_month) > 30:  # 한 달이 30일 이상이면 윤달
                # 현재 날짜가 두 번째 그룹에 속하는지 확인
                first_group_last_day = same_lunar_month.iloc[29]['day']
                if day > first_group_last_day:
                    is_leap_month = True
            
            return {
                "lunar_year": lunar_year,
                "lunar_month": lunar_month,
                "lunar_day": lunar_day,
                "is_leap_month": is_leap_month,
                "solar_date": f"{year}-{month:02d}-{day:02d}"
            }
            
        except Exception as e:
            raise ValueError(f"양력-음력 변환 오류: {str(e)}")
    
    def lunar_to_solar(self, lunar_year: int, lunar_month: int, lunar_day: int, 
                      is_leap_month: bool = False) -> Dict[str, any]:
        """
        음력을 양력으로 변환합니다.
        
        Parameters:
        -----------
        lunar_year : int
            음력 년도
        lunar_month : int
            음력 월 (1-12)
        lunar_day : int
            음력 일 (1-30)
        is_leap_month : bool
            윤달 여부 (기본값: False)
            
        Returns:
        --------
        Dict[str, any]
            양력 날짜 정보 (year, month, day)
        """
        try:
            # 해당 음력 날짜를 가진 모든 행 찾기
            rows = self.data[(self.data['lunar_year'] == lunar_year) & 
                            (self.data['lunar_month'] == lunar_month) & 
                            (self.data['lunar_day'] == lunar_day)]
            
            if len(rows) == 0:
                raise ValueError(f"음력 날짜를 찾을 수 없습니다: {lunar_year}년 {lunar_month}월 {lunar_day}일")
            
            # 윤달이 있는 경우 처리
            if len(rows) > 1:
                if is_leap_month:
                    # 나중에 나오는 날짜가 윤달
                    row = rows.iloc[-1]
                else:
                    # 먼저 나오는 날짜가 평달
                    row = rows.iloc[0]
            else:
                if is_leap_month:
                    raise ValueError(f"해당 음력 날짜에 윤달이 없습니다: {lunar_year}년 {lunar_month}월")
                row = rows.iloc[0]
            
            year = int(row['year'])
            month = int(row['month'])
            day = int(row['day'])
            
            return {
                "solar_year": year,
                "solar_month": month,
                "solar_day": day,
                "solar_date": f"{year}-{month:02d}-{day:02d}",
                "lunar_date": f"{lunar_year}년 {'윤' if is_leap_month else ''}{lunar_month}월 {lunar_day}일"
            }
            
        except Exception as e:
            raise ValueError(f"음력-양력 변환 오류: {str(e)}")
    
    def get_lunar_month_days(self, lunar_year: int, lunar_month: int, is_leap_month: bool = False) -> int:
        """
        특정 음력 월의 일수를 반환합니다.
        
        Parameters:
        -----------
        lunar_year : int
            음력 년도
        lunar_month : int
            음력 월 (1-12)
        is_leap_month : bool
            윤달 여부
            
        Returns:
        --------
        int
            해당 월의 일수 (29 또는 30)
        """
        # 해당 음력 년월의 모든 데이터 찾기
        month_data = self.data[(self.data['lunar_year'] == lunar_year) & 
                              (self.data['lunar_month'] == lunar_month)]
        
        if len(month_data) == 0:
            raise ValueError(f"해당 음력 년월을 찾을 수 없습니다: {lunar_year}년 {lunar_month}월")
        
        # 윤달이 있는 경우
        if len(month_data) > 30:
            # 첫 번째 그룹(평달)과 두 번째 그룹(윤달) 구분
            lunar_days = month_data['lunar_day'].values
            # 음력 일이 1로 다시 시작하는 지점 찾기
            reset_index = -1
            for i in range(1, len(lunar_days)):
                if lunar_days[i] == 1 and lunar_days[i-1] > 1:
                    reset_index = i
                    break
            
            if is_leap_month:
                # 윤달의 일수
                return len(month_data) - reset_index
            else:
                # 평달의 일수
                return reset_index if reset_index > 0 else 30
        else:
            # 윤달이 없는 경우
            if is_leap_month:
                raise ValueError(f"해당 음력 년월에 윤달이 없습니다: {lunar_year}년 {lunar_month}월")
            return len(month_data)
    
    def has_leap_month(self, lunar_year: int, lunar_month: int) -> bool:
        """
        특정 음력 년월에 윤달이 있는지 확인합니다.
        
        Parameters:
        -----------
        lunar_year : int
            음력 년도
        lunar_month : int
            음력 월 (1-12)
            
        Returns:
        --------
        bool
            윤달 존재 여부
        """
        month_data = self.data[(self.data['lunar_year'] == lunar_year) & 
                              (self.data['lunar_month'] == lunar_month)]
        
        # 한 달 데이터가 30개 이상이면 윤달이 있음
        return len(month_data) > 30


# 싱글톤 인스턴스
_calculator_instance = None

def get_saju_calculator() -> SajuCalculator:
    """SajuCalculator 싱글톤 인스턴스를 반환합니다."""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = SajuCalculator()
    return _calculator_instance


# 간편한 함수형 인터페이스
def calculate_saju(year: int, month: int, day: int, hour: int, minute: int = 0, 
                  city: Optional[str] = None, longitude: Optional[float] = None,
                  use_solar_time: bool = False, utc_offset: float = 9,
                  early_zi_time: bool = True) -> str:
    """
    생년월일시분을 입력받아 사주팔자를 계산하고 JSON 문자열로 반환합니다.
    
    Parameters:
    -----------
    year : int
        출생 년도 (예: 1990)
    month : int
        출생 월 (1-12)
    day : int
        출생 일 (1-31)
    hour : int
        출생 시간 (0-23, 24시간 형식)
    minute : int
        출생 분 (0-59)
    city : Optional[str]
        출생 도시명 (경도 자동 조회)
    longitude : Optional[float]
        경도 직접 입력 (동경은 양수, 서경은 음수)
    use_solar_time : bool
        태양시 보정 사용 여부
    utc_offset : float
        UTC 오프셋 (기본값: 9, 한국 표준시)
    early_zi_time : bool
        조자시(早子時) 사용 여부 (기본값: True)
        
    Returns:
    --------
    str
        JSON 형식의 사주팔자 정보
    """
    calculator = get_saju_calculator()
    result = calculator.calculate_saju(year, month, day, hour, minute, city, longitude, 
                                     use_solar_time, utc_offset, early_zi_time)
    return json.dumps(result, ensure_ascii=False, indent=2)


def print_saju(year: int, month: int, day: int, hour: int, minute: int = 0,
              city: Optional[str] = None, longitude: Optional[float] = None,
              use_solar_time: bool = False, utc_offset: float = 9,
              early_zi_time: bool = True) -> str:
    """사주를 계산하고 JSON 형식으로 반환합니다."""
    calculator = get_saju_calculator()
    saju = calculator.calculate_saju(year, month, day, hour, minute, city, longitude, 
                                   use_solar_time, utc_offset, early_zi_time)
    return json.dumps(saju, ensure_ascii=False, indent=2)


def get_saju_details(saju_dict: Dict[str, any]) -> str:
    """사주 딕셔너리를 받아 상세 정보를 JSON 문자열로 반환합니다."""
    details = {
        "pillars": {
            "year": {
                "pillar": saju_dict['year_pillar'],
                "stem": saju_dict['year_stem'],
                "branch": saju_dict['year_branch']
            },
            "month": {
                "pillar": saju_dict['month_pillar'],
                "stem": saju_dict['month_stem'],
                "branch": saju_dict['month_branch']
            },
            "day": {
                "pillar": saju_dict['day_pillar'],
                "stem": saju_dict['day_stem'],
                "branch": saju_dict['day_branch']
            },
            "hour": {
                "pillar": saju_dict['hour_pillar'],
                "stem": saju_dict['hour_stem'],
                "branch": saju_dict['hour_branch']
            }
        },
        "birth_time": saju_dict['birth_time'],
        "birth_date": saju_dict.get('birth_date'),
        "zi_time_type": saju_dict.get('zi_time_type'),
        "date_adjusted": saju_dict.get('date_adjusted', False),
        "solar_correction": saju_dict.get('solar_correction')
    }
    
    return json.dumps(details, ensure_ascii=False, indent=2)


def get_available_cities() -> str:
    """
    [Deprecated] 이제 모든 도시를 지원합니다.
    """
    return json.dumps({
        "notice": "This function is deprecated.",
        "message": "All city names are now supported. Use the city parameter in calculate_saju."
    }, ensure_ascii=False, indent=2)


def solar_to_lunar(year: int, month: int, day: int) -> str:
    """
    양력을 음력으로 변환합니다.
    
    Parameters:
    -----------
    year : int
        양력 년도
    month : int
        양력 월 (1-12)
    day : int
        양력 일 (1-31)
        
    Returns:
    --------
    str
        JSON 형식의 음력 날짜 정보
        
    Example:
    --------
    >>> result = solar_to_lunar(2024, 1, 1)
    >>> print(result)
    {
        "lunar_year": 2023,
        "lunar_month": 11,
        "lunar_day": 20,
        "is_leap_month": false,
        "solar_date": "2024-01-01"
    }
    """
    calculator = get_saju_calculator()
    result = calculator.solar_to_lunar(year, month, day)
    return json.dumps(result, ensure_ascii=False, indent=2)


def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int, 
                  is_leap_month: bool = False) -> str:
    """
    음력을 양력으로 변환합니다.
    
    Parameters:
    -----------
    lunar_year : int
        음력 년도
    lunar_month : int
        음력 월 (1-12)
    lunar_day : int
        음력 일 (1-30)
    is_leap_month : bool
        윤달 여부 (기본값: False)
        
    Returns:
    --------
    str
        JSON 형식의 양력 날짜 정보
        
    Example:
    --------
    >>> result = lunar_to_solar(2023, 11, 20)
    >>> print(result)
    {
        "solar_year": 2024,
        "solar_month": 1,
        "solar_day": 1,
        "solar_date": "2024-01-01",
        "lunar_date": "2023년 11월 20일"
    }
    """
    calculator = get_saju_calculator()
    result = calculator.lunar_to_solar(lunar_year, lunar_month, lunar_day, is_leap_month)
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_lunar_month_info(lunar_year: int, lunar_month: int) -> str:
    """
    특정 음력 년월의 정보를 조회합니다.
    
    Parameters:
    -----------
    lunar_year : int
        음력 년도
    lunar_month : int
        음력 월 (1-12)
        
    Returns:
    --------
    str
        JSON 형식의 월 정보 (일수, 윤달 여부 등)
        
    Example:
    --------
    >>> result = get_lunar_month_info(2023, 2)
    >>> print(result)
    {
        "lunar_year": 2023,
        "lunar_month": 2,
        "has_leap_month": true,
        "regular_month_days": 29,
        "leap_month_days": 30
    }
    """
    calculator = get_saju_calculator()
    
    try:
        has_leap = calculator.has_leap_month(lunar_year, lunar_month)
        result = {
            "lunar_year": lunar_year,
            "lunar_month": lunar_month,
            "has_leap_month": has_leap
        }
        
        # 평달 일수
        regular_days = calculator.get_lunar_month_days(lunar_year, lunar_month, False)
        result["regular_month_days"] = regular_days
        
        # 윤달이 있으면 윤달 일수도 포함
        if has_leap:
            leap_days = calculator.get_lunar_month_days(lunar_year, lunar_month, True)
            result["leap_month_days"] = leap_days
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "lunar_year": lunar_year,
            "lunar_month": lunar_month
        }, ensure_ascii=False, indent=2)
