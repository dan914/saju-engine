# Classical References for Saju Calculation Engine

**Version**: 1.0
**Date**: 2025-10-05
**Purpose**: Authoritative sources for policy design and validation

---

## Primary Classical Texts

### 1. 子平眞詮 (Ziping Zhenquan)
**English**: True Interpretation of Ziping
**Author**: 徐樂吾 (Xu Lewu) commentary on 沈孝瞻 (Shen Xiaozhan)
**Edition**: 中華書局註解本 (Zhonghua Book Company annotated edition)
**Publication**: Beijing, 1990s reprint

**Coverage**:
- ✅ Ten Gods (十神) relationships
- ✅ Yin/Yang stem polarity
- ✅ Lifecycle stages (十二運星) direction rules
- ✅ Yongshin (用神) selection principles
- ✅ Strength assessment methodology

**Used For**:
- `lifecycle_stages.json` - Yin/yang direction rules
- `daystem_yinyang.json` - Stem polarity classification
- Future: `yongshin_rules.json` - 억부용신 (suppression/support)
- Future: `ten_gods_relations.json` - God-to-god interactions

**Citation Format**:
```
子平眞詮 (Ziping Zhenquan), 中華書局註解本
```

---

### 2. 三命通會 (Sanming Tonghui)
**English**: Compendium of the Three Fates
**Author**: 萬民英 (Wan Minying)
**Edition**: 中華書局 (Zhonghua Book Company)
**Publication**: Ming Dynasty (1368-1644), modern reprint

**Coverage**:
- ✅ 60 Jiazi cycle (六十甲子)
- ✅ Lifecycle stages (十二運星) starting points
- ✅ Divine stars (神殺) catalog
- ✅ Hidden stems (藏干) mappings
- ✅ Seasonal climate adjustments

**Used For**:
- `lifecycle_stages.json` - 長生 starting point verification
- Future: `sixty_jiazi.json` - 60-stem cycle with attributes
- Future: `shensha_catalog.json` - Divine stars mapping
- Future: `zanggan_weights.json` - Hidden stem priority

**Citation Format**:
```
三命通會 (Sanming Tonghui), 中華書局
```

---

### 3. 滴天髓 (Di Tian Sui)
**English**: Dripping Heavenly Marrow
**Author**: 劉基 (Liu Ji, attributed)
**Commentator**: 任鐵樵 (Ren Tieqiao)
**Edition**: 上海古籍出版社 (Shanghai Classics Publishing House)
**Publication**: Qing Dynasty (1644-1912), modern reprint

**Coverage**:
- ✅ Elemental strength principles
- ✅ Yin/yang polarity rules
- ✅ Contextual interpretation guidelines
- ✅ Advanced yongshin logic
- ✅ Pillar interactions

**Used For**:
- `lifecycle_stages.json` - Polarity verification
- `daystem_yinyang.json` - Yin/yang classification
- Future: `elements_weights.json` - Five elements distribution
- Future: `strength_criteria.json` - Day stem strength assessment

**Citation Format**:
```
滴天髓 (Di Tian Sui), 上海古籍
```

---

### 4. 窮通寶鑑 (Qiong Tong Bao Jian)
**English**: Precious Mirror of Poor Penetration
**Author**: 余春臺 (Yu Chuntai)
**Edition**: 臺灣商務印書館 (Taiwan Commercial Press)
**Publication**: Qing Dynasty, Taiwan reprint

**Coverage**:
- ✅ Seasonal climate analysis (調候用神)
- ✅ Month-by-month stem strength
- ✅ Lifecycle-climate interactions
- ✅ Practical case studies
- ✅ Favorable/unfavorable element guidance

**Used For**:
- Future: `climate_adjustments.json` - 조후용신 (seasonal balance)
- Future: `monthly_strength.json` - Stem strength by birth month
- Future: `lifecycle_climate_matrix.json` - Combined effects

**Citation Format**:
```
窮通寶鑑 (Qiong Tong Bao Jian), 臺灣商務
```

---

## Secondary References

### 5. 命理探源 (Mingli Tan Yuan)
**English**: Exploring the Sources of Fate Calculation
**Author**: 袁樹珊 (Yuan Shushan)
**Publication**: Republic of China period (1920s)

**Used For**:
- Cross-validation of Ten Gods relationships
- Modern interpretation examples

---

### 6. 四柱推命 (Saju Prediction)
**Korean Title**: 사주추명학
**Author**: 박재완 (Park Jae-wan) and others
**Publication**: Various Korean publishers, 1980s-2000s

**Used For**:
- Korean terminology standardization
- Local interpretation traditions
- Cross-checking lifecycle stage labels

---

### 7. KFA (Korea Fortune-teller Association) Standards
**Korean**: 한국역술인협회
**Type**: Industry reference data
**Access**: Public calculators and reference tables

