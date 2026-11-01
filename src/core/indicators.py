"""Official six-indicator framework (Port Said housing redevelopment priority).

This module defines the immutable BASELINE weights/rubrics. They are copied into
each new Study's IndicatorConfig rows, where they may be freely edited per-study
(scenario weights, rubric tuning) without ever changing this baseline definition
("the original official indicator weights must remain available as an unchanged
baseline" per the spec).

Missing or unclear source data remain unscored; no value is silently inferred.
"""
from __future__ import annotations

OFFICIAL_INDICATORS = [
    {
        "code": "structural",
        "name_ar": "الحالة الإنشائية والعامة للمباني",
        "name_en": "Structural and General Building Condition",
        "weight": 35,
        "normalization_method": "category_map",
        "always_provisional": False,
        "source_columns": ["الحالة_العامة_للمبني"],
        "rubric": {
            "map": {
                "متوسط": 50,
                "رديء": 75,
                "ردئ": 75,
                "ردىء": 75,
                "متهالك": 90,
                "ردئ ومتهالك": 100,
                "ردىء ومتهالك": 100,
            },
            "default_if_unmapped": None,
        },
        "description": (
            "مبني على تصنيف الحالة العامة للمبنى (متوسط/ردئ/متهالك/ردئ ومتهالك). "
            "قرارات الترميم/الإزالة الرسمية تُعرض كتنبيه سلامة منفصل ولا تُدمج في هذا المؤشر."
        ),
    },
    {
        "code": "strategic",
        "name_ar": "الأهمية الاستراتيجية للموقع",
        "name_en": "Strategic Importance",
        "weight": 20,
        "normalization_method": "linear_scale",
        "always_provisional": False,
        "source_columns": ["الأهميه الأستراتيجيه"],
        "rubric": {"max_raw": 15},
        "description": (
            "قيمة خام من 0 إلى 15 كما وردت في المصدر، تُحوَّل خطيًا إلى 0-100. "
            "السجلات بلا قيمة تُعرض كبيانات ناقصة ولا تُستبدل بصفر."
        ),
    },
    {
        "code": "age",
        "name_ar": "العمر الزمني للمباني",
        "name_en": "Building Age",
        "weight": 15,
        "normalization_method": "threshold_bands",
        "always_provisional": False,
        "source_columns": ["سنة_الانشاء"],
        "rubric": {
            "reference_year": 2026,
            "bands": [
                {"min": 0, "max": 20, "score": 20},
                {"min": 20, "max": 40, "score": 50},
                {"min": 40, "max": 60, "score": 75},
                {"min": 60, "max": 1000, "score": 100},
            ],
        },
        "description": (
            "العمر = 2026 - سنة الإنشاء. الفئات: أقل من 20 سنة = 20/100؛ "
            "20 إلى أقل من 40 = 50؛ 40 إلى أقل من 60 = 75؛ 60 سنة فأكثر = 100."
        ),
    },
    {
        "code": "density",
        "name_ar": "حجم المخزون السكني والكثافة العمرانية",
        "name_en": "Housing Stock and Urban Density",
        "weight": 10,
        "normalization_method": "density_ratio",
        "always_provisional": False,
        "source_columns": ["عدد_الوحدات", "عدد_العمارات", "المساحة_بالفدان"],
        "rubric": {"ratio": "units_per_feddan", "mode": "minmax"},
        "description": (
            "الكثافة = عدد الوحدات السكنية / مساحة المشروع بالفدان فقط. "
            "تُطبَّع بمقياس أدنى-أعلى داخل مجموعة المشروعات الثلاثين؛ لا يُستبدل عدد الوحدات بعدد العمارات."
        ),
    },
    {
        "code": "modifications",
        "name_ar": "التعديلات والإضافات غير المعتمدة",
        "name_en": "Modifications & Extensions (extent, authorization unverified)",
        "weight": 10,
        "normalization_method": "modification_extent",
        "always_provisional": True,
        "source_columns": ["الامتدادات_بالعمارات", "نوع_الامتدادات", "هل_حدث_تغيير_في_استخدام_الدور_الارضي"],
        "rubric": {
            "presence_map": {"يوجد": 100, "لا يوجد": 0},
        },
        "description": (
            "يوجد امتدادات = 100/100؛ لا يوجد = 0/100؛ المفقود أو غير الواضح لا يُحتسب. "
            "وجود امتداد لا يثبت وحده أنه غير معتمد قانونيًا؛ التقييم مبدئي."
        ),
    },
    {
        "code": "infrastructure",
        "name_ar": "حالة المرافق والبنية الأساسية",
        "name_en": "Infrastructure and Basic Services",
        "weight": 10,
        "normalization_method": "infrastructure_ratio",
        "always_provisional": True,
        "source_columns": [
            "اتصال_المشروع_بالكهرباء", "اتصال_المشروع_بالمياه",
            "اتصال_المشروع_بالصرف_الصحي", "اتصال_المشروع_بالغاز",
        ],
        "rubric": {"connected_values": ["متصل"], "utilities": 4},
        "description": (
            "نسبة المرافق المتصلة (كهرباء/مياه/صرف/غاز) من أصل 4. "
            "الاتصال لا يعادل جودة الخدمة أو كفاءتها؛ دائمًا 'مبدئي'."
        ),
    },
]

TOTAL_OFFICIAL_WEIGHT = sum(i["weight"] for i in OFFICIAL_INDICATORS)
assert TOTAL_OFFICIAL_WEIGHT == 100

CRITICAL_DECISION_KEYWORDS = {
    "ازالة": "critical",
    "إزالة": "critical",
    "ترميم وإزالة": "critical",
    "ترميم وازالة": "critical",
    "ترميم": "warning",
}

DEFAULT_STUDY_SETTINGS = {
    "dominant_indicator_min_weight": 30,  # indicator at/above this weight is "dominant"; missing it -> Insufficient Data
    "validated_completeness_threshold": 90,
    "provisional_completeness_threshold": 60,
}
