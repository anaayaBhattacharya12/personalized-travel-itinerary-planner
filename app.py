
import io
import json
import math
import os
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

import requests
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, PageBreak, SimpleDocTemplate
)

APP_NAME = "Personalized Travel Itinerary Planner"
DATA_FILE = Path(".travel_trips.json")

CITIES = [
    {"city":"Goa, India","vibes":["Beach","Urban"],"budgets":["Budget","Moderate","Luxury"],"interests":["Food","Adventure","Nightlife"],"currency":"INR","symbol":"₹","daily": {"Budget":2200,"Moderate":4500,"Luxury":10000}},
    {"city":"Jaipur, India","vibes":["Cultural","Urban"],"budgets":["Budget","Moderate","Luxury"],"interests":["Food","History"],"currency":"INR","symbol":"₹","daily":{"Budget":1800,"Moderate":3800,"Luxury":8500}},
    {"city":"Manali, India","vibes":["Mountains","Adventure"],"budgets":["Budget","Moderate","Luxury"],"interests":["Adventure","Food"],"currency":"INR","symbol":"₹","daily":{"Budget":2000,"Moderate":4200,"Luxury":9000}},
    {"city":"Udaipur, India","vibes":["Cultural","Urban"],"budgets":["Budget","Moderate","Luxury"],"interests":["History","Food"],"currency":"INR","symbol":"₹","daily":{"Budget":1900,"Moderate":4000,"Luxury":9000}},
    {"city":"Bangkok, Thailand","vibes":["Urban","Cultural"],"budgets":["Budget","Moderate","Luxury"],"interests":["Food","Nightlife","History"],"currency":"THB","symbol":"฿","daily":{"Budget":900,"Moderate":1800,"Luxury":4200}},
    {"city":"Bali, Indonesia","vibes":["Beach","Cultural"],"budgets":["Budget","Moderate","Luxury"],"interests":["Food","Adventure","Nightlife"],"currency":"IDR","symbol":"Rp","daily":{"Budget":350000,"Moderate":750000,"Luxury":1800000}},
    {"city":"Kyoto, Japan","vibes":["Cultural","Mountains"],"budgets":["Moderate","Luxury"],"interests":["History","Food"],"currency":"JPY","symbol":"¥","daily":{"Budget":8500,"Moderate":17000,"Luxury":35000}},
    {"city":"Dubai, UAE","vibes":["Urban","Beach"],"budgets":["Moderate","Luxury"],"interests":["Food","Nightlife"],"currency":"AED","symbol":"د.إ","daily":{"Budget":250,"Moderate":500,"Luxury":1200}},
]

