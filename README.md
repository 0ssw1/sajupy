# sajupy

사주팔자 만세력 계산을 위한 Python 라이브러리입니다.

## 특징

- **정확한 사주팔자 계산**: 1900년부터 2100년까지의 만세력 데이터 기반
- **음력/양력 변환**: 음력과 양력 간 자유로운 날짜 변환
- **태양시 보정**: 출생 지역의 경도를 고려한 정확한 시간 계산
- **전 세계 도시 지원**: 도시 이름으로 자동 경도 조회
- **절기 시간 고려**: 절기 시간을 정확히 반영한 월주 계산
- **조자시/야자시 처리**: 23시-01시 구간의 정확한 시주 계산

## 설치

```bash
pip install sajupy
```

## 빠른 시작

```python
from sajupy import calculate_saju

# 기본 사용법
result = calculate_saju(1990, 10, 10, 14, 30)
print(result)

# 태양시 보정을 사용한 계산
result = calculate_saju(
    year=1990, 
    month=10, 
    day=10, 
    hour=14, 
    minute=30,
    city="Seoul",  # 또는 longitude=126.9780
    use_solar_time=True
)
print(result)
```

## 주요 기능

### 1. 만세력 계산

```python
from sajupy import SajuCalculator

calculator = SajuCalculator()

# 상세 옵션을 사용한 사주 계산
saju = calculator.calculate_saju(
    year=1990,
    month=10,
    day=10,
    hour=14,
    minute=30,
    city="Seoul",          # 도시 이름으로 경도 자동 조회
    use_solar_time=True,      # 태양시 보정 사용
    utc_offset=9,           # UTC 오프셋 (서울)
    early_zi_time=True       # 조자시 사용 (00:00-01:00을 당일로)
)

print(f"연주: {saju['year_pillar']}")
print(f"월주: {saju['month_pillar']}")
print(f"일주: {saju['day_pillar']}")
print(f"시주: {saju['hour_pillar']}")
```

### 2. 음력/양력 변환

```python
from sajupy import solar_to_lunar, lunar_to_solar

# 양력을 음력으로 변환
lunar_date = solar_to_lunar(2024, 1, 1)
print(lunar_date)
# {
#     "lunar_year": 2023,
#     "lunar_month": 11,
#     "lunar_day": 20,
#     "is_leap_month": false,
#     "solar_date": "2024-01-01"
# }

# 음력을 양력으로 변환
solar_date = lunar_to_solar(2023, 11, 20)
print(solar_date)
# {
#     "solar_year": 2024,
#     "solar_month": 1,
#     "solar_day": 1,
#     "solar_date": "2024-01-01",
#     "lunar_date": "2023년 11월 20일"
# }
```

### 3. 음력 월 정보 조회

```python
from sajupy import get_lunar_month_info

# 음력 월의 일수 및 윤달 정보 조회
month_info = get_lunar_month_info(2023, 2)
print(month_info)
# {
#     "lunar_year": 2023,
#     "lunar_month": 2,
#     "has_leap_month": true,
#     "regular_month_days": 29,
#     "leap_month_days": 30
# }
```

## 출력 형식

`calculate_saju` 함수는 다음과 같은 딕셔너리 결과를 반환합니다:

```json
{
  "year_pillar": "庚午",
  "month_pillar": "丙戌",
  "day_pillar": "己未",
  "hour_pillar": "辛未",
  "year_stem": "庚",
  "year_branch": "午",
  "month_stem": "丙",
  "month_branch": "戌",
  "day_stem": "己",
  "day_branch": "未",
  "hour_stem": "辛",
  "hour_branch": "未",
  "birth_time": "14:30",
  "birth_date": "1990-10-10",
  "zi_time_type": null,
  "solar_correction": {
    "city": "Seoul",
    "longitude": 126.9780,
    "longitude_source": "geocoded",
    "utc_offset": 9,
    "standard_longitude": 135,
    "correction_minutes": -32.1,
    "original_time": "14:30",
    "solar_time": "13:58"
  }
}
```

## 고급 사용법

### SajuCalculator 클래스 직접 사용

```python
from sajupy import SajuCalculator

# 커스텀 데이터 파일 사용
calculator = SajuCalculator(csv_path='my_custom_data.csv')

# datetime 객체로 계산
from datetime import datetime
dt = datetime(1990, 10, 10, 14, 30)
saju = calculator.calculate_saju_from_datetime(dt, city="Seoul")
```

### 태양시 보정 상세 설정

```python
# 경도를 직접 지정
saju = calculate_saju(
    year=1990, month=10, day=10, hour=14, minute=30,
    longitude=126.9780,  # 서울의 경도
    use_solar_time=True,
    utc_offset=9
)

# 해외 도시 예시
saju = calculate_saju(
    year=1990, month=10, day=10, hour=14, minute=30,
    city="Los Angeles",
    use_solar_time=True,
    utc_offset=-8  # 태평양 표준시
)
```

## 주의사항

- 데이터 범위: 1900년 ~ 2100년
- 시간은 24시간 형식 사용 (0-23)
- 태양시 보정 시 정확한 출생 지역 정보 필요
- 윤달 처리 시 `is_leap_month` 파라미터 확인 필요

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다! 
[이슈](https://github.com/0ssw1/sajupy/issues)를 생성하거나 풀 리퀘스트를 보내주세요.
