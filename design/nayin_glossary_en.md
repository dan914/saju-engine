# NaYin English Glossary & Label Rules (v1.0)

**Scope**: 六十甲子 정책의 label_en 일관성 확보를 위한 표준 용어 모음.

## 1) Label 형식 규칙

**Pattern**: `Stem-Pinyin-Branch-Pinyin (NaYin_English)`

예) `Jia-Zi (Metal in the Sea)`, `Bing-Yin (Fire in the Furnace)`

**Regex**: `^[A-Z][a-z]+-[A-Z][a-z]+ \([A-Za-z&'\- ]+\)$`

**Pinyin 표준**:
- 干: Jia, Yi, Bing, Ding, Wu, Ji, Geng, Xin, Ren, Gui
- 支: Zi, Chou, Yin, Mao, Chen, Si, Wu, Wei, Shen, You, Xu, Hai

## 2) NaYin 영문 표준(발췌)

| 納音 (中文) | Korean | English Translation |
|-----------|--------|---------------------|
| 海中金 | 해중금 | Metal in the Sea |
| 炉中火 | 노중화 | Fire in the Furnace |
| 大林木 | 대림목 | Great Forest Wood |
| 路旁土 | 노방토 | Roadside Earth |
| 剑锋金 | 검봉금 | Sword Edge Metal |
| 山头火 | 산두화 | Mountain Peak Fire |
| 涧下水 | 간하수 | Stream Water in the Gorge |
| 城头土 | 성두토 | City Wall Earth |
| 白蜡金 | 백랍금 | Wax Metal |
| 杨柳木 | 양류목 | Willow Wood |
| 泉中水 | 천중수 | Spring Water |
| 屋上土 | 옥상토 | Rooftop Earth |
| 霹雳火 | 벽력화 | Thunderbolt Fire |
| 松柏木 | 송백목 | Pine & Cypress Wood |
| 长流水 | 장류수 | Long Flowing Water |
| 砂中金 | 사중금 | Metal in Sand |
| 山下火 | 산하화 | Fire at Mountain's Foot |
| 平地木 | 평지목 | Flatland Wood |
| 壁上土 | 벽상토 | Wall-Top Earth |
| 金箔金 | 금박금 | Gold Foil Metal |
| 覆灯火 | 복등화 | Covered Lamp Fire |
| 天河水 | 천하수 | Milky Way Water |
| 大驿土 | 대역토 | Post-Station Earth |
| 钗钏金 | 차천금 | Ornamental Gold |
| 桑柘木 | 상자목 | Mulberry Wood |
| 大溪水 | 대계수 | Great Stream Water |
| 沙中土 | 사중토 | Sandy Soil |
| 天上火 | 천상화 | Heavenly Fire |
| 石榴木 | 석류목 | Pomegranate Wood |
| 大海水 | 대해수 | Great Sea Water |

## 3) CI 체크 연동

`policies/localization_en_v1.json`을 `dependencies.localization_en`로 참조.

**빌드 시**:
1. 스키마 검증 →
2. NaYin 쌍 규칙 검사(각 납음 당 2레코드) →
3. label_en 패턴 검사(정규식) + NaYin 영문 사전 존재성 검사 →
4. SHA-256 자동 서명 주입(정책 JSON의 `signature` 필드).

본 문서는 번역자·개발자·LLM 프롬프터가 공용 기준으로 사용.