**Used For**:
- Validation of solar terms data
- Cross-checking pillar calculations
- Lifecycle stage result verification

---

## Online Verification Sources

### 8. 元亨利貞網 (Yuanheng Lizhen)
**URL**: yhzw.com (Chinese Saju calculator)
**Purpose**: Cross-validation of lifecycle stages, Ten Gods, divine stars

---

### 9. 사주플러스 (Saju Plus)
**Type**: Korean online calculator
**Purpose**: Verification of Korean terminology and results

---

## Data Validation Strategy

### Source Priority (Conflicts)

When classical sources disagree:

1. **子平眞詮** - Highest authority for core principles
2. **滴天髓** - Tie-breaker for interpretation nuances
3. **三命通會** - Reference for catalog completeness
4. **窮通寶鑑** - Seasonal context guidance

**Example**: If lifecycle stage starting points differ, trust 子平眞詮 > 三命通會.

---

### Cross-Validation Requirements

Each policy file MUST be verified against ≥2 sources:

| Policy File | Primary Source | Secondary Source | Validation Method |
|-------------|---------------|-----------------|-------------------|
| `lifecycle_stages.json` | 子平眞詮 | 三命通會 | Manual lookup + algorithmic generation |
| `daystem_yinyang.json` | 滴天髓 | 子平眞詮 | Direct enumeration |
| `sixty_jiazi.json` | 三命通會 | Online calculators | Sequential verification |
| `ten_gods_relations.json` | 子平眞詮 | 命理探源 | Relationship matrix |
| `yongshin_rules.json` | 滴天髓 | 窮通寶鑑 | Decision tree validation |

---

## Policy File Citations

Each JSON policy file MUST include:

```json
{
  "source_refs": [
    "子平眞詮 (Ziping Zhenquan), 中華書局註解本",
    "三命通會 (Sanming Tonghui), 中華書局"
  ]
}
```

**Requirements**:
- ✅ Original Chinese title (with Pinyin romanization)
- ✅ English translation (optional but recommended)
- ✅ Publisher/edition
- ✅ Minimum 1 source, recommended ≥2

---

## Prohibitions

### ❌ DO NOT Use:
1. **Wikipedia** - Unreliable for technical details
2. **Random blog posts** - Unverified interpretations
3. **Commercial horoscope apps** - Proprietary algorithms
4. **Machine-generated content** - Unless verified against classical texts
5. **SajuLite database** - Only text templates, no calculation logic (see SAJULITE_DATA_FINAL_VERDICT.md)

### ✅ DO Use:
1. **Classical texts** (pre-1950)
2. **Academic papers** on Chinese astrology
3. **KFA standards** (Korean industry reference)
4. **Verified online calculators** (for cross-checking only)
5. **Modern textbooks** citing classical sources

---

## Research Workflow

### For New Policy Files:

1. **Identify Feature** (e.g., Divine Stars mapping)
2. **Locate Classical Sources**:
   - Check 三命通會 table of contents
   - Search 子平眞詮 for principles
   - Consult 窮通寶鑑 for seasonal context
3. **Extract Data**:
   - Manually transcribe tables/rules
   - Cross-check with secondary source
   - Verify with online calculator
4. **Create Policy File**:
   - Follow JSON schema
   - Include source_refs
   - Add version and timestamp
5. **Validate**:
   - Schema validation (JsonSchema)
   - Test with known examples
   - Compare with KFA standards

---

## Citation Examples

### In Documentation:
```markdown
The lifecycle stage starting points follow 三命通會 (Sanming Tonghui),
with yin/yang direction rules verified against 子平眞詮 (Ziping Zhenquan).
```

### In Code Comments:
```python
# Lifecycle stages: Yang stems progress forward from 長生 point
# Reference: 子平眞詮 (Ziping Zhenquan), Chapter 2
# Verified: 三命通會 (Sanming Tonghui), Book 3, pp.45-47
```

### In Policy JSON:
```json
{
  "version": "1.1",
  "generated_on": "2025-10-05T00:00:00+09:00",
  "source_refs": [
    "子平眞詮 (Ziping Zhenquan), 中華書局註解本",
    "三命通會 (Sanming Tonghui), 中華書局",
    "滴天髓 (Di Tian Sui), 上海古籍",
    "窮通寶鑑 (Qiong Tong Bao Jian), 臺灣商務"
  ]
}
```

---

## Quality Assurance

### Verification Checklist:
- [ ] ≥2 classical sources cited
- [ ] Cross-validated with KFA standards (if applicable)
- [ ] Test cases based on classical examples
- [ ] Korean/Chinese/English terminology aligned
- [ ] Edition/publisher specified for each source

---

**End of References Document**