ATTRACTIONS = {
    "Goa, India":[
        ("Baga Beach","Beach","Beach walk & water activities","North Goa",350),
        ("Fort Aguada","History","Portuguese fort & sea views","North Goa",100),
        ("Anjuna Flea Market","Food","Local shopping and street food","North Goa",250),
        ("Panaji Latin Quarter","Cultural","Heritage lanes & cafés","Central Goa",300),
        ("Dona Paula","Beach","Sunset viewpoint","Central Goa",0),
        ("Candolim Dining Strip","Nightlife","Dinner and live music","North Goa",900),
    ],
    "Jaipur, India":[
        ("Amber Fort","History","Fort complex and palace","Amer",550),
        ("City Palace","History","Royal residence and museum","Old City",400),
        ("Jantar Mantar","History","Astronomical instruments","Old City",200),
        ("Hawa Mahal","Cultural","Iconic pink façade","Old City",200),
        ("Johari Bazaar","Food","Market, snacks and crafts","Old City",350),
        ("MI Road Dinner","Nightlife","Restaurants and evening walk","Central Jaipur",800),
    ],
    "Manali, India":[
        ("Hadimba Temple","History","Forest temple","Old Manali",30),
        ("Old Manali Café Walk","Food","Cafés and local food","Old Manali",450),
        ("Solang Valley","Adventure","Mountain views and activities","Solang",1000),
        ("Vashisht Hot Springs","Adventure","Village and hot springs","Vashisht",100),
        ("Mall Road","Cultural","Shopping and people watching","Central Manali",250),
        ("Riverside Dinner","Food","Mountain-view dinner","Old Manali",800),
    ],
    "Udaipur, India":[
        ("City Palace","History","Palace and museum","Old City",500),
        ("Jagdish Temple","History","Historic temple","Old City",0),
        ("Lake Pichola Boat Ride","Adventure","Sunset lake cruise","Lake Pichola",800),
        ("Bagore Ki Haveli","Cultural","Museum and folk show","Old City",200),
        ("Hathi Pol Market","Food","Crafts and local snacks","Old City",300),
        ("Lakefront Dinner","Nightlife","Rooftop dinner","Lake Pichola",1000),
    ],
    "Bangkok, Thailand":[
        ("Grand Palace","History","Royal complex","Rattanakosin",500),
        ("Wat Pho","History","Temple and reclining Buddha","Rattanakosin",200),
        ("Chinatown","Food","Street-food exploration","Yaowarat",400),
        ("Chatuchak Market","Food","Markets and snacks","Chatuchak",300),
        ("Chao Phraya Cruise","Adventure","River cruise","Riverside",700),
        ("Rooftop Dinner","Nightlife","Skyline dining","Sukhumvit",1500),
    ],
    "Bali, Indonesia":[
        ("Ubud Palace","Cultural","Balinese architecture","Ubud",80000),
        ("Tegallalang Rice Terrace","Adventure","Rice terrace walk","Ubud",50000),
        ("Ubud Market","Food","Local crafts and food","Ubud",150000),
        ("Seminyak Beach","Beach","Beach afternoon","Seminyak",0),
        ("Uluwatu Temple","History","Clifftop temple","Uluwatu",50000),
        ("Beach Club Dinner","Nightlife","Sunset dinner","Seminyak",350000),
    ],
    "Kyoto, Japan":[
        ("Fushimi Inari","History","Torii gate trail","Fushimi",0),
        ("Kiyomizu-dera","History","Temple and city views","Higashiyama",500),
        ("Nishiki Market","Food","Food market","Downtown",1500),
        ("Gion Walk","Cultural","Traditional streets","Gion",0),
        ("Arashiyama Bamboo Grove","Adventure","Bamboo forest","Arashiyama",0),
        ("Pontocho Dinner","Nightlife","Laneway dining","Downtown",4500),
    ],
    "Dubai, UAE":[
        ("Burj Khalifa","Urban","Observation deck","Downtown",180),
        ("Dubai Mall","Urban","Shopping and aquarium area","Downtown",100),
        ("Al Fahidi Historic District","History","Heritage quarter","Old Dubai",35),
        ("Gold Souk","Cultural","Traditional market","Deira",0),
        ("Jumeirah Beach","Beach","Beach relaxation","Jumeirah",0),
        ("Marina Dinner","Nightlife","Waterfront dining","Dubai Marina",180),
    ],
}

FX_TO_USD = {"INR":0.0115, "THB":0.029, "IDR":0.000059, "JPY":0.0067, "AED":0.272}
USD_TO_INR = 88.5

def safe_int(v, default=0):
    try:
        return int(round(float(v)))
    except Exception:
        return default

def money(local, currency):
    symbols = {"INR":"₹","THB":"฿","IDR":"Rp","JPY":"¥","AED":"د.إ"}
    return f"{symbols.get(currency, currency)}{local:,.0f}"

def usd(local, currency):
    return local * FX_TO_USD.get(currency, 0.0115)

def api_generate(prompt: str, provider: str, key: str) -> str:
    """Optional AI enhancement. Returns empty string on failure so demo mode remains usable."""
    if not key:
        return ""
    try:
        if provider == "Gemini":
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            r = requests.post(url, params={"key": key}, json={"contents":[{"parts":[{"text":prompt}]}]}, timeout=25)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        url = "https://api.groq.com/openai/v1/chat/completions"
        r = requests.post(url, headers={"Authorization":f"Bearer {key}"}, json={
            "model":"llama-3.3-70b-versatile",
            "messages":[{"role":"user","content":prompt}],
            "temperature":0.7
        }, timeout=25)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return ""

def load_trips() -> List[Dict[str, Any]]:
    try:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []

def save_trips(trips):
    DATA_FILE.write_text(json.dumps(trips, indent=2, ensure_ascii=False), encoding="utf-8")

def recommend(prefs):
    scored = []
    for c in CITIES:
        score = 0
        if prefs["vibe"] in c["vibes"]: score += 5
        if prefs["budget"] in c["budgets"]: score += 3
        score += sum(2 for i in prefs["interests"] if i in c["interests"])
        if prefs["destination"] and prefs["destination"].lower() in c["city"].lower(): score += 20
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:3]]

