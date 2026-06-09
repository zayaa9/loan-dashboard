"""
config.py — Бүх тогтмол утга, багана нэр, өнгийн тохиргоо
"""

# ── Column names ──────────────────────────────────────────────────────────────
COL_CUST    = "cust_code"
COL_DATE    = "adv_date"
COL_AMT     = "adv_amt"
COL_STATUS1 = "status_1"
COL_STATUS  = "status"
COL_SCORE   = "total_score"
COL_IS_OD   = "is_overdue"
COL_MAX_OD  = "max_overdue_day"
COL_ACT_OD  = "active_overdue"
COL_MAX_AOD = "max_active_overdue_day"

# ── Bucket bins & labels ──────────────────────────────────────────────────────
BUCKET_BINS = [-1, 0, 1, 5, 10, 15, 30, 9999]
BUCKET_LBLS = ["0", "1", "2–5", "6–10", "11–15", "16–30", "30+"]

BUCKET_COLORS = {
    "0":     "#1d9e75",
    "1":     "#84cc16",
    "2–5":   "#f59e0b",
    "6–10":  "#f97316",
    "11–15": "#ef4444",
    "16–30": "#dc2626",
    "30+":   "#7f1d1d",
}

# ── Status colors ─────────────────────────────────────────────────────────────
CLR_STATUS = {
    "O_active": "#e24b4a",
    "O_max":    "#f59e0b",
    "C":        "#1d9e75",
}
CLR_BUCKET = ["#1d9e75","#84cc16","#f59e0b","#f97316","#ef4444","#dc2626","#7f1d1d"]

# ── Customer attribute columns ────────────────────────────────────────────────
CUST_ATTRS = [
    "age","gender","marital_status","edu_name","location",
    "has_ios","is_bio_login","fin_score","psy_score",
    "total_score_sr","slry_last_amt","slry_last_avg_6m",
    "zms_active_ln_cnt","is_device_remember","zms_monthly_payment",
    "slry_last_row_cnt_24m","slry_has_cont_salary_3m",
    "zms_closed_ln_total_amount","has_active_overdue_loan",
]

# ── Score columns ─────────────────────────────────────────────────────────────
SCORE_COLS = {
    "total_score":    "Нийт оноо",
    "fin_score":      "Санхүүгийн оноо",
    "psy_score":      "Сэтгэл зүйн оноо",
    "total_score_sr": "Нийт оноо (SR)",
}

# ── Numeric columns for correlation ──────────────────────────────────────────
CORR_COLS = {
   # ── Демографи ────────────────────────────────────────────────────────────
    "age":                        "Нас",

    # ── Оноо ─────────────────────────────────────────────────────────────────
    "fin_score":                  "Санхүүгийн оноо",
    "psy_score":                  "Сэтгэл зүйн оноо",
    "total_score":                "Нийт оноо",
    # "avg_score":                  "Дундаж оноо",
    # "max_score":                  "Хамгийн өндөр оноо",
    # "min_score":                  "Хамгийн бага оноо",

    # ── Зээлийн тоо & дүн ────────────────────────────────────────────────────
    # "total_loan_cnt":             "Нийт зээлийн тоо",
    # "overdue_loan_cnt":           "Хэтэрсэн зээлийн тоо",
    # "closed_cnt":                 "Хаалттай зээлийн тоо (C)",
    # "o_max_cnt":                  "O_max зээлийн тоо",
    # "o_active_cnt":               "O_active зээлийн тоо",
    # "total_loan_amt":             "Нийт зээлийн дүн",
    # "avg_loan_amt":               "Дундаж зээлийн дүн",
    # "max_loan_amt":               "Хамгийн их зээлийн дүн",
    # "max_calc_lmt":               "Зээлийн хязгаар",

    # ── ZMS зээлийн мэдээлэл ─────────────────────────────────────────────────
    "zms_active_ln_cnt":          "Нээлттэй зээлийн тоо (ZMS)",
    "zms_closed_ln_total_amount": "Хаагдсан зээлийн нийт дүн",

    # ── Сарын төлбөр ─────────────────────────────────────────────────────────
    # "total_monthly_payment":      "Сарын нийт төлбөр",
    # "avg_monthly_payment":        "Дундаж сарын төлбөр",
    "zms_monthly_payment":        "Сарын зээлийн төлбөр",

    # ── Цалин ────────────────────────────────────────────────────────────────
    "slry_last_amt":              "Сүүлийн цалин",
    "slry_last_avg_6m":           "Цалингийн 6с дундаж",
    "slry_last_row_cnt_24m":      "Цалингийн бичилт (24с)",
    "slry_has_cont_salary_3m":    "Тасралтгүй цалин 3 сар (1/0)",

    # ── Харьцаа & Тооцоолсон ─────────────────────────────────────────────────
    "dti_ratio":                  "DTI харьцаа (төлбөр/цалин)",
    "loan_to_salary_ratio":       "Зээл/Цалин харьцаа",
}

