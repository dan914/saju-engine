# POST /api/v1/report/saju — JSON Schema + Samples v1.0

**Version:** 1.0
**Date:** 2025-10-07 KST
**Spec:** JSON Schema draft-2020-12

사주 전체 보고서 엔드포인트의 정식 스키마와 검증 가능한 샘플 응답 2건.

---

## JSON Schema (draft-2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.saju.example.com/schemas/report-saju-v1.json",
  "title": "SajuReportResponse",
  "description": "사주 전체 분석 보고서 응답 스키마 (KO-first, RFC-8785 canonical JSON)",
  "type": "object",
  "required": ["meta", "time", "pillars", "analysis", "localization", "evidence"],
  "properties": {
    "meta": {
      "type": "object",
      "required": ["name", "gender", "school_profile", "signatures"],
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "description": "사용자 이름"
        },
        "gender": {
          "type": "string",
          "enum": ["male", "female", "other"],
          "description": "성별 (대운 방향 결정에 영향)"
        },
        "school_profile": {
          "type": "string",
          "description": "학파 프로필 ID (예:徐樂吾, 韋千里, 任鐵樵)"
        },
        "school_profile_ko": {
          "type": "string",
          "description": "학파 프로필 한국어 이름"
        },
        "signatures": {
          "type": "object",
          "required": ["sha256"],
          "properties": {
            "sha256": {
              "type": "string",
              "pattern": "^[a-f0-9]{64}$",
              "description": "RFC-8785 canonical JSON의 SHA-256 해시 (캐시 무결성 검증용)"
            }
          }
        }
      }
    },
    "time": {
      "type": "object",
      "required": ["timezone", "dst", "utc", "lmt", "regional_correction_minutes", "solar_time", "evidence"],
      "properties": {
        "timezone": {
          "type": "string",
          "pattern": "^[A-Za-z]+/[A-Za-z_]+(?:/[A-Za-z_]+)?$",
          "description": "IANA timezone (예: Asia/Seoul)"
        },
        "dst": {
          "type": "boolean",
          "description": "일광 절약 시간 적용 여부"
        },
        "utc": {
          "type": "string",
          "format": "date-time",
          "description": "UTC 시간 (ISO8601)"
        },
        "lmt": {
          "type": "string",
          "format": "date-time",
          "description": "Local Mean Time (경도 보정 적용)"
        },
        "regional_correction_minutes": {
          "type": "integer",
          "minimum": -180,
          "maximum": 180,
          "description": "지역 경도 보정 분 (서울: -32, 부산: -24)"
        },
        "solar_time": {
          "type": "string",
          "format": "date-time",
          "description": "절기 계산에 사용된 태양시"
        },
        "evidence": {
          "type": "object",
          "description": "시간 계산 근거 (solar term, zi transition 등)",
          "properties": {
            "solar_term_prev": {
              "type": "string",
              "description": "직전 절기"
            },
            "solar_term_next": {
              "type": "string",
              "description": "다음 절기"
            },
            "zi_transition": {
              "type": "boolean",
              "description": "자시 전환 발생 여부"
            },
            "zi_hour_mode": {
              "type": "string",
              "enum": ["default", "split_23", "traditional"],
              "description": "자시 처리 모드"
            }
          }
        }
      }
    },
    "pillars": {
      "type": "object",
      "required": ["year", "month", "day"],
      "properties": {
        "year": { "$ref": "#/$defs/Pillar" },
        "month": { "$ref": "#/$defs/Pillar" },
        "day": { "$ref": "#/$defs/Pillar" },
        "hour": {
          "oneOf": [
            { "$ref": "#/$defs/Pillar" },
            { "type": "null", "description": "시간 미상인 경우 null" }
          ]
        },
        "meta": {
          "type": "object",
          "properties": {
            "unknown_hour": {
              "type": "boolean",
              "description": "시간 미상 여부"
            },
            "zi_hour_mode": {
              "type": "string",
              "enum": ["default", "split_23", "traditional"],
              "description": "자시 처리 모드"
            }
          }
        }
      }
    },
    "analysis": {
      "type": "object",
      "required": ["ten_gods", "relations", "strength", "structure", "wuxing", "luck"],
      "properties": {
        "ten_gods": { "$ref": "#/$defs/TenGodsAnalysis" },
        "relations": { "$ref": "#/$defs/RelationsAnalysis" },
        "void": { "$ref": "#/$defs/VoidAnalysis" },
        "life_stage": { "$ref": "#/$defs/LifeStageAnalysis" },
        "shensha": { "$ref": "#/$defs/ShenshaAnalysis" },
        "strength": { "$ref": "#/$defs/StrengthAnalysis" },
        "structure": { "$ref": "#/$defs/StructureAnalysis" },
        "climate": { "$ref": "#/$defs/ClimateAnalysis" },
        "yongshin": { "$ref": "#/$defs/YongshinAnalysis" },
        "wuxing": { "$ref": "#/$defs/WuxingAnalysis" },
        "luck": { "$ref": "#/$defs/LuckAnalysis" }
      }
    },
    "localization": {
      "type": "object",
      "required": ["ko"],
      "properties": {
        "ko": {
          "type": "boolean",
          "description": "한국어 라벨 보강 여부"
        },
        "enrichment": {
          "type": "object",
          "description": "보강 메타데이터",
          "properties": {
            "mappings_count": { "type": "integer" },
            "locale": { "type": "string" },
            "enricher_version": { "type": "string" }
          }
        }
      }
    },
    "evidence": {
      "type": "object",
      "required": ["policies_applied", "trace_id", "inputs_hash"],
      "properties": {
        "policies_applied": {
          "type": "array",
          "items": { "type": "string" },
          "description": "적용된 정책 파일 목록 (예: strength_policy_v2.json)"
        },
        "trace_id": {
          "type": "string",
          "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
          "description": "추적 ID (UUID v4)"
        },
        "inputs_hash": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$",
          "description": "입력값 SHA-256 해시 (재현성 보장)"
        }
      }
    },
    "entitlements": {
      "type": "object",
      "description": "사용자 권한 정보 (옵션)",
      "properties": {
        "plan": {
          "type": "string",
          "enum": ["free", "plus", "pro"],
          "description": "구독 플랜"
        },
        "storage_limit": {
          "type": "integer",
          "minimum": 0,
          "description": "프로필 저장 한도"
        },
        "stored": {
          "type": "integer",
          "minimum": 0,
          "description": "현재 저장된 프로필 수"
        },
        "light_daily_left": {
          "type": "integer",
          "minimum": 0,
          "description": "오늘 남은 무료 상담 횟수"
        },
        "deep_tokens": {
          "type": "integer",
          "minimum": 0,
          "description": "보유 딥 상담 토큰"
        }
      }
    },
    "ads_suggest": {
      "type": "object",
      "description": "광고 제안 정보 (옵션)",
      "properties": {
        "eligible": {
          "type": "boolean",
          "description": "광고 시청 자격 여부"
        },
        "cooldown_min": {
          "type": "integer",
          "minimum": 0,
          "description": "광고 재시청까지 남은 시간 (분)"
        }
      }
    }
  },
  "$defs": {
    "Pillar": {
      "type": "object",
      "required": ["stem", "branch", "sexagenary"],
      "properties": {
        "stem": {
          "type": "string",
          "enum": ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"],
          "description": "천간 (10간)"
        },
        "branch": {
          "type": "string",
          "enum": ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"],
          "description": "지지 (12지)"
        },
        "sexagenary": {
          "type": "string",
          "description": "육십갑자 (甲子~癸亥)",
          "pattern": "^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$"
        },
        "stem_ko": { "type": "string" },
        "branch_ko": { "type": "string" },
        "sexagenary_ko": { "type": "string" }
      }
    },
    "TenGodsAnalysis": {
      "type": "object",
      "required": ["by_pillar", "stats"],
      "properties": {
        "by_pillar": {
          "type": "object",
          "properties": {
            "year": { "$ref": "#/$defs/TenGodPair" },
            "month": { "$ref": "#/$defs/TenGodPair" },
            "day": { "$ref": "#/$defs/TenGodPair" },
            "hour": {
              "oneOf": [
                { "$ref": "#/$defs/TenGodPair" },
                { "type": "null" }
              ]
            }
          }
        },
        "stats": {
          "type": "object",
          "required": ["percent"],
          "properties": {
            "percent": {
              "type": "object",
              "description": "십신 분포 백분율",
              "patternProperties": {
                "^(比肩|劫財|食神|傷官|正財|偏財|正官|偏官|正印|偏印)$": {
                  "type": "number",
                  "minimum": 0,
                  "maximum": 100
                }
              }
            }
          }
        }
      }
    },
    "TenGodPair": {
      "type": "object",
      "required": ["heavenly", "earth"],
      "properties": {
        "heavenly": {
          "type": "string",
          "enum": ["比肩", "劫財", "食神", "傷官", "正財", "偏財", "正官", "偏官", "正印", "偏印", "日主"],
          "description": "천간 십신"
        },
        "earth": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["比肩", "劫財", "食神", "傷官", "正財", "偏財", "正官", "偏官", "正印", "偏印"]
          },
          "description": "지지 장간 십신 목록"
        },
        "heavenly_ko": { "type": "string" },
        "earth_ko": { "type": "array", "items": { "type": "string" } }
      }
    },
    "RelationsAnalysis": {
      "type": "object",
      "required": ["heavenly", "earth"],
      "properties": {
        "heavenly": {
          "type": "object",
          "properties": {
            "combine": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "천간 합 (甲己合土 등)"
            },
            "clash": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "천간 충"
            }
          }
        },
        "earth": {
          "type": "object",
          "properties": {
            "he6": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "육합 (子丑合, 寅亥合 등)"
            },
            "sanhe": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "삼합 (申子辰水局 등)"
            },
            "clash": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "지지 충 (子午沖 등)"
            },
            "xing": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "형 (寅巳申, 丑戌未 등)"
            },
            "po": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "파 (子酉破 등)"
            },
            "hai": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "해 (子未害 등)"
            },
            "directional": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "방합 (寅卯辰東方木 등)"
            },
            "yuanjin": {
              "type": "array",
              "items": { "type": "array", "items": { "type": "string" } },
              "description": "원진 (子未, 丑午 등)"
            }
          }
        },
        "extras": {
          "type": "object",
          "properties": {
            "priority_hit": { "type": "string" },
            "transform_to": { "type": "string" },
            "boosts": {
              "type": "array",
              "items": { "type": "object" }
            }
          }
        }
      }
    },
    "VoidAnalysis": {
      "type": "object",
      "properties": {
        "kong_wang": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
          },
          "description": "공망 지지 목록"
        },
        "kong_wang_ko": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },
    "LifeStageAnalysis": {
      "type": "object",
      "description": "12운성 분석",
      "properties": {
        "by_pillar": {
          "type": "object",
          "properties": {
            "year": { "$ref": "#/$defs/LifeStage" },
            "month": { "$ref": "#/$defs/LifeStage" },
            "day": { "$ref": "#/$defs/LifeStage" },
            "hour": {
              "oneOf": [
                { "$ref": "#/$defs/LifeStage" },
                { "type": "null" }
              ]
            }
          }
        }
      }
    },
    "LifeStage": {
      "type": "string",
      "enum": ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絶", "胎", "養"],
      "description": "12운성 단계"
    },
    "ShenshaAnalysis": {
      "type": "object",
      "required": ["enabled"],
      "properties": {
        "enabled": {
          "type": "boolean",
          "description": "신살 분석 활성화 여부"
        },
        "summary": {
          "type": "array",
          "items": { "type": "string" },
          "description": "전체 신살 요약 목록"
        },
        "by_pillar": {
          "type": "object",
          "properties": {
            "year": { "type": "array", "items": { "type": "string" } },
            "month": { "type": "array", "items": { "type": "string" } },
            "day": { "type": "array", "items": { "type": "string" } },
            "hour": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    },
    "StrengthAnalysis": {
      "type": "object",
      "required": ["score", "bucket", "factors"],
      "properties": {
        "score": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "일간 세력 점수 (0~100)"
        },
        "bucket": {
          "type": "string",
          "enum": ["극신강", "신강", "중화", "신약", "극신약"],
          "description": "강약 등급"
        },
        "bucket_ko": { "type": "string" },
        "factors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "name_ko": { "type": "string" },
              "value": { "type": "number" },
              "description": { "type": "string" }
            }
          },
          "description": "세력 계산 요소 상세"
        },
        "details": {
          "type": "object",
          "description": "strength_policy_v2.json 기반 상세 분석",
          "properties": {
            "month_state": { "type": "integer" },
            "branch_root": { "type": "integer" },
            "stem_visible": { "type": "integer" },
            "combo_clash": { "type": "integer" },
            "season_adjust": { "type": "integer" },
            "month_stem_effect": { "type": "integer" },
            "wealth_location_bonus_total": { "type": "number" },
            "total": { "type": "number" },
            "grade_code": { "type": "string" },
            "grade": { "type": "string" }
          }
        }
      }
    },
    "StructureAnalysis": {
      "type": "object",
      "required": ["primary", "status", "score"],
      "properties": {
        "primary": {
          "type": "string",
          "description": "주격국 (예: 정관격, 편관격, 식신격)"
        },
        "primary_ko": { "type": "string" },
        "status": {
          "type": "string",
          "enum": ["성격", "파격", "假格", "uncertain"],
          "description": "격국 상태"
        },
        "status_ko": { "type": "string" },
        "score": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "격국 신뢰도 점수"
        },
        "candidates": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "name_ko": { "type": "string" },
              "score": { "type": "number" }
            }
          },
          "description": "후보 격국 목록"
        }
      }
    },
    "ClimateAnalysis": {
      "type": "object",
      "description": "조후 분석 (계절 기후 조화)",
      "properties": {
        "needs": {
          "type": "array",
          "items": { "type": "string" },
          "description": "필요 오행/간지 (예: [火, 水])"
        },
        "notes": {
          "type": "array",
          "items": { "type": "string" },
          "description": "조후 해석 메모"
        }
      }
    },
    "YongshinAnalysis": {
      "type": "object",
      "description": "용신 분석 (yongshin_policy.json 기반)",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["扶抑", "調候", "通關", "專旺", "從格"],
          "description": "용신 유형"
        },
        "type_ko": { "type": "string" },
        "elements": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["木", "火", "土", "金", "水"]
          },
          "description": "용신 오행 목록"
        },
        "rationale": {
          "type": "string",
          "description": "용신 선정 근거 (객관적 사실 기반)"
        }
      }
    },
    "WuxingAnalysis": {
      "type": "object",
      "required": ["raw"],
      "properties": {
        "raw": {
          "type": "object",
          "required": ["percent"],
          "properties": {
            "percent": {
              "type": "object",
              "required": ["木", "火", "土", "金", "水"],
              "properties": {
                "木": { "type": "number", "minimum": 0, "maximum": 100 },
                "火": { "type": "number", "minimum": 0, "maximum": 100 },
                "土": { "type": "number", "minimum": 0, "maximum": 100 },
                "金": { "type": "number", "minimum": 0, "maximum": 100 },
                "水": { "type": "number", "minimum": 0, "maximum": 100 }
              },
              "description": "원시 오행 분포 (합 100%)"
            }
          }
        },
        "adjusted": {
          "type": "object",
          "description": "합충형파해 보정 후 분포 (옵션)",
          "properties": {
            "percent": {
              "type": "object",
              "properties": {
                "木": { "type": "number" },
                "火": { "type": "number" },
                "土": { "type": "number" },
                "金": { "type": "number" },
                "水": { "type": "number" }
              }
            }
          }
        },
        "status_tag": {
          "type": "object",
          "description": "오행별 상태 태그",
          "patternProperties": {
            "^(木|火|土|金|水)$": {
              "type": "string",
              "enum": ["過旺", "旺", "平", "弱", "缺"]
            }
          }
        }
      }
    },
    "LuckAnalysis": {
      "type": "object",
      "required": ["decades"],
      "properties": {
        "decades": {
          "type": "object",
          "required": ["start_age", "direction"],
          "properties": {
            "start_age": {
              "type": "number",
              "minimum": 0,
              "maximum": 20,
              "description": "대운 시작 나이 (0~20세)"
            },
            "direction": {
              "type": "string",
              "enum": ["forward", "reverse"],
              "description": "대운 순역 방향"
            },
            "direction_ko": { "type": "string" },
            "pillars": {
              "type": "array",
              "items": { "$ref": "#/$defs/Pillar" },
              "description": "대운 기둥 목록 (10년 단위)"
            }
          }
        },
        "years": {
          "type": "object",
          "description": "연운 분석 (YYYY 키)",
          "patternProperties": {
            "^(19|20|21)\\d{2}$": {
              "type": "object",
              "properties": {
                "pillar": { "$ref": "#/$defs/Pillar" },
                "score": { "type": "number" },
                "tags": { "type": "array", "items": { "type": "string" } }
              }
            }
          }
        },
        "months": {
          "type": "object",
          "description": "월운 분석 (YYYY-MM 키)",
          "patternProperties": {
            "^(19|20|21)\\d{2}-(0[1-9]|1[0-2])$": {
              "type": "object",
              "properties": {
                "pillar": { "$ref": "#/$defs/Pillar" },
                "good_days": { "type": "array", "items": { "type": "integer" } },
                "caution_days": { "type": "array", "items": { "type": "integer" } }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 샘플 응답 A (정상 시나리오)

```json
{
  "meta": {
    "name": "김사주",
    "gender": "male",
    "school_profile": "徐樂吾",
    "school_profile_ko": "서락오파",
    "signatures": {
      "sha256": "3a7bd3e2360a3d29eea436fcfb7e44c728d239f9f78caf42aac6a1c0bd4e2e9a"
    }
  },
  "time": {
    "timezone": "Asia/Seoul",
    "dst": false,
    "utc": "2000-09-14T01:00:00Z",
    "lmt": "2000-09-14T09:28:00+09:00",
    "regional_correction_minutes": 0,
    "solar_time": "2000-09-14T10:00:00+09:00",
    "evidence": {
      "solar_term_prev": "白露",
      "solar_term_next": "秋分",
      "zi_transition": false,
      "zi_hour_mode": "default"
    }
  },
  "pillars": {
    "year": {
      "stem": "庚",
      "branch": "辰",
      "sexagenary": "庚辰",
      "stem_ko": "경",
      "branch_ko": "진",
      "sexagenary_ko": "경진"
    },
    "month": {
      "stem": "乙",
      "branch": "酉",
      "sexagenary": "乙酉",
      "stem_ko": "을",
      "branch_ko": "유",
      "sexagenary_ko": "을유"
    },
    "day": {
      "stem": "乙",
      "branch": "亥",
      "sexagenary": "乙亥",
      "stem_ko": "을",
      "branch_ko": "해",
      "sexagenary_ko": "을해"
    },
    "hour": {
      "stem": "辛",
      "branch": "巳",
      "sexagenary": "辛巳",
      "stem_ko": "신",
      "branch_ko": "사",
      "sexagenary_ko": "신사"
    },
    "meta": {
      "unknown_hour": false,
      "zi_hour_mode": "default"
    }
  },
  "analysis": {
    "ten_gods": {
      "by_pillar": {
        "year": {
          "heavenly": "偏官",
          "earth": ["偏財", "劫財", "偏印"],
          "heavenly_ko": "편관",
          "earth_ko": ["편재", "겁재", "편인"]
        },
        "month": {
          "heavenly": "比肩",
          "earth": ["偏官"],
          "heavenly_ko": "비견",
          "earth_ko": ["편관"]
        },
        "day": {
          "heavenly": "日主",
          "earth": ["正印", "劫財"],
          "heavenly_ko": "일주",
          "earth_ko": ["정인", "겁재"]
        },
        "hour": {
          "heavenly": "正官",
          "earth": ["傷官", "正官"],
          "heavenly_ko": "정관",
          "earth_ko": ["상관", "정관"]
        }
      },
      "stats": {
        "percent": {
          "比肩": 12.5,
          "劫財": 25.0,
          "食神": 0.0,
          "傷官": 12.5,
          "正財": 0.0,
          "偏財": 12.5,
          "正官": 12.5,
          "偏官": 12.5,
          "正印": 12.5,
          "偏印": 0.0
        }
      }
    },
    "relations": {
      "heavenly": {
        "combine": [],
        "clash": []
      },
      "earth": {
        "he6": [["辰", "酉"]],
        "sanhe": [],
        "clash": [["巳", "亥"]],
        "xing": [],
        "po": [],
        "hai": [],
        "directional": [],
        "yuanjin": []
      },
      "extras": {
        "priority_hit": "he6",
        "transform_to": "金",
        "boosts": [
          {
            "type": "he6_辰酉",
            "element": "金",
            "boost_percent": 15
          }
        ]
      }
    },
    "void": {
      "kong_wang": ["戌", "亥"],
      "kong_wang_ko": ["술", "해"]
    },
    "life_stage": {
      "by_pillar": {
        "year": "墓",
        "month": "死",
        "day": "帝旺",
        "hour": "病"
      }
    },
    "shensha": {
      "enabled": true,
      "summary": [
        "天乙貴人:巳",
        "文昌貴人:巳",
        "驛馬:亥",
        "桃花:午",
        "華蓋:辰"
      ],
      "by_pillar": {
        "year": ["華蓋"],
        "month": [],
        "day": ["驛馬"],
        "hour": ["天乙貴人", "文昌貴人"]
      }
    },
    "strength": {
      "score": 42.5,
      "bucket": "신약",
      "bucket_ko": "신약",
      "factors": [
        {
          "name": "month_state",
          "name_ko": "월지 왕상휴수사",
          "value": -20,
          "description": "乙木 at 酉月 = 死 (-20점)"
        },
        {
          "name": "branch_root",
          "name_ko": "지지 통근",
          "value": 15,
          "description": "亥水 정인 통근 (+15점)"
        },
        {
          "name": "stem_visible",
          "name_ko": "천간 투출",
          "value": 10,
          "description": "월간 乙 비견 (+10점)"
        },
        {
          "name": "combo_clash",
          "name_ko": "합충형파해",
          "value": -5,
          "description": "巳亥沖 (-5점)"
        }
      ],
      "details": {
        "month_state": -20,
        "branch_root": 15,
        "stem_visible": 10,
        "combo_clash": -5,
        "season_adjust": 0,
        "month_stem_effect": 10,
        "wealth_location_bonus_total": 2.5,
        "total": 42.5,
        "grade_code": "신약",
        "grade": "신약"
      }
    },
    "structure": {
      "primary": "정관격",
      "primary_ko": "정관격",
      "status": "성격",
      "status_ko": "성격",
      "score": 78.3,
      "candidates": [
        {
          "name": "정관격",
          "name_ko": "정관격",
          "score": 78.3
        },
        {
          "name": "편관격",
          "name_ko": "편관격",
          "score": 65.2
        },
        {
          "name": "인수격",
          "name_ko": "인수격",
          "score": 54.8
        }
      ]
    },
    "climate": {
      "needs": ["火", "水"],
      "notes": [
        "秋月乙木: 金旺木死, 조후용신 火暖局 필요",
        "亥水 투출시 丙火 필수"
      ]
    },
    "yongshin": {
      "type": "扶抑",
      "type_ko": "부억용신",
      "elements": ["水", "火"],
      "rationale": "일간 신약, 정인(水) 생신, 조후 火 필요"
    },
    "wuxing": {
      "raw": {
        "percent": {
          "木": 25.0,
          "火": 12.5,
          "土": 12.5,
          "金": 37.5,
          "水": 12.5
        }
      },
      "adjusted": {
        "percent": {
          "木": 22.0,
          "火": 10.0,
          "土": 10.0,
          "金": 45.0,
          "水": 13.0
        }
      },
      "status_tag": {
        "木": "平",
        "火": "弱",
        "土": "弱",
        "金": "旺",
        "水": "弱"
      }
    },
    "luck": {
      "decades": {
        "start_age": 7.98,
        "direction": "reverse",
        "direction_ko": "역행",
        "pillars": [
          {
            "stem": "甲",
            "branch": "申",
            "sexagenary": "甲申",
            "stem_ko": "갑",
            "branch_ko": "신",
            "sexagenary_ko": "갑신"
          },
          {
            "stem": "癸",
            "branch": "未",
            "sexagenary": "癸未",
            "stem_ko": "계",
            "branch_ko": "미",
            "sexagenary_ko": "계미"
          },
          {
            "stem": "壬",
            "branch": "午",
            "sexagenary": "壬午",
            "stem_ko": "임",
            "branch_ko": "오",
            "sexagenary_ko": "임오"
          }
        ]
      },
      "years": {
        "2025": {
          "pillar": {
            "stem": "乙",
            "branch": "巳",
            "sexagenary": "乙巳"
          },
          "score": 68.5,
          "tags": ["比肩年", "巳亥沖"]
        }
      },
      "months": {
        "2025-10": {
          "pillar": {
            "stem": "丙",
            "branch": "戌",
            "sexagenary": "丙戌"
          },
          "good_days": [3, 8, 13, 18, 23, 28],
          "caution_days": [5, 14, 19, 27]
        }
      }
    }
  },
  "localization": {
    "ko": true,
    "enrichment": {
      "mappings_count": 141,
      "locale": "ko",
      "enricher_version": "1.0.0"
    }
  },
  "evidence": {
    "policies_applied": [
      "strength_policy_v2.json",
      "relation_policy.json",
      "shensha_v2_policy.json",
      "gyeokguk_policy.json",
      "yongshin_policy.json",
      "branch_tengods_policy.json",
      "sixty_jiazi.json",
      "localization_ko_v1.json"
    ],
    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
    "inputs_hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
  },
  "entitlements": {
    "plan": "free",
    "storage_limit": 3,
    "stored": 1,
    "light_daily_left": 2,
    "deep_tokens": 0
  }
}
```

---

## 샘플 응답 B (엣지 시나리오: 시간 미상 + split_23 + 지역 보정)

```json
{
  "meta": {
    "name": "이시미",
    "gender": "female",
    "school_profile": "韋千里",
    "school_profile_ko": "위천리파",
    "signatures": {
      "sha256": "8b4f2c6a1d7e9f3b5a2c8d1e4f6a9b3c7d2e5f8a1b4c7d9e2f5a8b1c4d7e9f2a"
    }
  },
  "time": {
    "timezone": "Asia/Seoul",
    "dst": false,
    "utc": "1985-12-25T14:30:00Z",
    "lmt": "1985-12-25T22:58:00+09:00",
    "regional_correction_minutes": -32,
    "solar_time": "1985-12-25T23:30:00+09:00",
    "evidence": {
      "solar_term_prev": "大雪",
      "solar_term_next": "冬至",
      "zi_transition": true,
      "zi_hour_mode": "split_23"
    }
  },
  "pillars": {
    "year": {
      "stem": "乙",
      "branch": "丑",
      "sexagenary": "乙丑",
      "stem_ko": "을",
      "branch_ko": "축",
      "sexagenary_ko": "을축"
    },
    "month": {
      "stem": "戊",
      "branch": "子",
      "sexagenary": "戊子",
      "stem_ko": "무",
      "branch_ko": "자",
      "sexagenary_ko": "무자"
    },
    "day": {
      "stem": "癸",
      "branch": "巳",
      "sexagenary": "癸巳",
      "stem_ko": "계",
      "branch_ko": "사",
      "sexagenary_ko": "계사"
    },
    "hour": null,
    "meta": {
      "unknown_hour": true,
      "zi_hour_mode": "split_23"
    }
  },
  "analysis": {
    "ten_gods": {
      "by_pillar": {
        "year": {
          "heavenly": "偏印",
          "earth": ["正財", "偏官", "偏印"],
          "heavenly_ko": "편인",
          "earth_ko": ["정재", "편관", "편인"]
        },
        "month": {
          "heavenly": "正財",
          "earth": ["劫財"],
          "heavenly_ko": "정재",
          "earth_ko": ["겁재"]
        },
        "day": {
          "heavenly": "日主",
          "earth": ["傷官", "正官"],
          "heavenly_ko": "일주",
          "earth_ko": ["상관", "정관"]
        },
        "hour": null
      },
      "stats": {
        "percent": {
          "比肩": 0.0,
          "劫財": 16.7,
          "食神": 0.0,
          "傷官": 16.7,
          "正財": 33.3,
          "偏財": 0.0,
          "正官": 16.7,
          "偏官": 16.7,
          "正印": 0.0,
          "偏印": 0.0
        }
      }
    },
    "relations": {
      "heavenly": {
        "combine": [],
        "clash": []
      },
      "earth": {
        "he6": [["丑", "子"]],
        "sanhe": [],
        "clash": [["巳", "亥"]],
        "xing": [],
        "po": [],
        "hai": [["丑", "午"]],
        "directional": [],
        "yuanjin": [["子", "未"]]
      },
      "extras": {
        "priority_hit": "he6",
        "transform_to": "土",
        "boosts": []
      }
    },
    "void": {
      "kong_wang": ["戌", "亥"],
      "kong_wang_ko": ["술", "해"]
    },
    "life_stage": {
      "by_pillar": {
        "year": "養",
        "month": "胎",
        "day": "長生",
        "hour": null
      }
    },
    "shensha": {
      "enabled": true,
      "summary": [
        "天乙貴人:丑",
        "太極貴人:子",
        "學堂:巳",
        "金輿:丑"
      ],
      "by_pillar": {
        "year": ["天乙貴人", "金輿"],
        "month": ["太極貴人"],
        "day": ["學堂"],
        "hour": []
      }
    },
    "strength": {
      "score": 58.0,
      "bucket": "중화",
      "bucket_ko": "중화",
      "factors": [
        {
          "name": "month_state",
          "name_ko": "월지 왕상휴수사",
          "value": 25,
          "description": "癸水 at 子月 = 旺 (+25점)"
        },
        {
          "name": "branch_root",
          "name_ko": "지지 통근",
          "value": 20,
          "description": "子水 강력 통근 (+20점)"
        },
        {
          "name": "stem_visible",
          "name_ko": "천간 투출",
          "value": 0,
          "description": "비겁 투출 없음"
        },
        {
          "name": "combo_clash",
          "name_ko": "합충형파해",
          "value": -10,
          "description": "丑子合 재성 강화 (-10점)"
        }
      ],
      "details": {
        "month_state": 25,
        "branch_root": 20,
        "stem_visible": 0,
        "combo_clash": -10,
        "season_adjust": 5,
        "month_stem_effect": -5,
        "wealth_location_bonus_total": 8.0,
        "total": 58.0,
        "grade_code": "중화",
        "grade": "중화"
      }
    },
    "structure": {
      "primary": "재격",
      "primary_ko": "재격",
      "status": "성격",
      "status_ko": "성격",
      "score": 82.1,
      "candidates": [
        {
          "name": "재격",
          "name_ko": "재격",
          "score": 82.1
        },
        {
          "name": "상관생재격",
          "name_ko": "상관생재격",
          "score": 71.5
        }
      ]
    },
    "climate": {
      "needs": ["火"],
      "notes": [
        "冬月癸水: 水旺需火暖局",
        "戊土透干 + 火調候 = 最佳配置"
      ]
    },
    "yongshin": {
      "type": "調候",
      "type_ko": "조후용신",
      "elements": ["火"],
      "rationale": "동월 계수, 조후용신 화 필수"
    },
    "wuxing": {
      "raw": {
        "percent": {
          "木": 16.7,
          "火": 16.7,
          "土": 33.3,
          "金": 16.7,
          "水": 16.7
        }
      },
      "status_tag": {
        "木": "平",
        "火": "弱",
        "土": "旺",
        "金": "平",
        "水": "旺"
      }
    },
    "luck": {
      "decades": {
        "start_age": 3.42,
        "direction": "forward",
        "direction_ko": "순행",
        "pillars": [
          {
            "stem": "己",
            "branch": "丑",
            "sexagenary": "己丑",
            "stem_ko": "기",
            "branch_ko": "축",
            "sexagenary_ko": "기축"
          },
          {
            "stem": "庚",
            "branch": "寅",
            "sexagenary": "庚寅",
            "stem_ko": "경",
            "branch_ko": "인",
            "sexagenary_ko": "경인"
          },
          {
            "stem": "辛",
            "branch": "卯",
            "sexagenary": "辛卯",
            "stem_ko": "신",
            "branch_ko": "묘",
            "sexagenary_ko": "신묘"
          }
        ]
      }
    }
  },
  "localization": {
    "ko": true,
    "enrichment": {
      "mappings_count": 141,
      "locale": "ko",
      "enricher_version": "1.0.0"
    }
  },
  "evidence": {
    "policies_applied": [
      "strength_policy_v2.json",
      "relation_policy.json",
      "shensha_v2_policy.json",
      "gyeokguk_policy.json",
      "yongshin_policy.json",
      "branch_tengods_policy.json",
      "sixty_jiazi.json",
      "localization_ko_v1.json"
    ],
    "trace_id": "7c9e6679-7425-40de-944b-e07f1b45c113",
    "inputs_hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
  },
  "entitlements": {
    "plan": "plus",
    "storage_limit": 10,
    "stored": 5,
    "light_daily_left": 0,
    "deep_tokens": 3
  },
  "ads_suggest": {
    "eligible": true,
    "cooldown_min": 0
  }
}
```

---

## 검증 힌트

**ajv/jsonschema 검증 시 주의점:**

1. **patternProperties 키 검증** (`luck.years`, `luck.months`)
   - `years` 키: `^(19|20|21)\d{2}$` 패턴 (1900~2199)
   - `months` 키: `^(19|20|21)\d{2}-(0[1-9]|1[0-2])$` 패턴
   - 동적 키이므로 additionalProperties 허용 필요

2. **oneOf 분기** (`pillars.hour`, `life_stage.by_pillar.hour`)
   - `unknown_hour:true`인 경우 `null` 허용
   - 스키마 검증기가 oneOf 조건을 정확히 처리하는지 확인

3. **enum 완전성**
   - 10간/12지/십신/12운성: 전체 값 포함됨
   - 60갑자: pattern으로 검증 (enum 60개는 과다하므로 정규식 사용)

4. **합계 검증** (`wuxing.raw.percent`)
   - JSON Schema 자체로는 5개 값 합=100 강제 불가
   - 애플리케이션 레벨에서 추가 검증 필요:
     ```python
     total = sum(wuxing["raw"]["percent"].values())
     assert 99.9 <= total <= 100.1  # 부동소수점 오차 허용
     ```

5. **RFC-8785 canonical JSON**
   - signatures.sha256 검증은 별도 로직:
     ```python
     canonical = canonicalize(response)  # RFC-8785
     computed_hash = hashlib.sha256(canonical).hexdigest()
     assert computed_hash == response["meta"]["signatures"]["sha256"]
     ```

6. **ISO8601 format 검증**
   - `"format": "date-time"` 키워드 사용
   - 일부 검증기는 format validation을 옵션으로 처리 (활성화 필요)

7. **$defs 참조 해결**
   - JSON Schema draft-2020-12의 `$defs` 키워드 지원 확인
   - 구버전 검증기는 `definitions` 사용 (호환성 주의)

**검증 예시 (Python jsonschema):**
```python
from jsonschema import validate, Draft202012Validator
import json

with open("schema.json") as f:
    schema = json.load(f)
with open("sample_a.json") as f:
    sample_a = json.load(f)

validator = Draft202012Validator(schema)
validator.validate(sample_a)  # 오류 없으면 통과
```

**추가 검증 레이어:**
- Policy 파일 기반 검증 (strength_policy_v2.json 등)
- LLM Guard v1.0 규칙 적용 (EVIDENCE_BOUND, POLICY_BOUND)
- Cross-field 로직 (예: gender + year_stem → luck.decades.direction 일치 확인)