def clustered_plan(city, days, budget, interests, pace):
    items = ATTRACTIONS.get(city, [])
    wanted = [x for x in items if x[1] in interests] or items
    groups = {}
    for item in wanted:
        groups.setdefault(item[3], []).append(item)
    clusters = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    ordered = [x for _, vals in clusters for x in vals]
    # Spread attractions while preserving cluster locality; repeat only when duration exceeds supply.
    plan = []
    pace_factor = {"Relaxed":1.0, "Moderate":1.15, "Fast-Paced":1.35}[pace]
    for d in range(days):
        day_items = []
        for j in range(2):
            idx = (d*2+j) % len(ordered)
            day_items.append(ordered[idx])
        day = {"day":d+1, "slots":[], "total":0}
        morning, afternoon = day_items
        slots = [
            ("Morning Sightseeing", morning),
            ("Lunch Recommendation", ("Local restaurant near " + morning[3], "Food", "Regional lunch", morning[3], 450)),
            ("Afternoon Leisure", afternoon),
            ("Evening Dining & Entertainment", ("Evening dining near " + afternoon[3], "Nightlife", "Dinner / entertainment", afternoon[3], 900)),
        ]
        for label, x in slots:
            name, category, desc, area, cost = x
            adjusted = safe_int(cost * pace_factor)
            day["slots"].append({"slot":label,"name":name,"category":category,"description":desc,"area":area,"cost":adjusted})
            day["total"] += adjusted
        plan.append(day)
    return plan

