"""
Seasonal and Branch Mapping Tables

Provides static mappings for:
- Gregorian month → Earth Branch (월지)
- Earth Branch → Season (계절)
- Earth Branch → Element (오행)

Version: 1.0.0
Date: 2025-10-09 KST
"""

# Gregorian month (1-12) to Earth Branch (월지)
# Note: Traditional transition occurs at solar terms, not month boundaries
# This is a simplified table for fallback/approximation only
GREGORIAN_MONTH_TO_BRANCH = {
    1: "丑",  # 축월 (12/7 ~ 1/5, 小寒~大寒)
    2: "寅",  # 인월 (1/6 ~ 2/3, 立春~雨水)
    3: "卯",  # 묘월 (2/4 ~ 3/5, 驚蟄~春分)
    4: "辰",  # 진월 (3/6 ~ 4/4, 清明~穀雨)
    5: "巳",  # 사월 (4/5 ~ 5/5, 立夏~小滿)
    6: "午",  # 오월 (5/6 ~ 6/5, 芒種~夏至)
    7: "未",  # 미월 (6/6 ~ 7/6, 小暑~大暑)
    8: "申",  # 신월 (7/7 ~ 8/7, 立秋~處暑)
    9: "酉",  # 유월 (8/8 ~ 9/7, 白露~秋分)
    10: "戌",  # 술월 (9/8 ~ 10/7, 寒露~霜降)
    11: "亥",  # 해월 (10/8 ~ 11/6, 立冬~小雪)
    12: "子",  # 자월 (11/7 ~ 12/6, 大雪~冬至)
}

# Earth Branch → Season
BRANCH_TO_SEASON = {
    "寅": "spring",  # 2월 입춘~우수
    "卯": "spring",  # 3월 경칩~춘분
    "辰": "long_summer",  # 4월 청명~곡우 (춘말하초, 土의 계절)
    "巳": "summer",  # 5월 입하~소만
    "午": "summer",  # 6월 망종~하지
    "未": "long_summer",  # 7월 소서~대서 (하말추초, 土의 계절)
    "申": "autumn",  # 8월 입추~처서
    "酉": "autumn",  # 9월 백로~추분
    "戌": "long_summer",  # 10월 한로~상강 (추말동초, 土의 계절)
    "亥": "winter",  # 11월 입동~소설
    "子": "winter",  # 12월 대설~동지
    "丑": "long_summer",  # 1월 소한~대한 (동말춘초, 土의 계절)
}

# Earth Branch → Element
BRANCH_TO_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

# Heavenly Stem → Element
STEM_TO_ELEMENT = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

# Season → Element boost mapping
SEASON_ELEMENT_BOOST = {
    "spring": {"木": 10, "火": 5, "土": 0, "金": -5, "水": 3},
    "summer": {"木": 3, "火": 10, "土": 5, "金": 0, "水": -5},
    "long_summer": {"木": 0, "火": 3, "土": 10, "金": 5, "水": 0},
    "autumn": {"木": -5, "火": 0, "土": 3, "金": 10, "水": 5},
    "winter": {"木": 5, "火": -5, "土": 0, "金": 3, "水": 10},
}

# Element generation cycle (相生)
ELEMENT_GENERATES = {
    "木": "火",  # Wood generates Fire
    "火": "土",  # Fire generates Earth
    "土": "金",  # Earth generates Metal
    "金": "水",  # Metal generates Water
    "水": "木",  # Water generates Wood
}

# Element control cycle (相剋)
ELEMENT_CONTROLS = {
    "木": "土",  # Wood controls Earth
    "火": "金",  # Fire controls Metal
    "土": "水",  # Earth controls Water
    "金": "木",  # Metal controls Wood
    "水": "火",  # Water controls Fire
}