# ── Category pairs for overdue analysis ──────────────────────────────────────
CATEGORY_PAIRS = [
    ("marital_label",   "Гэрлэлтийн байдал"),
    ("edu_name",        "Боловсролын түвшин"),
    ("age_group",       "Насны бүлэг"),
    ("ios_label",       "Төхөөрөмж (iOS / Android)"),
    ("bio_label",       "Биометр нэвтрэлт"),
    ("dev_label",       "Төхөөрөмж санасан эсэх"),
    ("slry_cont_label", "Цалингийн тасралтгүй байдал"),
    ("location_type",   "Байршил (УБ / Орон нутаг)"),
    ("gender_label",    "Жендэр"),
]

# ── All customer-level column display map ─────────────────────────────────────
CUST_DISPLAY_COLS = {
    COL_CUST:                    "Харилцагчийн код",
    "age":                       "Нас",
    "age_group":                 "Насны бүлэг",
    "gender_label":              "Жендэр",
    "marital_label":             "Гэрлэлтийн байдал",
    "edu_name":                  "Боловсрол",
    "location":                  "Байршил",
    "location_type":             "Байршлын төрөл",
    "is_bio_login":              "Биометр нэвтрэлт",
    "bio_label":                 "Биометр (label)",
    "has_ios":                   "iOS хэрэглэгч",
    "ios_label":                 "iOS (label)",
    "is_device_remember":        "Төхөөрөмж санасан",
    "total_loan_cnt":            "Нийт зээлийн тоо",
    "closed_cnt":                "Хаалттай (C)",
    "o_max_cnt":                 "O_max тоо",
    "o_active_cnt":              "O_active тоо",
    "overdue_loan_cnt":          "Хэтэрсэн зээлийн тоо",
    "status2":                   "O_active байсан уу (1/0)",
    "overdue_status":            "Хэтрэлтийн байдал",
    "overdue_band":              "Хэтрэлтийн бүс",
    "max_overdue_day":           "MAX хэтрэлт (хоног)",
    "avg_overdue_day":           "Дундаж хэтрэлт (хоног)",
    "has_overdue":               "Хэтрэлттэй эсэх",
    "total_loan_amt":            "Нийт зээлийн дүн (₮)",
    "avg_loan_amt":              "Дундаж зээлийн дүн (₮)",
    "max_loan_amt":              "Хамгийн их зээлийн дүн (₮)",
    "min_loan_amt":              "Хамгийн бага зээлийн дүн (₮)",
    "max_calc_lmt":              "Зээлийн хязгаар (₮)",
    "total_score":               "Нийт оноо",
    "total_score_sr":            "Нийт оноо (SR)",
    "fin_score":                 "Санхүүгийн оноо",
    "psy_score":                 "Сэтгэл зүйн оноо",
    "avg_score":                 "Дундаж оноо",
    "max_score":                 "Хамгийн өндөр оноо",
    "min_score":                 "Хамгийн бага оноо",
    "slry_last_amt":             "Сүүлийн цалин (₮)",
    "slry_last_avg_6m":          "6 сарын дундаж цалин (₮)",
    "slry_last_row_cnt_24m":     "24 сард цалингийн мөрийн тоо",
    "slry_has_cont_salary_3m":   "Тасралтгүй цалин 3 сар (1/0)",
    "slry_cont_label":           "Цалингийн тасралтгүй байдал",
    "zms_monthly_payment":       "Сарын зээлийн төлбөр (₮)",
    "total_monthly_payment":     "Нийт сарын төлбөр (₮)",
    "avg_monthly_payment":       "Дундаж сарын төлбөр (₮)",
    "zms_active_ln_cnt":         "Идэвхтэй зээлийн тоо (ZMS)",
    "zms_closed_ln_total_amount":"Хаагдсан зээлийн нийт дүн (₮)",
    "dti_ratio":                 "DTI (Сарын төлбөр / Цалин)",
    "loan_to_salary_ratio":      "Зээл/Цалин харьцаа",
    "has_active_overdue_loan":   "Идэвхтэй хэтрэлттэй зээл",
}

# ── Plotly base theme ─────────────────────────────────────────────────────────
FONT   = dict(family="Arial,sans-serif", color="#111", size=12)
AXIS   = dict(
    tickfont=dict(color="#111", size=11),
    title_font=dict(color="#444", size=12),
    gridcolor="#f0f0f0",
    linecolor="#ddd",
)
LEGEND = dict(
    font=dict(color="#111", size=11),
    bgcolor="rgba(255,255,255,.95)",
    bordercolor="#ddd",
    borderwidth=1,
)
BASE = dict(
    plot_bgcolor="#fff",
    paper_bgcolor="#fff",
    font=FONT,
    margin=dict(l=10, r=16, t=32, b=8),
    legend=LEGEND,
)
