"""
styles.py — Бүх CSS дашбордын нэг газарт
"""

CSS = """
<style>
/* ── base ── */
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],
[data-testid="stHeader"],.main,.block-container{
    background:#f8f9fb !important; color:#111 !important;}
.block-container{padding-top:1.6rem !important;}

/* ── sidebar ── */
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{
    background:#ffffff !important; border-right:1px solid #e8e8e8;}
[data-testid="stSidebar"] *{color:#111111 !important;}
[data-testid="stSidebar"] .stRadio label{font-size:13px;}
[data-testid="stSidebar"] hr{border-color:#eee;}

/* Input field */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="textarea"] textarea {
    background-color:#ffffff !important;
    color:#111111 !important;
    border:1px solid #cccccc !important;
    border-radius:6px !important;}

/* Selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] {background-color:#ffffff !important;}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color:#ffffff !important; color:#111111 !important;
    border:1px solid #cccccc !important; border-radius:6px !important;}
[data-testid="stSidebar"] [data-baseweb="select"] span {color:#111111 !important;}

/* File uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background-color:#f8f9fb !important;
    border:1px dashed #cccccc !important; border-radius:8px !important;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] * {color:#ffffff !important;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
    background-color:#1a73e8 !important; color:#ffffff !important;
    border:none !important; border-radius:6px !important;}

/* Slider */
[data-testid="stSidebar"] [data-testid="stSlider"] * {color:#111111 !important;}

/* Multiselect */
[data-testid="stSidebar"] [data-baseweb="tag"] {background-color:#e8f0fe !important;}
[data-testid="stSidebar"] [data-baseweb="tag"] span {color:#1a73e8 !important;}

/* Date input */
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background-color:#111111 !important; color:#ffffff !important;}

/* Expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background-color:#f8f9fb !important;
    border:1px solid #e0e0e0 !important; border-radius:8px !important;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {color:#111111 !important;}

/* ── top-level tabs ── */
.stTabs [data-baseweb="tab-list"]{
    gap:4px; background:#fff; border-radius:12px; padding:5px 6px;
    border:1px solid #e4e6ea; box-shadow:0 1px 4px rgba(0,0,0,.06);
    width:fit-content;}
.stTabs [data-baseweb="tab"]{
    border-radius:8px; padding:8px 22px; font-size:14px; font-weight:600;
    color:#555 !important; background:transparent; border:none !important;}
.stTabs [aria-selected="true"]{
    background:#1a73e8 !important; color:#fff !important;
    box-shadow:0 2px 6px rgba(26,115,232,.35);}

/* ── section header ── */
.sh{font-size:13.5px; font-weight:700; color:#222; margin:1.1rem 0 .45rem;
    display:flex; align-items:center; gap:7px;}
.sh::before{content:""; display:inline-block; width:3px; height:14px;
    border-radius:2px; background:#1a73e8; flex-shrink:0;}

/* ── sub-section card ── */
.sub-card{background:#fff; border-radius:12px; border:1px solid #e8eaed;
    padding:16px 18px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,.05);}

/* ── KPI card ── */
[data-testid="stMetric"]{background:#fff !important; border-radius:10px;
    padding:12px 16px !important; border:1px solid #e8eaed;
    box-shadow:0 1px 3px rgba(0,0,0,.04);}
[data-testid="stMetricLabel"] p{color:#666 !important; font-size:12px !important;}
[data-testid="stMetricValue"]{color:#111 !important; font-size:1.5rem !important;}
[data-testid="stMetricDelta"]{font-size:12px !important;}

/* ── info boxes ── */
.box{padding:10px 14px; border-radius:8px; font-size:13px;
     margin-bottom:10px; line-height:1.5;}
.box-blue  {background:#f0f7ff; border-left:3px solid #1a73e8;}
.box-green {background:#f0faf5; border-left:3px solid #1d9e75;}
.box-warn  {background:#fff8e1; border-left:3px solid #f59e0b;}
.box-danger{background:#fff5f5; border-left:3px solid #e24b4a;}

/* ── Customer sub-tabs flex-wrap ── */
.stTabs [data-baseweb="tab-list"]:has([data-baseweb="tab"]:nth-child(5)){
    flex-wrap:wrap !important; background:#f4f6f9 !important;
    border-radius:10px !important; padding:5px 6px !important;
    border:1px solid #e0e2e6 !important; gap:3px !important;
    width:100% !important; box-shadow:0 1px 3px rgba(0,0,0,.06) !important;
    row-gap:5px !important;}
.stTabs [data-baseweb="tab-list"]:has([data-baseweb="tab"]:nth-child(5)) [data-baseweb="tab"]{
    border-radius:7px !important; padding:7px 15px !important;
    font-size:13px !important; font-weight:600 !important;
    color:#555 !important; background:transparent !important;
    border:none !important; flex-shrink:0 !important; min-width:fit-content !important;}
.stTabs [data-baseweb="tab-list"]:has([data-baseweb="tab"]:nth-child(5)) [aria-selected="true"]{
    background:#1a73e8 !important; color:#fff !important;
    box-shadow:0 2px 5px rgba(26,115,232,.3) !important;}

/* ── download button ── */
.stDownloadButton button{
    background:#1a73e8 !important; color:#fff !important;
    border:none; border-radius:8px; font-weight:600;}

/* ── text ── */
h1,h2,h3,h4,h5,h6,p,span,div,label,
.stMarkdown,.stText,[data-testid="stMarkdownContainer"]{color:#111 !important;}

/* ── Dropdown / Selectbox list items ── */
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="listbox"] *,
[data-baseweb="menu"] *,
[data-baseweb="select"] [role="option"] {
    background-color:#ffffff !important;
    color:#111111 !important;}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="menu"] li:hover {
    background-color:#e8f0fe !important;
    color:#1a73e8 !important;}

/* ── Selectbox дотор сонгосон утга ── */
[data-baseweb="select"] [data-testid="stSelectbox"] *,
div[data-baseweb="select"] > div > div {
    color:#111111 !important;
    background-color:#ffffff !important;}

/* ── Multiselect dropdown list ── */
[data-baseweb="popover"] {
    background-color:#ffffff !important;}
[data-baseweb="popover"] * {
    color:#111111 !important;}

/* ── Main area selectbox (tab дотор) ── */
.main [data-baseweb="select"] > div {
    background-color:#ffffff !important;
    color:#111111 !important;
    border:1px solid #cccccc !important;
    border-radius:6px !important;}
.main [data-baseweb="select"] span {
    color:#111111 !important;}
.main [data-baseweb="popover"] [role="option"] {
    background-color:#ffffff !important;
    color:#111111 !important;}

</style>
"""
