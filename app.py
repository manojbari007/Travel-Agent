"""
AI Travel Agent - Streamlit Chat Application
Conversational travel planning with budget enforcement
"""

import streamlit as st
import json
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from agent.travel_agent import TravelAgent
from config import AVAILABLE_CITIES
from utils.helpers import get_city_emoji, format_itinerary_for_export
from utils.query_parser import QueryParser

# Page config
st.set_page_config(page_title="AI Travel Agent", page_icon="✈️", layout="wide", initial_sidebar_state="collapsed")

# Clean, readable CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .hero {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .hero p { margin: 0.5rem 0 0; opacity: 0.9; font-size: 0.95rem; }
    
    .user-msg {
        background: #4F46E5;
        color: white;
        padding: 12px 16px;
        border-radius: 16px 16px 4px 16px;
        margin: 8px 0;
        margin-left: 25%;
        font-size: 0.95rem;
    }
    
    .bot-msg {
        background: #F3F4F6;
        color: #1F2937;
        padding: 12px 16px;
        border-radius: 16px 16px 16px 4px;
        margin: 8px 0;
        margin-right: 25%;
        font-size: 0.95rem;
        border: 1px solid #E5E7EB;
    }
    
    .error-msg {
        background: #FEF2F2;
        color: #991B1B;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #FECACA;
    }
    
    .success-msg {
        background: #F0FDF4;
        color: #166534;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #BBF7D0;
    }
    
    /* Trip Card */
    .trip-header {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 16px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .trip-header h2 { margin: 0; font-size: 1.5rem; }
    .trip-header p { margin: 8px 0 0; opacity: 0.9; }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-value { font-size: 1.4rem; font-weight: 700; color: #4F46E5; }
    .metric-label { font-size: 0.75rem; color: #6B7280; text-transform: uppercase; margin-top: 4px; }
    
    /* Info Cards - Light backgrounds with dark text */
    .flight-card {
        background: #EFF6FF;
        color: #1E3A8A;
        padding: 16px 20px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #BFDBFE;
    }
    .flight-card h4 { margin: 0 0 8px; color: #1E40AF; }
    
    .hotel-card {
        background: #F0FDF4;
        color: #166534;
        padding: 16px 20px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #BBF7D0;
    }
    .hotel-card h4 { margin: 0 0 8px; color: #15803D; }
    
    .budget-card {
        background: #FFFBEB;
        color: #92400E;
        padding: 16px 20px;
        border-radius: 12px;
        margin: 8px 0;
        border: 1px solid #FDE68A;
    }
    .budget-card h4 { margin: 0 0 8px; color: #B45309; }
    
    /* Day Card */
    .day-card {
        background: white;
        padding: 16px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #4F46E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .day-title { font-weight: 600; color: #1F2937; margin: 0; }
    .day-date { font-size: 0.85rem; color: #6B7280; }
    .day-weather { 
        font-size: 0.9rem; 
        color: #4B5563;
        background: #F9FAFB;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 8px 0;
        display: inline-block;
    }
    .activity { color: #374151; padding: 4px 0; font-size: 0.9rem; }
    
    /* Savings badge */
    .savings-badge {
        background: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    #MainMenu, footer { visibility: hidden; }
    
    .stButton > button {
        background: #4F46E5;
        color: white;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton > button:hover { background: #4338CA; }
</style>
""", unsafe_allow_html=True)


def init_state():
    defaults = {'messages': [], 'trip_plan': None, 'context': {}, 'parser': QueryParser(), 'key': 0}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def process_input(text: str):
    parser = st.session_state.parser
    ctx = st.session_state.context
    
    parsed = parser.parse_query(text, ctx)
    
    # Update context
    for key in ['source', 'destination', 'num_days', 'start_date', 'num_travelers', 'budget_preference', 'min_hotel_stars', 'max_budget']:
        if parsed.get(key):
            st.session_state.context[key] = parsed[key]
    
    ctx = st.session_state.context
    missing = []
    if not ctx.get('source'): missing.append('source')
    if not ctx.get('destination'): missing.append('destination')
    if not ctx.get('num_days'): missing.append('days')
    
    if missing:
        msg = build_missing_msg(missing, ctx)
        st.session_state.messages.append({"role": "bot", "content": msg})
    else:
        confirm = build_confirm_msg(ctx)
        st.session_state.messages.append({"role": "bot", "content": confirm})
        execute_plan(ctx)


def build_missing_msg(missing, ctx):
    parts = []
    if ctx.get('source'): parts.append(f"from {ctx['source']}")
    if ctx.get('destination'): parts.append(f"to {ctx['destination']}")
    if ctx.get('num_days'): parts.append(f"{ctx['num_days']} days")
    if ctx.get('max_budget'): parts.append(f"under ₹{ctx['max_budget']:,}")
    
    msg = ""
    if parts:
        msg = f"✅ Got: {', '.join(parts)}\n\n"
    
    msg += "📝 **Need:**\n"
    for m in missing:
        if m == 'source': msg += f"• **From?** ({', '.join(AVAILABLE_CITIES)})\n"
        elif m == 'destination': msg += f"• **To?** ({', '.join(AVAILABLE_CITIES)})\n"
        elif m == 'days': msg += "• **How many days?**\n"
    
    return msg


def build_confirm_msg(ctx):
    budget = f" within ₹{ctx['max_budget']:,}" if ctx.get('max_budget') else ""
    return f"🔍 Planning {ctx['num_days']}-day trip: {ctx['source']} → {ctx['destination']}{budget}..."


def execute_plan(ctx):
    agent = TravelAgent()
    
    plan = agent.plan_trip(
        source=ctx['source'],
        destination=ctx['destination'],
        start_date=ctx.get('start_date', (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")),
        num_days=ctx['num_days'],
        num_travelers=ctx.get('num_travelers', 1),
        budget_preference=ctx.get('budget_preference', 'balanced'),
        min_hotel_stars=ctx.get('min_hotel_stars', 2),
        max_budget=ctx.get('max_budget')
    )
    
    st.session_state.trip_plan = plan
    
    if plan.get('success'):
        b = plan['budget']
        savings_text = f" (₹{b['savings']:,} saved!)" if b.get('savings', 0) > 0 else ""
        st.session_state.messages.append({
            "role": "bot",
            "content": f"🎉 **Trip Ready!** Total: **{b['total_formatted']}**{savings_text} — {b['category']['description']}",
            "type": "success"
        })
    else:
        error_content = f"❌ **{plan.get('error', 'Cannot plan trip')}**\n\n"
        
        if plan.get('budget_analysis'):
            ba = plan['budget_analysis']
            error_content += f"**Your budget:** ₹{ba['your_budget']:,}\n"
            error_content += f"• Flights: ₹{ba['flight_cost']:,}\n"
            error_content += f"• Min expenses: ₹{ba['min_daily_expenses']:,}\n"
            error_content += f"• Left for hotel: ₹{ba['remaining_for_hotel']:,} ({ba['nights']} nights = ₹{ba['per_night_available']:,}/night)\n\n"
        
        if plan.get('closest_option'):
            co = plan['closest_option']
            error_content += f"**Closest option:** ₹{co['cost']:,}\n"
        
        if plan.get('suggestion'):
            error_content += f"\n💡 {plan['suggestion']}"
        
        st.session_state.messages.append({"role": "bot", "content": error_content, "type": "error"})


def render_trip(plan):
    if not plan.get('success'):
        return
    
    s = plan['trip_summary']
    f = plan['flight']
    h = plan['hotel']
    b = plan['budget']
    
    # Header
    st.markdown(f'''
    <div class="trip-header">
        <h2>🎉 {s['title']}</h2>
        <p>{get_city_emoji(s['from'])} {s['from']} → {get_city_emoji(s['to'])} {s['to']} • {s['dates']} • {s['travelers']} traveler(s)</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{b["total_formatted"]}</div><div class="metric-label">Total Cost</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{len(plan["itinerary"])}</div><div class="metric-label">Days</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{len(plan.get("places", []))}</div><div class="metric-label">Places</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-value">{b["category"]["emoji"]}</div><div class="metric-label">{b["category"]["name"]}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    t1, t2, t3, t4 = st.tabs(["📅 Itinerary", "✈️ Flight & Hotel", "💰 Budget", "🤖 Reasoning"])
    
    with t1:
        for day in plan['itinerary']:
            st.markdown(f'''
            <div class="day-card">
                <p class="day-title">Day {day['day']}</p>
                <p class="day-date">{day['date_display']}</p>
                <span class="day-weather">{day['weather_display']}</span>
            </div>
            ''', unsafe_allow_html=True)
            for act in day['activities']:
                st.markdown(f"<p class='activity'>• {act}</p>", unsafe_allow_html=True)
    
    with t2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'''
            <div class="flight-card">
                <h4>✈️ Flight</h4>
                <p><strong>{f['airline']}</strong></p>
                <p>One-way: {f['price_formatted']}</p>
                <p>Round-trip total: ₹{f['round_trip_cost']:,}</p>
                <p>Duration: {f['duration']}</p>
                <p style="font-size:0.85rem; opacity:0.8;">Departure: {f['departure']}</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            stars = "⭐" * h['stars']
            amenities = ", ".join(h['amenities'][:4])
            st.markdown(f'''
            <div class="hotel-card">
                <h4>🏨 Hotel</h4>
                <p><strong>{h['name']}</strong> {stars}</p>
                <p>{h['price_formatted']}</p>
                <p>Total: ₹{h['total_cost']:,}</p>
                <p style="font-size:0.85rem;">Amenities: {amenities}</p>
            </div>
            ''', unsafe_allow_html=True)
    
    with t3:
        bd = b['breakdown']
        st.markdown(f'''
        <div class="budget-card">
            <h4>💰 Budget Breakdown</h4>
            <p>✈️ <strong>Flights:</strong> {bd['flights']['formatted']} <span style="opacity:0.7">({bd['flights']['description']})</span></p>
            <p>🏨 <strong>Hotel:</strong> {bd['accommodation']['formatted']} <span style="opacity:0.7">({bd['accommodation']['description']})</span></p>
            <p>🍽️ <strong>Daily Expenses:</strong> {bd['daily_expenses']['formatted']} <span style="opacity:0.7">({bd['daily_expenses']['description']})</span></p>
            <hr style="border-color:#FDE68A; margin: 12px 0;">
            <p style="font-size:1.1rem;"><strong>Total: {b['total_formatted']}</strong> ({b['per_person_formatted']})</p>
        </div>
        ''', unsafe_allow_html=True)
        
        if b.get('within_budget') and b.get('max_budget'):
            st.markdown(f'<span class="savings-badge">✅ Within your ₹{b["max_budget"]:,} budget!</span>', unsafe_allow_html=True)
    
    with t4:
        st.markdown("### 🤖 How I Planned This Trip")
        for step in plan.get('reasoning', []):
            st.markdown(f"• {step}")
    
    # Export
    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.download_button("📄 Download JSON", json.dumps(plan, indent=2, default=str), "trip.json", use_container_width=True)
    col2.download_button("📝 Download Text", format_itinerary_for_export(plan), "trip.txt", use_container_width=True)


def main():
    init_state()
    
    st.markdown('<div class="hero"><h1>✈️ AI Travel Agent</h1><p>Tell me where you want to go and your budget!</p></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        if st.button("🗑️ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.trip_plan = None
            st.session_state.context = {}
            st.session_state.key += 1
            st.rerun()
        
        st.markdown("---")
        st.markdown("**🌍 Cities**")
        st.caption(", ".join(AVAILABLE_CITIES))
        
        st.markdown("---")
        st.markdown("**💡 Try saying:**")
        st.caption("• 3 day trip Mumbai to Goa under 15k")
        st.caption("• Budget trip Delhi to Jaipur")
        st.caption("• 5 days Bangalore to Hyderabad for 2")
        
        if st.session_state.context:
            st.markdown("---")
            st.markdown("**🧠 Current Context:**")
            ctx = st.session_state.context
            if ctx.get('source'): st.caption(f"From: {ctx['source']}")
            if ctx.get('destination'): st.caption(f"To: {ctx['destination']}")
            if ctx.get('num_days'): st.caption(f"Days: {ctx['num_days']}")
            if ctx.get('max_budget'): st.caption(f"Budget: ₹{ctx['max_budget']:,}")
    
    # Welcome
    if not st.session_state.messages:
        st.markdown('''
        <div class="bot-msg">
            <strong>👋 Hi! I'm your AI Travel Agent.</strong><br><br>
            Tell me your travel plans with budget, like:<br>
            • "Plan 3 day trip from Mumbai to Goa under 15k"<br>
            • "Budget trip from Delhi to Jaipur for 5 days"<br><br>
            I'll find options that fit your budget, or tell you if it's not possible!
        </div>
        ''', unsafe_allow_html=True)
    
    # Messages
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            msg_type = msg.get('type', '')
            if msg_type == 'error':
                st.markdown(f'<div class="error-msg">{msg["content"]}</div>', unsafe_allow_html=True)
            elif msg_type == 'success':
                st.markdown(f'<div class="success-msg">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # Trip results
    if st.session_state.trip_plan and st.session_state.trip_plan.get('success'):
        st.markdown("---")
        render_trip(st.session_state.trip_plan)
    
    # Input
    st.markdown("---")
    with st.form("chat", clear_on_submit=True):
        user_input = st.text_input("Message", placeholder="e.g., 3 day trip Chennai to Hyderabad under 20k", label_visibility="collapsed", key=f"in_{st.session_state.key}")
        if st.form_submit_button("Send ✈️", use_container_width=True) and user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.trip_plan = None
            process_input(user_input.strip())
            st.rerun()


if __name__ == "__main__":
    main()
