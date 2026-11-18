"""Theme: page names, status labels, CSS and the brand mark."""
from ui import palettes
HERO_TITLE = "You split the work.<br><em>Don't split the understanding.</em>"
HERO_TEXT = ("BusFactor finds the project decisions only one teammate can explain, sets up peer teaching between "
             "teammates, and checks with a new question that the knowledge really moved.")
PAGES = ["Overview", "1. Project Setup", "2. Private Check", "3. Team Coverage", "4. Teach Each Other",
         "5. Defense Retest", "6. Evidence & Limits"]
PAGE_HINTS = ["Where your team stands", "Key decisions and sources", "Your own questions", "Who can explain what",
              "Peer-teaching missions", "New question, no hints", "Sources, log, limits"]

COVERAGE_PILL = {
    "covered": ("2+ can explain it", "green"),
    "single_point_of_failure": ("Only 1 can explain it", "red"),
    "no_explainer": ("Nobody can explain it yet", "ink"),
    "not_assessed": ("Not assessed", "gray"),
}
CARD_PILL = {"verified": ("Verified", "green"), "proposed": ("Needs review", "amber"),
             "unsupported": ("No source", "red")}
MISSION_PILL = {"proposed": ("Waiting for consent", "amber"), "accepted": ("Accepted", "blue"),
                "completed": ("Retest: try again", "gray"), "verified": ("Confirmed: can explain it", "green"),
                "fallback": ("Ask the TA", "ink")}
EVIDENCE_PILL = {"demonstrated": ("Demonstrated", "green"), "needs_practice": ("Needs practice", "amber"),
                 "insufficient_evidence": ("Not scored: needs human review", "gray")}


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root {
  --bf-bg: #0A0F1F; --bf-surface: #121A33; --bf-fg: #E8EBF7; --bf-muted: #9AA4C7; --bf-line: #243058;
  --bf-accent: #6F88FF; --bf-accent-soft: rgba(111,136,255,.16); --bf-risk: #FF6B61; --bf-ok: #2BD99F; --bf-warn: #F5C46B;
  --bf-display: "Bricolage Grotesque", "IBM Plex Sans", system-ui, sans-serif;
  --bf-body: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --bf-mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
}

/* base */
.stApp { background: var(--bf-bg); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp td, .stApp th {
  font-family: var(--bf-body);
}
.block-container { padding-top: 1.6rem; padding-bottom: 4rem; max-width: 1080px; }
.stApp h1, .stApp h2, .stApp h3 { font-family: var(--bf-display); color: var(--bf-fg); letter-spacing: -0.02em; }
.stApp h1 { font-size: 2.35rem !important; font-weight: 700; line-height: 1.08; padding-bottom: 0.2rem; }
.stApp h2 { font-size: 1.35rem !important; font-weight: 700; }
.stApp h3 { font-size: 1.1rem !important; font-weight: 600; }

/* quiet Streamlit chrome for the demo */
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebarHeader"] { min-height: 0; height: 2.2rem; padding: .3rem .6rem 0; margin: 0; }
[data-testid="stSidebarUserContent"] { padding-top: .2rem; }
.stAppDeployButton, [data-testid="stToolbarActions"], #MainMenu, footer { display: none !important; }

/* sidebar */
[data-testid="stSidebar"] { background: var(--bf-surface); border-right: 1px solid var(--bf-line); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: var(--bf-muted); }
[data-testid="stSidebar"] .stRadio label p { font-weight: 500; }
.bf-brand { display: flex; align-items: center; gap: 10px; font: 700 1.25rem/1 var(--bf-display);
            letter-spacing: -0.01em; color: var(--bf-fg); margin: 0.2rem 0 0.4rem; }
.bf-brand svg { width: 22px; height: 22px; color: var(--bf-fg); }

/* cards = bordered containers */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height] {
  background: var(--bf-surface); border-color: var(--bf-line) !important; border-radius: 12px !important;
}

/* metrics */
[data-testid="stMetricLabel"] p { font: 500 0.72rem/1.3 var(--bf-mono) !important; text-transform: uppercase;
                                  letter-spacing: 0.06em; color: var(--bf-muted); }
