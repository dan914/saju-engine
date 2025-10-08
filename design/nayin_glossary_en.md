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

| 納音 (中文) | English Translation |
|-----------|---------------------|
| 海中金 | Metal in the Sea |
| 炉中火 | Fire in the Furnace |
| 大林木 | Great Forest Wood |
| 路旁土 | Roadside Earth |
| 剑锋金 | Sword Edge Metal |
| 山头火 | Mountain Peak Fire |
| 涧下水 | Stream Water in the Gorge |
| 城头土 | City Wall Earth |
| 白蜡金 | Wax Metal |
| 杨柳木 | Willow Wood |
| 泉中水 | Spring Water |
| 屋上土 | Rooftop Earth |
| 霹雳火 | Thunderbolt Fire |
| 松柏木 | Pine & Cypress Wood |
| 长流水 | Long Flowing Water |
| 砂中金 | Metal in Sand |
| 山下火 | Fire at Mountain's Foot |
| 平地木 | Flatland Wood |
| 壁上土 | Wall-Top Earth |
| 金箔金 | Gold Foil Metal |
| 覆灯火 | Covered Lamp Fire |
| 天河水 | Milky Way Water |
| 大驿土 | Post-Station Earth |
| 钗钏金 | Ornamental Gold |
| 桑柘木 | Mulberry Wood |
| 大溪水 | Great Stream Water |
| 沙中土 | Sandy Soil |
| 天上火 | Heavenly Fire |
| 石榴木 | Pomegranate Wood |
| 大海水 | Great Sea Water |

## 3) CI 체크 연동

`policies/localization_en_v1.json`을 `dependencies.localization_en`로 참조.

**빌드 시**:
1. 스키마 검증 →
2. NaYin 쌍 규칙 검사(각 납음 당 2레코드) →
3. label_en 패턴 검사(정규식) + NaYin 영문 사전 존재성 검사 →
4. SHA-256 자동 서명 주입(정책 JSON의 `signature` 필드).

본 문서는 번역자·개발자·LLM 프롬프터가 공용 기준으로 사용.
