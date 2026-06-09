# 📊 Хугацаа хэтрэлтийн шинжилгээний дашборд

Зээлийн хугацаа хэтрэлтийн иж бүрэн дүн шинжилгээний Streamlit дашборд.

---

## 📁 Фолдерийн бүтэц

```
loan_dashboard/
│
├── app.py                    ← Үндсэн entry point
├── requirements.txt          ← Хамаарал
│
├── utils/
│   ├── config.py             ← Тогтмол утга, багана нэр, өнгийн схем
│   ├── preprocess.py         ← Өгөгдөл цэвэрлэх, баяжуулах
│   ├── archive.py            ← Parquet архив (хадгалах/уншах/устгах)
│   ├── charts.py             ← Plotly layout helper, давтагдах chart функц
│   └── export.py             ← Excel/CSV экспорт
│
├── components/
│   └── sidebar.py            ← Sidebar UI + filter хэрэгжүүлэлт
│
├── tabs/
│   ├── tab_loan.py           ← 🏦 Данс түвшний таб (L1–L5)
│   └── tab_customer.py       ← 👤 Харилцагч түвшний таб (C1–C10)
│
├── assets/
│   └── styles.py             ← Бүх CSS нэг файлд
│
└── archive/                  ← Хадгалагдсан parquet + json мета (auto-created)
```

---

## 🚀 Ажиллуулах

```bash
# 1. Хамаарал суулгах
pip install -r requirements.txt

# 2. Дашборд ажиллуулах
streamlit run app.py
```

---

## 📤 Файл оруулах форматын шаардлага

| Багана | Тайлбар |
|--------|---------|
| `cust_code` | Харилцагчийн код |
| `adv_date` | Зээл олгосон огноо |
| `adv_amt` | Зээлийн дүн |
| `status_1` | Зээлийн төлөв (`C` / `O_max` / `O_active`) |
| `max_active_overdue_day` | Идэвхтэй хэтрэлтийн хоног |
| `max_overdue_day` | Нийт хэтрэлтийн хоног (заавал биш) |
| `total_score` | Нийт эрсдэлийн оноо (заавал биш) |

> Заавал байх баганууд: `status_1`, `max_active_overdue_day`

---

## ⚡ Гүйцэтгэлийн оновчлол

| Техник | Тайлбар |
|--------|---------|
| `@st.cache_data` | Preprocess, customer aggregation кэшлэгдэнэ |
| Parquet архив | Хурдан унших/бичих форматыг ашиглана |
| Filter нэг газарт | `apply_filters()` нэг функц — бүх хэсэгт ижил filtered data |
| Модуль задаргаа | Tab тус бүр тусдаа файл — ачаалах хугацаа буурна |

---

## 🔧 Тохиргоо өөрчлөх

- **Багана нэр өөрчлөх** → `utils/config.py` дотор `COL_*` тогтмолуудыг шинэчлэнэ
- **Өнгийн схем** → `utils/config.py` дотор `CLR_STATUS`, `CLR_BUCKET`
- **CSS загвар** → `assets/styles.py`
- **Шинэ категори нэмэх** → `utils/config.py` дотор `CATEGORY_PAIRS` жагсаалтад нэмнэ

---

## 🐛 Нийтлэг алдааны шийдэл

| Алдаа | Шийдэл |
|-------|--------|
| `Дутуу багана` | Upload хийсэн файлд `status_1`, `max_active_overdue_day` байгаа эсэхийг шалгана |
| Categorical dtype алдаа | Sidebar-ийн `🔄 Бүх архивыг дахин боловсруулах` товч дарна |
| Cache хуучирсан | Sidebar-ийн `🗑️ Бүх архив устгах` эсвэл `streamlit cache clear` |