[data-testid="stMetricValue"] { font-family: var(--bf-display); font-weight: 700; letter-spacing: -0.02em;
                                font-variant-numeric: tabular-nums; }

/* controls */
.stButton button, .stFormSubmitButton button, .stDownloadButton button { border-radius: 8px; font-weight: 500; }
.stTextArea textarea, .stTextInput input { border-radius: 8px; }
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stExpander"] details { border-radius: 10px; border-color: var(--bf-line); background: var(--bf-surface); }
[data-testid="stDataFrame"] { border: 1px solid var(--bf-line); border-radius: 10px; overflow: hidden; }
button[data-baseweb="tab"] p { font-weight: 500; }
hr { border-color: var(--bf-line) !important; }

/* BusFactor pieces */
div.bf-muted { padding-bottom: 0.35rem; }
.bf-muted { font-size: .92rem !important; }
.bf-pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font: 600 0.74rem/1.3 var(--bf-body);
           white-space: nowrap; }
.bf-green { background: #E5F5EC; color: #17784C; }
.bf-red   { background: #FCEBEA; color: #B3352C; }
.bf-amber { background: #FFF3DF; color: var(--bf-warn); }
.bf-blue  { background: var(--bf-accent-soft); color: var(--bf-accent); }
.bf-gray  { background: #EEF0F4; color: #4A5160; }
.bf-ink   { background: #23272F; color: #FFFFFF; }
.bf-step  { font: 500 0.78rem/1.3 var(--bf-mono); color: var(--bf-muted); text-transform: uppercase;
            letter-spacing: 0.08em; margin-bottom: -0.5rem; }
.bf-sub   { color: var(--bf-muted); font-size: 1.02rem; margin-top: -0.3rem; margin-bottom: 1.4rem; max-width: 46rem; }
.bf-quote { border-left: 2px solid var(--bf-accent); background: var(--bf-bg); padding: 0.65rem 0.95rem;
            border-radius: 0 8px 8px 0; font-size: 0.92rem; margin: 0.4rem 0; }
.bf-muted { color: var(--bf-muted); font-size: 0.86rem; }
.bf-badge { background: #FFF3DF; color: var(--bf-warn); border: 1px solid #F2D29B; border-radius: 10px;
            padding: 0.6rem 0.8rem; font: 600 0.78rem/1.45 var(--bf-body); margin: 0.6rem 0 1rem; }
.bf-badge b { font: 500 0.7rem/1.3 var(--bf-mono); letter-spacing: 0.06em; text-transform: uppercase; display: block; }
.bf-dots  { font-size: 1.1rem; letter-spacing: 0.2em; color: var(--bf-accent); }
.bf-question { background: var(--bf-bg); border: 1px solid var(--bf-line); border-radius: 10px; padding: 1rem 1.2rem;
               font: 500 1.04rem/1.5 var(--bf-body); margin: 0.5rem 0 0.9rem; }
.bf-title { font-weight: 600; font-size: 1.02rem; }

/* ---------- colour + motion ---------- */
@keyframes bf-rise  { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes bf-pulse { 0% { box-shadow: 0 0 0 0 rgba(214,69,59,.5); } 70% { box-shadow: 0 0 0 7px rgba(214,69,59,0); }
                      100% { box-shadow: 0 0 0 0 rgba(214,69,59,0); } }
@keyframes bf-march { to { background-position: 28px 0; } }
@keyframes bf-ring  { from { stroke-dashoffset: var(--from); } to { stroke-dashoffset: var(--to); } }
@keyframes bf-draw  { to { stroke-dashoffset: 0; } }
@keyframes bf-pop   { 0% { transform: scale(.7); opacity: 0; } 60% { transform: scale(1.06); opacity: 1; } 100% { transform: scale(1); } }

[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height] { animation: bf-rise .45s ease both; }

.bf-hero { background: linear-gradient(120deg, #ECF0FF 0%, #F4F7FF 48%, #E8F6EF 100%); border: 1px solid #DCE3F5;
           border-radius: 16px; padding: 18px 24px 22px; margin: 0 0 1.4rem; animation: bf-rise .4s ease both; }
.bf-hero h1 { margin: 1rem 0 .3rem !important; padding: 0 !important; }
.bf-hero p { color: var(--bf-muted); margin: 0; max-width: 46rem; font-size: 1.02rem; }

.bf-stepper { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.bf-st { display: inline-flex; align-items: center; gap: 7px; font: 500 .78rem/1 var(--bf-body); color: var(--bf-muted); white-space: nowrap; }
.bf-st span { width: 22px; height: 22px; border-radius: 50%; display: grid; place-items: center; border: 1.5px solid #C9D0DC;
              background: #fff; font: 600 .68rem/1 var(--bf-mono); }
.bf-st.done span { background: var(--bf-accent-soft); border-color: var(--bf-accent); color: var(--bf-accent); }
.bf-st.now { color: var(--bf-fg); font-weight: 600; }
.bf-st.now span { background: var(--bf-accent); border-color: var(--bf-accent); color: #fff; box-shadow: 0 0 0 4px rgba(47,79,216,.16); }
.bf-stepper i { flex: 1 1 14px; max-width: 46px; height: 2px; border-radius: 2px; background: #D3D9E4; }
.bf-stepper i.done { background: var(--bf-accent); }

.bf-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: currentColor; margin-right: 6px;
          vertical-align: 1px; animation: bf-pulse 1.8s ease-out infinite; }

.bf-av { display: inline-grid; place-items: center; border-radius: 50%; background: var(--c); color: #fff !important; flex: none; line-height: 1;
         font-family: var(--bf-display); font-weight: 700; box-shadow: 0 0 0 3px #fff, 0 0 0 4px var(--c); }
.bf-me { display: flex; gap: 10px; align-items: center; background: var(--bf-bg); border: 1px solid var(--bf-line);
         border-radius: 10px; padding: 9px 11px; margin: -.2rem 0 .9rem; }
.bf-me b { display: block; font-size: .88rem; line-height: 1.3; } .bf-me div > span { display: block; font-size: .74rem; line-height: 1.35; color: var(--bf-muted); }

.bf-ring { position: relative; width: 176px; height: 176px; margin: 0 auto; }
.bf-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.bf-ring .trk { fill: none; stroke: #E5E9F0; stroke-width: 14; }
.bf-ring .val { fill: none; stroke: url(#bfg); stroke-width: 14; stroke-linecap: round;
                animation: bf-ring 1.4s cubic-bezier(.2,.7,.2,1) .25s both; }
.bf-ring .lbl { position: absolute; inset: 0; display: grid; place-content: center; text-align: center; }
.bf-ring .lbl b { font: 700 2.3rem/1 var(--bf-display); letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
.bf-ring .lbl span { font: 500 .7rem/1.4 var(--bf-mono); color: var(--bf-muted); text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }

.bf-dots2 { display: flex; gap: 6px; margin-bottom: 4px; }
.bf-dots2 i { width: 11px; height: 11px; border-radius: 50%; border: 1.5px solid #C5CCD8; }
.bf-dots2.covered i.on { background: var(--bf-ok); border-color: var(--bf-ok); }
.bf-dots2.single_point_of_failure i.on { background: var(--bf-risk); border-color: var(--bf-risk); }

.bf-flow { display: flex; align-items: center; gap: 16px; margin: .5rem 0 .9rem; }
.bf-flow .who { display: flex; align-items: center; gap: 11px; position: relative; }
.bf-flow .who b { display: block; font-size: .95rem; }
.bf-flow .who span { font: 500 .68rem/1.3 var(--bf-mono); color: var(--bf-muted); text-transform: uppercase; letter-spacing: .07em; }
.bf-flow .ck { position: absolute; left: 27px; top: -5px; width: 18px; height: 18px; border-radius: 50%; background: var(--bf-ok);
               color: #fff; font: 700 .64rem/1 var(--bf-body); font-style: normal; display: grid; place-items: center;
               border: 2px solid #fff; animation: bf-pop .4s ease both; }
.bf-flow .arrow { flex: 1 1 60px; min-width: 50px; display: flex; align-items: center; }
.bf-flow .arrow i { flex: 1; height: 2px; background: repeating-linear-gradient(90deg, var(--bf-accent) 0 8px, transparent 8px 14px);
                    background-size: 28px 2px; animation: bf-march .9s linear infinite; }
.bf-flow .arrow::after { content: ""; border-left: 8px solid var(--bf-accent); border-top: 5px solid transparent; border-bottom: 5px solid transparent; }
.bf-flow .arrow.ok i { background: var(--bf-ok); animation: none; }
.bf-flow .arrow.ok::after { border-left-color: var(--bf-ok); }

.bf-win { display: flex; gap: 14px; align-items: center; background: linear-gradient(120deg, #E6F6EE, #EEF4FF);
          border: 1px solid #BFE3CF; border-radius: 12px; padding: 14px 16px; margin: .4rem 0 .6rem; animation: bf-pop .5s ease both; }
.bf-win svg { width: 44px; height: 44px; flex: none; }
.bf-win circle { fill: var(--bf-ok); }
.bf-win path { fill: none; stroke: #fff; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round;
               stroke-dasharray: 40; stroke-dashoffset: 40; animation: bf-draw .6s .35s ease forwards; }
.bf-win b { display: block; font-size: 1rem; } .bf-win span { color: var(--bf-muted); font-size: .9rem; }

/* ---------- dark sidebar ---------- */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0D1430 0%, #121B42 100%); border-right: none; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .bf-brand,
[data-testid="stSidebar"] .bf-me b { color: #E8EBF7 !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p, [data-testid="stSidebar"] .bf-me div > span { color: #8D97BC !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.14); }
[data-testid="stSidebar"] [data-baseweb="select"] * { color: #E8EBF7 !important; }
[data-testid="stSidebar"] .stButton button { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.16); color: #E8EBF7; }
[data-testid="stSidebar"] .stButton button:hover { border-color: #8FA5FF; color: #fff; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.1) !important; }
[data-testid="stSidebar"] .bf-me { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.1); }
[data-testid="stSidebar"] .bf-av { box-shadow: 0 0 0 3px #121B42, 0 0 0 4px var(--c); }
[data-testid="stSidebar"] .bf-brand svg { color: #fff; }
[data-testid="stSidebar"] [role="radiogroup"] label, [data-testid="stSidebar"] [role="radiogroup"] label * { color: #C9D0EA !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { background: transparent !important; border: 1.5px solid #56628F !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) > div:first-child { background: #2F4FD8 !important; border-color: #9DB0FF !important; }
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stCaptionContainer"] * { color: #7E89B1 !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"]:not([data-testid="stCaptionContainer"] *) p { color: #FFFFFF !important; font-weight: 600; }

/* ---------- overview ---------- */
.bf-dark { position: relative; overflow: hidden; border-radius: 18px; padding: 30px 32px 26px; margin-bottom: 1rem; color: #fff;
  background:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 32px 32px,
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 32px 32px,
    radial-gradient(900px 380px at 12% -20%, #2B44B0 0%, rgba(43,68,176,0) 62%),
    radial-gradient(700px 320px at 105% 120%, rgba(30,154,98,.5) 0%, rgba(30,154,98,0) 60%),
    #0A0F1F;
  animation: bf-rise .5s ease both; }
.bf-dark .kicker { font: 500 .74rem/1.4 var(--bf-mono); letter-spacing: .1em; text-transform: uppercase; color: #9FAAD6; }
.bf-dark h1 { color: #FFFFFF !important; font-size: clamp(2rem, 4vw, 3rem) !important; line-height: 1.05 !important;
              margin: .7rem 0 .8rem !important; padding: 0 !important; max-width: 46rem; }
.bf-dark h1 em { font-style: normal; background: linear-gradient(90deg, #93A8FF 0%, #46E0A8 100%);
                 -webkit-background-clip: text; background-clip: text; color: transparent; }
.bf-dark p { color: #B9C1E0; max-width: 40rem; margin: 0 0 1.4rem; font-size: 1.04rem; }
.bf-kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.bf-kpi { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); border-radius: 12px; padding: 14px 16px;
          backdrop-filter: blur(4px); animation: bf-rise .5s ease both; }
.bf-kpi:nth-child(2) { animation-delay: .08s; } .bf-kpi:nth-child(3) { animation-delay: .16s; } .bf-kpi:nth-child(4) { animation-delay: .24s; }
.bf-kpi .k { font: 500 .76rem/1.3 var(--bf-mono); letter-spacing: .08em; text-transform: uppercase; color: #9FAAD6; }
.bf-kpi .v { font: 700 2rem/1.1 var(--bf-display); letter-spacing: -.02em; color: #fff; margin-top: 6px; font-variant-numeric: tabular-nums; }
.bf-kpi .s { font-size: .8rem; color: #8D97BC; margin-top: 2px; }
.bf-kpi .s b { color: #46E0A8; font-weight: 600; }
.bf-kpi .s b.bad { color: #FF8A80; }

.bf-story { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: .4rem 0 1rem; }
.bf-sc { background: var(--bf-surface); border: 1px solid var(--bf-line); border-radius: 12px; padding: 14px 14px 16px;
         animation: bf-rise .45s ease both; min-width: 0; }
.bf-sc:nth-child(2) { animation-delay: .06s; } .bf-sc:nth-child(3) { animation-delay: .12s; }
.bf-sc:nth-child(4) { animation-delay: .18s; } .bf-sc:nth-child(5) { animation-delay: .24s; }
.bf-sc .n { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font: 600 .72rem/1 var(--bf-mono);
            border: 1.5px solid #C9D0DC; color: var(--bf-muted); background: #fff; }
.bf-sc.done .n { background: var(--bf-ok); border-color: var(--bf-ok); color: #fff; }
.bf-sc.next { border-color: var(--bf-accent); animation: bf-rise .45s ease both, bf-glow 2.2s ease-in-out .6s infinite; }
.bf-sc.next .n { background: var(--bf-accent); border-color: var(--bf-accent); color: #fff; }
.bf-sc h4 { font: 600 .95rem/1.3 var(--bf-body) !important; margin: .7rem 0 .25rem !important; padding: 0 !important; color: var(--bf-fg); }
.bf-sc p { font-size: .82rem; color: var(--bf-muted); margin: 0 0 .6rem; }
.bf-sc .st { font: 600 .68rem/1 var(--bf-mono); letter-spacing: .06em; text-transform: uppercase; }
.bf-sc.done .st { color: var(--bf-ok); } .bf-sc.next .st { color: var(--bf-accent); } .bf-sc .st { color: #9AA1AE; }
@keyframes bf-glow { 0%, 100% { box-shadow: 0 0 0 0 rgba(47,79,216,.0); } 50% { box-shadow: 0 0 0 5px rgba(47,79,216,.14); } }
@media (max-width: 900px) { .bf-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .bf-story { grid-template-columns: minmax(0, 1fr); } }

/* ---------- every page matches the overview ---------- */
.bf-hero, .bf-panel {
  position: relative; overflow: hidden; border: none; color: #fff;
  background:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 32px 32px,
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 32px 32px,
    radial-gradient(800px 340px at 10% -30%, #2B44B0 0%, rgba(43,68,176,0) 62%),
    radial-gradient(600px 300px at 105% 130%, rgba(30,154,98,.45) 0%, rgba(30,154,98,0) 60%),
    #0A0F1F;
}
.bf-hero { border-radius: 18px; padding: 20px 28px 24px; }
.bf-hero h1 { color: #FFFFFF !important; margin: 1.1rem 0 .35rem !important; }
.bf-hero h1 em, .bf-grad { font-style: normal; background: linear-gradient(90deg, #93A8FF 0%, #46E0A8 100%);
                           -webkit-background-clip: text; background-clip: text; color: transparent; }
.bf-hero p { color: #B9C1E0; }
.bf-hero .bf-st { color: #8F9AC4; }
.bf-hero .bf-st span { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.22); color: #C9D0EA; }
.bf-hero .bf-st.done { color: #B9C1E0; }
.bf-hero .bf-st.done span { background: rgba(70,224,168,.14); border-color: #46E0A8; color: #46E0A8; }
.bf-hero .bf-st.now { color: #FFFFFF; }
.bf-hero .bf-st.now span { background: #4F6BFF; border-color: #A9B9FF; color: #fff; box-shadow: 0 0 0 4px rgba(79,107,255,.3); }
.bf-hero .bf-stepper i { background: rgba(255,255,255,.14); }
.bf-hero .bf-stepper i.done { background: #46E0A8; }

.bf-panel { display: grid; grid-template-columns: 190px minmax(0, 1fr); gap: 28px; align-items: center;
            border-radius: 18px; padding: 22px 28px; margin: 0 0 1.2rem; animation: bf-rise .5s ease both; }
.bf-panel .bf-ring .trk { stroke: rgba(255,255,255,.1); }
.bf-panel .bf-ring .lbl b { color: #fff; }
.bf-panel .bf-ring .lbl span { color: #9FAAD6; }
.bf-pstats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.bf-pstats > div { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); border-radius: 12px; padding: 14px 16px; }
.bf-pstats .k { font: 500 .76rem/1.3 var(--bf-mono); letter-spacing: .08em; text-transform: uppercase; color: #9FAAD6; }
.bf-pstats .v { font: 700 1.9rem/1.1 var(--bf-display); letter-spacing: -.02em; color: #fff; margin-top: 6px; font-variant-numeric: tabular-nums; }
.bf-pstats .s { font-size: .8rem; color: #8D97BC; margin-top: 2px; }
.bf-pstats .s b { color: #46E0A8; font-weight: 600; }
.bf-panel .note { grid-column: 1 / -1; font-size: .82rem; color: #8D97BC; margin-top: -6px; }
@media (max-width: 900px) { .bf-panel { grid-template-columns: minmax(0, 1fr); } .bf-pstats { grid-template-columns: minmax(0, 1fr); } }

[data-testid="stMetric"] { background: var(--bf-surface); border: 1px solid var(--bf-line); border-radius: 12px; padding: 14px 16px; }
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height] { transition: transform .18s ease, box-shadow .18s ease; }
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height]:hover {
  transform: translateY(-2px); box-shadow: 0 14px 30px -18px rgba(16,24,64,.35); }
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
  background: linear-gradient(135deg, #4A66FF 0%, #2F4FD8 100%); border: none; box-shadow: 0 8px 20px -10px rgba(47,79,216,.8); }
.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover { filter: brightness(1.08); }
.bf-question { background: #F3F5FF; border-color: #DCE3FF; }

/* ---------- dark page: the whole app matches the overview ---------- */
.stApp {
  background:
    radial-gradient(1100px 560px at 85% -10%, rgba(43,68,176,.32) 0%, rgba(43,68,176,0) 60%),
    radial-gradient(900px 520px at -10% 110%, rgba(30,154,98,.16) 0%, rgba(30,154,98,0) 60%),
    #0A0F1F;
  background-attachment: fixed;
}
[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,.06); }
.bf-hero, .bf-panel, .bf-dark { border: 1px solid rgba(255,255,255,.08); box-shadow: 0 24px 60px -30px rgba(0,0,0,.8); }
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height] {
  background: rgba(18,26,51,.78) !important; border-color: var(--bf-line) !important; backdrop-filter: blur(6px); }
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][height]:hover {
  border-color: #33427A !important; box-shadow: 0 16px 36px -20px rgba(0,0,0,.9), 0 0 0 1px rgba(111,136,255,.12); }
[data-testid="stMetric"], [data-testid="stExpander"] details { background: rgba(18,26,51,.78); border-color: var(--bf-line); }

.bf-green { background: rgba(43,217,159,.14); color: #4BE3AE; }
.bf-red   { background: rgba(255,107,97,.15); color: #FF8A80; }
.bf-amber { background: rgba(245,196,107,.14); color: #F5C46B; }
.bf-blue  { background: rgba(111,136,255,.16); color: #A9B9FF; }
.bf-gray  { background: rgba(255,255,255,.08); color: #B5BDDC; }
.bf-ink   { background: #E8EBF7; color: #0A0F1F; }
.bf-badge { background: rgba(245,196,107,.1); color: #F5C46B; border-color: rgba(245,196,107,.35); }
.bf-quote { background: rgba(255,255,255,.04); }
.bf-question { background: rgba(111,136,255,.08); border-color: rgba(111,136,255,.28); color: var(--bf-fg); }
.bf-av { box-shadow: 0 0 0 3px #121A33, 0 0 0 4px var(--c); }
.bf-flow .ck { border-color: #121A33; color: #0A0F1F; }
.bf-ring .trk { stroke: rgba(255,255,255,.1); }
.bf-dots2 i { border-color: #3A4670; }
.bf-sc .n { background: transparent; border-color: #3A4670; }
.bf-sc.done .n, .bf-sc.next .n { color: #0A0F1F; }
.bf-sc.next { box-shadow: 0 0 0 1px rgba(111,136,255,.3); }
.bf-win { background: linear-gradient(120deg, rgba(43,217,159,.16), rgba(111,136,255,.12)); border-color: rgba(43,217,159,.35); }
.bf-win path { stroke: #0A0F1F; }
.bf-kpi .s b, .bf-pstats .s b { color: #4BE3AE; }
.stApp [data-testid="stCaptionContainer"] p { color: var(--bf-muted); }
@keyframes bf-glow { 0%, 100% { box-shadow: 0 0 0 1px rgba(111,136,255,.3); } 50% { box-shadow: 0 0 0 5px rgba(111,136,255,.18); } }

@media (prefers-reduced-motion: reduce) {
  .stApp *, .stApp *::before, .stApp *::after { animation: none !important; transition: none !important; }
  .bf-win path { stroke-dashoffset: 0; }
}

/* ---------- accessibility and polish (contrast measured on the rendered page, WCAG AA 4.5:1) ---------- */
[data-testid="stCaptionContainer"], [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { opacity: 1 !important; }
.stApp [data-testid="stCaptionContainer"] p, .stApp [data-testid="stCaptionContainer"] { color: #A9B2D6 !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stCaptionContainer"] * { color: #AEB7DA !important; opacity: 1 !important; }
.bf-hero .bf-st.now span { background: #3A54E0; border-color: #C5D0FF; }
.bf-muted, .bf-kpi .s, .bf-pstats .s, .bf-panel .note { color: #A9B2D6; }
:focus-visible { outline: 3px solid #A9B9FF !important; outline-offset: 2px; }
button:focus-visible, [role="tab"]:focus-visible, summary:focus-visible { outline-offset: 3px; }
.bf-pill .ic { font-style: normal; margin-right: 5px; font-size: .72rem; }
.bf-pill .ic.pulse { animation: bf-pulse 1.8s ease-out infinite; border-radius: 50%; }

/* coverage page: a one-line verdict first, a smaller ring */
.bf-verdict { display: flex; gap: 12px; align-items: center; border-radius: 12px; padding: 12px 16px; margin: 0 0 .9rem;
              border: 1px solid var(--bf-line); background: rgba(18,26,51,.78); font-size: 1.02rem; }
.bf-verdict b { font-weight: 600; }
.bf-verdict .vi { flex: none; width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center;
                  font: 700 .95rem/1 var(--bf-body); }
.bf-verdict.warn { border-color: rgba(255,107,97,.45); } .bf-verdict.warn .vi { background: rgba(255,107,97,.18); color: #FF8A80; }
.bf-verdict.good { border-color: rgba(43,217,159,.45); } .bf-verdict.good .vi { background: rgba(43,217,159,.16); color: #4BE3AE; }
.bf-verdict.idle .vi { background: rgba(255,255,255,.08); color: #B5BDDC; }
.bf-verdict .next { display: block; color: #A9B2D6; font-size: .86rem; margin-top: 2px; }
.bf-panel { grid-template-columns: 150px minmax(0, 1fr); gap: 22px; padding: 16px 24px; }
.bf-ring { width: 136px; height: 136px; }
.bf-ring .lbl b { font-size: 1.8rem; }

/* empty states */
.bf-empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; padding: 22px 16px;
            border: 1px dashed #3A4670; border-radius: 12px; background: rgba(255,255,255,.02); margin: .4rem 0; }
.bf-empty svg { width: 34px; height: 34px; color: #8FA5FF; margin-bottom: 4px; }
.bf-empty b { font-size: 1.02rem; } .bf-empty span { color: #A9B2D6; font-size: .9rem; max-width: 30rem; }
.bf-lock { display: inline-flex; gap: 6px; align-items: center; font: 600 .78rem/1 var(--bf-body); color: #B5BDDC;
           background: rgba(255,255,255,.07); border-radius: 999px; padding: 5px 11px; margin-right: 6px; }
.bf-lock svg { width: 13px; height: 13px; }

/* phones */
@media (max-width: 700px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.4rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: .6rem !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
  .bf-stepper { gap: 5px; } .bf-stepper i { display: none; } .bf-st { font-size: .72rem; }
  .bf-hero, .bf-dark { padding: 16px 16px 18px; border-radius: 14px; }
  .bf-panel { grid-template-columns: minmax(0, 1fr); }
  .bf-pstats { width: 100%; }
  .bf-flow { flex-wrap: wrap; } .bf-flow .arrow { min-width: 30px; }
  .bf-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bf-story { grid-template-columns: minmax(0, 1fr); }
}

/* ---------- guidance: next step, privacy table, compact decision list, Back/Next ---------- */
.bf-next { display: flex; gap: 12px; align-items: center; border: 1px solid rgba(111,136,255,.45); border-radius: 12px;
           padding: 12px 16px; margin: 0 0 .5rem; background: rgba(111,136,255,.10); }
.bf-next .nx { flex: none; width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center;
               background: #3A54E0; color: #fff; font: 700 1rem/1 var(--bf-body); }
.bf-next b { display: block; font: 600 .78rem/1.3 var(--bf-mono); letter-spacing: .08em; text-transform: uppercase; color: #C5D0FF; }
.bf-next span { font-size: 1.02rem; }
.bf-who { width: 100%; border-collapse: collapse; font-size: .92rem; }
.bf-who th, .bf-who td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--bf-line); vertical-align: top; }
.bf-who th { width: 32%; font-weight: 600; }
.bf-list { list-style: none; margin: .2rem 0 1rem; padding: 0; display: grid; gap: 8px; }
.bf-list li { display: flex; gap: 12px; align-items: center; padding: 10px 14px; border: 1px solid var(--bf-line);
              border-radius: 10px; background: rgba(18,26,51,.6); }
.bf-list li .t { flex: 1; min-width: 0; } .bf-list li .c { color: #A9B2D6; font-size: .86rem; white-space: nowrap; }
.bf-pstats .v.small { font-size: 1.35rem; line-height: 1.25; }
.bf-stepper { cursor: default; }
/* sidebar groups are plain: no card, border or hover lift around the navigation and the other sidebar widgets */
[data-testid="stSidebar"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"],
[data-testid="stSidebar"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"]:hover {
  background: transparent !important; border: 0 !important; box-shadow: none !important; transform: none !important;
  backdrop-filter: none !important; transition: none; }
[data-testid="stSidebar"] [role="radiogroup"] { padding: 2px 4px; }
[data-testid="stHtml"]:has(#bf-tour-loader) { display: none; }   /* the tour's loader takes no room */
@media (max-width: 700px) { .bf-list li { flex-wrap: wrap; } .bf-who th { width: 40%; } }
</style>
"""

_BRAND = """<div class="bf-brand"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
<circle cx="5" cy="6" r="2.4" fill="currentColor"/><circle cx="19" cy="6" r="2.4" fill="currentColor"/>
<circle cx="5" cy="18" r="2.4" fill="currentColor"/><circle cx="19" cy="18" r="2.4" fill="currentColor"/>
<path d="M12 8.5 15.5 12 12 15.5 8.5 12Z" fill="#2F4FD8"/>
<path d="M7 7.3 10 10.3M17 7.3 14 10.3M7 16.7l3-3M17 16.7l-3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
</svg>BusFactor</div>"""

# the active palette (BUSFACTOR_PALETTE) is applied once; status colours keep their meaning in every palette
# a flat palette's overrides go INSIDE the <style> block (after the rules they replace)
_sheet = palettes.recolor(_CSS)
CSS = _sheet.replace("</style>", palettes.overrides() + "</style>") if palettes.overrides() else _sheet
BRAND = palettes.recolor(_BRAND)