def make_pdf(trip):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleX", parent=styles["Title"], alignment=TA_CENTER, fontSize=22, leading=26, spaceAfter=8)
    h2 = ParagraphStyle("H2X", parent=styles["Heading2"], fontSize=15, leading=18, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("BodyX", parent=styles["BodyText"], fontSize=9.5, leading=13)
    story = [Paragraph("✈ " + APP_NAME, title), Paragraph(trip["city"], h2),
             Paragraph(f"<b>Dates:</b> {trip['start']} → {trip['end']} &nbsp;&nbsp; <b>Party:</b> {trip['party']} &nbsp;&nbsp; <b>Budget:</b> {trip['budget']}", body), Spacer(1,8)]
    cumulative = 0
    for day in trip["plan"]:
        story.append(Paragraph(f"Day {day['day']}", h2))
        data = [["Time slot","Plan","Area","Est. cost"]]
        for s in day["slots"]:
            cumulative += s["cost"]
            data.append([s["slot"], f"<b>{s['name']}</b><br/>{s['description']}", s["area"], money(s["cost"], trip["currency"])])
        data.append(["","<b>Running trip total</b>","","<b>"+money(cumulative, trip["currency"])+"</b>"])
        t = Table(data, colWidths=[32*mm,75*mm,35*mm,30*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17324D")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),8),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#D6DCE3")),
            ("BACKGROUND",(0,1),(-1,-2),colors.HexColor("#F7FAFC")),
            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#E9F2F8")),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        story += [t, Spacer(1,8)]
    story += [PageBreak(), Paragraph("Emergency & Departure Checklist", h2)]
    checklist = [
        "Passport / government ID checked", "Travel insurance details saved offline",
        "Emergency contacts shared with travel party", "Hotel / accommodation address saved",
        "Local emergency number noted", "Copies of tickets and important documents saved",
        "Medication / essential items packed", "Bank cards and backup payment method ready",
    ]
    story.append(Table([[f"☐ {x}"] for x in checklist], colWidths=[170*mm],
                       style=[("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#D6DCE3")),
                              ("INNERGRID",(0,0),(-1,-1),0.25,colors.HexColor("#E5E7EB")),
                              ("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),10),
                              ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]))
    story += [Spacer(1,12), Paragraph("<b>Emergency contacts:</b> Local emergency services • Embassy / consulate • Travel insurer • Accommodation front desk", body)]
    doc.build(story)
    return buf.getvalue()

st.set_page_config(page_title=APP_NAME, page_icon="✈️", layout="wide")

st.markdown("""
<style>
:root { --navy:#17324D; --sky:#4EA5D9; --sand:#FFF7E8; --ink:#17202A; }
.stApp { background: linear-gradient(135deg,#F8FBFD 0%,#FFF8ED 100%); color:var(--ink); }
.hero { padding:28px 32px; border-radius:24px; background:linear-gradient(120deg,#17324D,#276C8E); color:white; margin-bottom:18px; box-shadow:0 12px 35px rgba(23,50,77,.16); }
.hero h1 { margin:0; font-size:2.2rem; } .hero p { margin:8px 0 0; opacity:.9; }
.card { background:white; padding:18px; border-radius:18px; border:1px solid #E5EAF0; box-shadow:0 7px 22px rgba(20,40,60,.06); margin-bottom:12px; }
.tag { display:inline-block; padding:4px 9px; border-radius:99px; background:#E9F4FA; margin:2px; font-size:.78rem; }
.small { color:#657180; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""<div class="hero"><h1>✈️ {APP_NAME}</h1><p>AI-assisted planning • locality-aware days • live budget tracking • offline PDF</p></div>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    mode = st.radio("AI mode", ["Demo mode", "Gemini", "Groq"], index=0)
    api_key = ""
    if mode != "Demo mode":
        api_key = st.text_input(f"{mode} API key", type="password", help="Stored only in this Streamlit session.")
        st.caption("Your key is used for the current session and is never written to the trip file.")
    st.divider()
    st.caption("Deployment: Streamlit Community Cloud")
    st.caption("Persistence: local JSON (demo-friendly, no external DB)")

with st.form("preferences"):
    c1,c2,c3 = st.columns(3)
    with c1:
        destination = st.text_input("Destination (optional)", placeholder="Leave blank to get recommendations")
        vibe = st.selectbox("Travel vibe", ["Beach","Mountains","Cultural","Urban"])
        duration = st.number_input("Trip duration (days)", min_value=1, max_value=30, value=4)
    with c2:
        start = st.date_input("Travel start date", value=date.today()+timedelta(days=14))
        budget = st.selectbox("Budget level", ["Budget","Moderate","Luxury"])
        party = st.selectbox("Travel party", ["Solo","Couple","Family","Friends"])
    with c3:
        pace = st.selectbox("Pace", ["Relaxed","Moderate","Fast-Paced"])
        interests = st.multiselect("Interests", ["Food","Adventure","History","Nightlife"], default=["Food","History"])
        submitted = st.form_submit_button("✨ Build my trip", use_container_width=True)

if submitted:
    prefs = {"destination":destination, "vibe":vibe, "duration":duration, "start":start.isoformat(),
             "budget":budget, "party":party, "pace":pace, "interests":interests or ["Food"]}
    choices = recommend(prefs)
    selected = choices[0]["city"] if destination == "" else next((c["city"] for c in CITIES if destination.lower() in c["city"].lower()), choices[0]["city"])
    trip = {
        "id": f"{date.today().isoformat()}-{len(load_trips())+1}",
        "city": selected, "start": start.isoformat(),
        "end": (start + timedelta(days=int(duration)-1)).isoformat(),
        "budget": budget, "party": party, "pace": pace, "interests": interests or ["Food"],
        "currency": next(c["currency"] for c in CITIES if c["city"]==selected),
        "plan": clustered_plan(selected, int(duration), budget, interests or ["Food"], pace),
    }
    st.session_state["prefs"] = prefs
    st.session_state["recommendations"] = choices
    st.session_state["trip"] = trip
    st.session_state["saved"] = False
    if mode != "Demo mode":
        prompt = f"Create concise travel tips for {selected}, {duration} days, {budget} budget, {party}, interests {interests}. Do not invent prices."
        ai = api_generate(prompt, mode, api_key)
        st.session_state["ai_tip"] = ai or "AI service was unavailable; the deterministic itinerary remains active."
    else:
        st.session_state["ai_tip"] = "Demo mode is active. The planner uses its built-in destination and locality-aware itinerary engine."

tabs = st.tabs(["🌍 Destination Recommender","🗺️ Optimized Itinerary","🎨 Vibe & Activity Swap","💾 Trip Management"])

with tabs[0]:
    st.subheader("Smart Destination Recommender")
    if "recommendations" not in st.session_state:
        st.info("Set your preferences above and click **Build my trip**.")
    else:
        for i,c in enumerate(st.session_state["recommendations"],1):
            score_tags = c["vibes"] + [st.session_state["prefs"]["budget"]] + [x for x in st.session_state["prefs"]["interests"] if x in c["interests"]]
            st.markdown(f"""<div class="card"><h3>{i}. {c['city']}</h3>
            {''.join(f'<span class="tag">{x}</span>' for x in dict.fromkeys(score_tags))}
            <p class="small">Indicative daily spend: {money(c['daily'].get(st.session_state['prefs']['budget'], c['daily']['Moderate']), c['currency'])} • matched to your vibe, budget and interests.</p></div>""", unsafe_allow_html=True)

with tabs[1]:
    st.subheader("Day-by-Day Optimized Itinerary")
    trip = st.session_state.get("trip")
    if not trip:
        st.info("Build a trip first.")
    else:
        total = 0
        for day in trip["plan"]:
            st.markdown(f"### Day {day['day']}")
            rows = []
            for s in day["slots"]:
                total += s["cost"]
                rows.append([s["slot"], s["name"], s["area"], money(s["cost"],trip["currency"]), f"${usd(s['cost'],trip['currency']):.2f}"])
            st.dataframe(rows, column_config={"0":"Time slot","1":"Activity","2":"Area","3":"Local cost","4":"USD"}, hide_index=True, use_container_width=True)
            st.caption(f"Day total: {money(day['total'],trip['currency'])} • Nearby areas are intentionally clustered to reduce backtracking.")
        st.metric("Estimated trip activity + dining total", money(total, trip["currency"]), f"≈ ${usd(total,trip['currency']):,.0f} USD • ≈ ₹{usd(total,trip['currency'])*USD_TO_INR:,.0f} INR")
        if st.session_state.get("ai_tip"):
            st.info(st.session_state["ai_tip"])

with tabs[2]:
    st.subheader("Vibe Customization & Dynamic Activity Swap")
    trip = st.session_state.get("trip")
    if not trip:
        st.info("Build a trip first.")
    else:
        day_no = st.selectbox("Choose day", list(range(1,len(trip["plan"])+1)))
        day = trip["plan"][day_no-1]
        slot_names = [s["slot"] for s in day["slots"]]
        slot_name = st.selectbox("Choose slot", slot_names)
        slot = next(s for s in day["slots"] if s["slot"]==slot_name)
        st.write(f"Current: **{slot['name']}** — {slot['description']} ({slot['area']})")
        swap_options = ["Outdoor market","Museum","Beach / park","Local food experience","Adventure activity","Café / relaxed time"]
        replacement = st.selectbox("Swap with", swap_options)
        if st.button("🔄 Regenerate this slot", use_container_width=True):
            cost_map = {"Outdoor market":300,"Museum":400,"Beach / park":100,"Local food experience":650,"Adventure activity":900,"Café / relaxed time":350}
            slot["name"] = replacement
            slot["description"] = f"Customized {replacement.lower()} near {slot['area']}"
            slot["category"] = "Food" if "food" in replacement.lower() or "café" in replacement.lower() else "Adventure"
            slot["cost"] = cost_map[replacement]
            day["total"] = sum(x["cost"] for x in day["slots"])
            st.success("Only this slot was regenerated. The rest of the itinerary is unchanged.")
            st.rerun()

with tabs[3]:
    st.subheader("Trip Management & Offline Export")
    trip = st.session_state.get("trip")
    if trip:
        if st.button("💾 Save current trip", use_container_width=True):
            trips = load_trips()
            trips = [x for x in trips if x["id"] != trip["id"]]
            trips.insert(0, trip)
            save_trips(trips)
            st.session_state["saved"] = True
        if st.session_state.get("saved"):
            st.success("Trip saved to local JSON persistence.")
        pdf = make_pdf(trip)
        st.download_button("📄 Export offline PDF itinerary", data=pdf, file_name=f"{re.sub(r'[^A-Za-z0-9]+','_',trip['city'])}_itinerary.pdf", mime="application/pdf", use_container_width=True)
    st.divider()
    trips = load_trips()
    st.write(f"**Saved trip history:** {len(trips)}")
    for t in trips[:10]:
        with st.expander(f"{t['city']} • {t['start']} → {t['end']}"):
            st.write(f"{t['budget']} • {t['party']} • {len(t['plan'])} days")
            if st.button("Load trip", key=f"load_{t['id']}"):
                st.session_state["trip"] = t
                st.rerun()
