import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from itertools import permutations
from math import factorial
from datetime import datetime, timedelta, time as dt_time

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Βελτιστοποιητής Διαδρομής Αθήνας",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    color: white;
    position: relative;
    overflow: hidden;
}
.app-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(83,177,255,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.app-header h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
.app-header p  { margin: 6px 0 0; font-size: 14px; opacity: 0.7; }

/* Cards */
.route-card {
    background: white;
    border: 1px solid #e8ecf0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* Result rows */
.stop-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 14px 0;
    border-bottom: 1px solid #f0f2f5;
}
.stop-row:last-child { border-bottom: none; }
.stop-icon {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
    font-weight: 700;
}
.stop-icon.start  { background: #d1fae5; color: #065f46; }
.stop-icon.middle { background: #dbeafe; color: #1d4ed8; }
.stop-icon.end    { background: #fee2e2; color: #991b1b; }
.stop-name  { font-weight: 600; font-size: 15px; color: #111827; }
.stop-times { font-size: 13px; color: #6b7280; margin-top: 2px; font-family: 'DM Mono', monospace; }
.stop-dist  { font-size: 12px; color: #9ca3af; margin-top: 3px; }
.badge-ok   { background: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-warn { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-late { background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }

/* Stat boxes */
.stat-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.stat-val  { font-size: 24px; font-weight: 700; color: #0f3460; }
.stat-lbl  { font-size: 12px; color: #64748b; margin-top: 2px; }

/* Streamlit overrides */
div[data-testid="stSidebar"] > div { padding-top: 1rem; }
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Δεδομένα
# ─────────────────────────────────────────────
locations = {
    "Σύνταγμα": (37.9755, 23.7349), "Μοναστηράκι": (37.9765, 23.7257),
    "Πλάκα": (37.9721, 23.7265), "Γκάζι": (37.9771, 23.7131),
    "Κολωνάκι": (37.9782, 23.7436), "Λυκαβηττός": (37.9833, 23.7431),
    "Παγκράτι": (37.9681, 23.7432), "Καλλιμάρμαρο": (37.9688, 23.7414),
    "Ιλίσια": (37.9783, 23.7662), "Καισαριανή": (37.9642, 23.7651),
    "Υμηττός": (37.9498, 23.7522), "Ζωγράφου": (37.9685, 23.7760),
    "Δάφνη": (37.9509, 23.7343), "Βύρωνας": (37.9612, 23.7530),
    "Καρέας": (37.9494, 23.7556), "Γλυφάδα": (37.8638, 23.7547),
    "Βάρη": (37.8175, 23.7915), "Βούλα": (37.8543, 23.7769),
    "Βουλιαγμένη": (37.8081, 23.7764), "Άγιος Δημήτριος": (37.9306, 23.7341),
    "Ηλιούπολη": (37.9323, 23.7352), "Αργυρούπολη": (37.9049, 23.7523),
    "Ελληνικό": (37.8788, 23.7322), "Παλαιό Φάληρο": (37.9284, 23.7010),
    "Νέα Σμύρνη": (37.9445, 23.7146), "Καλλιθέα": (37.9550, 23.7029),
    "Μοσχάτο": (37.9539, 23.6787), "Κηφισιά": (38.0728, 23.8111),
    "Μαρούσι": (38.0567, 23.8086), "Χαλάνδρι": (38.0209, 23.7965),
    "Χολαργός": (38.0041, 23.7923), "Παπάγου": (38.0000, 23.7873),
    "Πεύκη": (38.0606, 23.7923), "Μελίσσια": (38.0617, 23.8314),
    "Βριλήσσια": (38.0413, 23.8296), "Πεντέλη": (38.0651, 23.8650),
    "Δροσιά": (38.1112, 23.8432), "Άνοιξη": (38.1464, 23.8571),
    "Νέα Ιωνία": (38.0365, 23.7574), "Λυκόβρυση": (38.0720, 23.7830),
    "Θρακομακεδόνες": (38.1361, 23.7508), "Νέα Χαλκηδόνα": (38.0272, 23.7350),
    "Μεταμόρφωση": (38.0563, 23.7532), "Νέα Φιλαδέλφεια": (38.0361, 23.7383),
    "Μενίδι": (38.0833, 23.7365), "Ηράκλειο": (38.0465, 23.7674),
    "Πευκάκια": (38.0338, 23.7575), "Αιγάλεω": (37.9847, 23.6823),
    "Περιστέρι": (38.0155, 23.7039), "Ίλιον": (38.0356, 23.6997),
    "Χαιδάρι": (38.0113, 23.6661), "Καματερό": (38.0463, 23.6999),
    "Άγιοι Ανάργυροι": (38.0304, 23.7136), "Πειραιάς": (37.9429, 23.6460),
    "Κερατσίνι": (37.9627, 23.6191), "Δραπετσώνα": (37.9550, 23.6350),
    "Νίκαια": (37.9665, 23.6471), "Κορυδαλλός": (37.9844, 23.6472),
    "Σαλαμίνα": (37.9641, 23.4961), "Γέρακας": (38.0167, 23.8575),
    "Ανθούσα": (38.0348, 23.8797), "Παιανία": (37.9574, 23.8540),
    "Κορωπί": (37.8985, 23.8738), "Μαρκόπουλο": (37.8852, 23.9290),
    "Σπάτα": (37.9616, 23.9155), "Ραφήνα": (38.0181, 24.0055),
    "Αρτέμιδα (Λούτσα)": (37.9666, 24.0036), "Λαύριο": (37.7140, 24.0565),
    "Ανάβυσσος": (37.7333, 23.9440), "Σούνιο": (37.6525, 24.0184),
    "Μαραθώνας": (38.1495, 23.9669), "Ωρωπός": (38.3075, 23.7936),
    "Χαλκίδα": (38.4635, 23.5985), "Ελευσίνα": (38.0414, 23.5426),
    "Ασπρόπυργος": (38.0651, 23.5899), "Μαγούλα": (38.0800, 23.5544),
}

SORTED_LOCS = sorted(locations.keys())
STOP_DURATION = timedelta(minutes=20)


# ─────────────────────────────────────────────
# Λογική βελτιστοποίησης
# ─────────────────────────────────────────────

def km_to_td(km, speed):
    return timedelta(seconds=(km / speed) * 3600)


def evaluate_route(path, start_dt, required_times, speed, tol_min=5):
    cur = start_dt
    arrivals = {}
    dist_total = 0.0
    wait_total = timedelta(0)
    late_total = timedelta(0)
    feasible = True
    tol = timedelta(minutes=tol_min)

    for i, place in enumerate(path):
        is_last = (i == len(path) - 1)
        if i == 0:
            arr = cur
            if required_times.get(place):
                tgt = required_times[place]
                if arr > tgt + tol:
                    feasible = False; late_total += arr - tgt
                elif arr < tgt:
                    wait_total += tgt - arr; arr = tgt; cur = tgt
            arrivals[place] = arr
            if not is_last: cur = arr + STOP_DURATION
            continue

        prev = path[i - 1]
        d = geodesic(locations[prev], locations[place]).km
        dist_total += d
        arr = cur + km_to_td(d, speed)

        if required_times.get(place):
            tgt = required_times[place]
            if arr > tgt + tol:
                feasible = False; late_total += arr - tgt
                arrivals[place] = arr; cur = arr
            else:
                if arr < tgt: wait_total += tgt - arr; arr = tgt
                arrivals[place] = arr; cur = arr
        else:
            arrivals[place] = arr; cur = arr

        if not is_last: cur += STOP_DURATION

    return {
        'path': path, 'feasible': feasible, 'arrivals': arrivals,
        'dist_km': dist_total, 'total_time': cur - start_dt,
        'wait': wait_total, 'lateness': late_total,
    }


def greedy_path(start, end, inter, req_times, start_dt, speed):
    path, remaining, cur, cur_t = [start], inter.copy(), start, start_dt
    while remaining:
        def score(x):
            d = geodesic(locations[cur], locations[x]).km
            arr = cur_t + km_to_td(d, speed)
            penalty = max(timedelta(0), arr - req_times[x]).total_seconds() if req_times.get(x) else 0
            return d + penalty * 0.01
        nxt = min(remaining, key=score)
        d = geodesic(locations[cur], locations[nxt]).km
        cur_t += km_to_td(d, speed) + STOP_DURATION
        path.append(nxt); remaining.remove(nxt); cur = nxt
    return path + [end]


def optimize(start, end, inter, start_dt, req_times, speed):
    use_greedy = factorial(len(inter)) > 40320 if inter else False
    if use_greedy:
        p = greedy_path(start, end, inter, req_times, start_dt, speed)
        candidates = [evaluate_route(p, start_dt, req_times, speed)]
    else:
        candidates = [
            evaluate_route([start] + list(p) + [end], start_dt, req_times, speed)
            for p in permutations(inter)
        ] if inter else [evaluate_route([start, end], start_dt, req_times, speed)]

    feasible = [c for c in candidates if c['feasible']]
    if feasible:
        return min(feasible, key=lambda x: (x['total_time'], x['dist_km'])), True
    return min(candidates, key=lambda x: (x['lateness'], x['dist_km'])), False


def build_map(result, req_times):
    m = folium.Map(location=locations[result['path'][0]], zoom_start=11, tiles="CartoDB positron")
    path = result['path']
    for i, place in enumerate(path):
        arr = result['arrivals'].get(place)
        arr_s = arr.strftime('%H:%M') if arr else '—'
        req = req_times.get(place)
        req_s = req.strftime('%H:%M') if req else '—'
        popup = f"<b>{i}. {place}</b><br>Άφιξη: {arr_s}<br>Απαιτούμενη: {req_s}"
        color = 'pink' if i == 0 else ('red' if i == len(path)-1 else ('green' if req_times.get(place) else 'blue'))
        folium.Marker(
            locations[place], popup=popup,
            tooltip=f"{i}. {place} ({arr_s})",
            icon=folium.Icon(color=color)
        ).add_to(m)
    folium.PolyLine([locations[p] for p in path], color="#2563eb", weight=5, opacity=0.8).add_to(m)
    return m


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🗺️ Βελτιστοποιητής Διαδρομής Αθήνας</h1>
  <p>Βρες την καλύτερη σειρά επισκέψεων — με ώρες άφιξης, στάσεις και χάρτη</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar — Εισροές
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Παράμετροι")

    # Αφετηρία
    st.markdown("**🟢 Αφετηρία**")
    start_loc = st.selectbox("Επίλεξε αφετηρία", SORTED_LOCS,
                              index=SORTED_LOCS.index("Σύνταγμα"), key="start")
    use_start_time = st.checkbox("Ορισμός ώρας έναρξης", key="use_st")
    start_time = st.time_input("Ώρα έναρξης", value=dt_time(9, 0), key="st") if use_start_time else None

    st.markdown("---")

    # Τερματισμός
    st.markdown("**🔴 Τερματισμός**")
    end_loc = st.selectbox("Επίλεξε τερματισμό", SORTED_LOCS,
                            index=SORTED_LOCS.index("Πειραιάς"), key="end")
    use_end_time = st.checkbox("Ορισμός ώρας άφιξης στον τερματισμό", key="use_et")
    end_time = st.time_input("Ώρα άφιξης τερματισμού", value=dt_time(17, 0), key="et") if use_end_time else None

    st.markdown("---")

    # Παράμετροι
    st.markdown("**🚗 Παράμετροι**")
    speed_kmh = st.slider("Μέση ταχύτητα (km/h)", 10, 120, 30, 5)
    tol_min = st.slider("Ανοχή ώρας (λεπτά)", 0, 30, 5, 1)

    st.markdown("---")

    # Ενδιάμεσες στάσεις
    st.markdown("**🔵 Ενδιάμεσες Στάσεις**")
    num_stops = st.number_input("Αριθμός ενδιάμεσων στάσεων", 0, 12, 2, 1)

    intermediate_stops = []
    for i in range(int(num_stops)):
        st.markdown(f"*Στάση #{i+1}*")
        available = [l for l in SORTED_LOCS if l != start_loc and l != end_loc
                     and l not in [s['loc'] for s in intermediate_stops]]
        if not available:
            st.warning("Δεν υπάρχουν άλλες τοποθεσίες.")
            break
        loc = st.selectbox(f"Τοποθεσία", available, key=f"stop_{i}")
        use_t = st.checkbox("Συγκεκριμένη ώρα άφιξης", key=f"use_t_{i}")
        req_t = st.time_input("Ώρα", value=dt_time(10+i, 0), key=f"t_{i}") if use_t else None
        intermediate_stops.append({'loc': loc, 'req_time': req_t})

    st.markdown("---")
    calc_btn = st.button("🔍 Υπολόγισε Διαδρομή", use_container_width=True, type="primary")

# ─────────────────────────────────────────────
# Κύριο περιεχόμενο
# ─────────────────────────────────────────────
if calc_btn:
    # Validation
    all_locs = [start_loc] + [s['loc'] for s in intermediate_stops] + [end_loc]
    if len(all_locs) != len(set(all_locs)):
        st.error("⚠️ Υπάρχουν διπλότυπες τοποθεσίες. Παρακαλώ επέλεξε διαφορετικές στάσεις.")
        st.stop()

    # Χτίσε τα δεδομένα
    now = datetime.now()
    ref_date = now.date()
    start_dt = datetime.combine(ref_date, start_time) if start_time else now

    req_times = {}
    if use_start_time and start_time:
        req_times[start_loc] = datetime.combine(ref_date, start_time)
    for s in intermediate_stops:
        if s['req_time']:
            req_times[s['loc']] = datetime.combine(ref_date, s['req_time'])
    if use_end_time and end_time:
        req_times[end_loc] = datetime.combine(ref_date, end_time)

    intermediates = [s['loc'] for s in intermediate_stops]

    with st.spinner("⏳ Υπολογισμός βέλτιστης διαδρομής..."):
        result, all_feasible = optimize(start_loc, end_loc, intermediates, start_dt, req_times, speed_kmh)

    # ── Banner αποτελέσματος ──
    if all_feasible:
        st.success("✅ Βρέθηκε διαδρομή που ικανοποιεί **όλες** τις καθορισμένες ώρες!")
    else:
        st.warning("⚠️ Δεν υπάρχει τέλεια διαδρομή — εμφανίζεται αυτή με τη **μικρότερη καθυστέρηση**.")

    # ── Στατιστικά ──
    total_min = int(result['total_time'].total_seconds() / 60)
    wait_min = int(result['wait'].total_seconds() / 60)
    late_min = int(result['lateness'].total_seconds() / 60)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-val">{result['dist_km']:.1f}</div>
            <div class="stat-lbl">χιλιόμετρα</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-val">{total_min}</div>
            <div class="stat-lbl">λεπτά συνολικά</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-box">
            <div class="stat-val">{wait_min}</div>
            <div class="stat-lbl">λεπτά αναμονής</div></div>""", unsafe_allow_html=True)
    with c4:
        color = "#dc2626" if late_min > 0 else "#059669"
        st.markdown(f"""<div class="stat-box">
            <div class="stat-val" style="color:{color}">{late_min}</div>
            <div class="stat-lbl">λεπτά καθυστέρησης</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs: Χρονοδιάγραμμα / Χάρτης ──
    tab1, tab2 = st.tabs(["📋 Χρονοδιάγραμμα", "🗺️ Χάρτης"])

    with tab1:
        path = result['path']
        rows_html = ""
        for i, place in enumerate(path):
            arr = result['arrivals'].get(place)
            arr_s = arr.strftime('%H:%M') if arr else '—'
            req = req_times.get(place)
            req_s = req.strftime('%H:%M') if req else '—'

            # Badge
            if req and arr:
                diff = (arr - req).total_seconds() / 60
                if diff > tol_min:
                    badge = f'<span class="badge-late">+{diff:.0f}\' αργά</span>'
                elif diff < -1:
                    badge = f'<span class="badge-ok">{abs(diff):.0f}\' νωρίς</span>'
                else:
                    badge = '<span class="badge-ok">εντός</span>'
            else:
                badge = ''

            # Απόσταση από προηγούμενο
            dist_info = ""
            if i > 0:
                prev = path[i-1]
                d = geodesic(locations[prev], locations[place]).km
                t_m = int(km_to_td(d, speed_kmh).total_seconds() / 60)
                dist_info = f'<div class="stop-dist">↳ από {prev}: {d:.2f} km · {t_m} λεπτά οδήγησης</div>'

            # Αναχώρηση (εκτός τελευταίας)
            dep_info = ""
            if i < len(path) - 1 and arr:
                dep = (arr + STOP_DURATION).strftime('%H:%M')
                dep_info = f'<div class="stop-dist">🕒 Στάση 20 λεπτά → Αναχώρηση: {dep}</div>'

            icon_cls = "start" if i == 0 else ("end" if i == len(path)-1 else "middle")
            icon_txt = "🟢" if i == 0 else ("🔴" if i == len(path)-1 else str(i))

            rows_html += f"""
            <div class="stop-row">
              <div class="stop-icon {icon_cls}">{icon_txt}</div>
              <div>
                <div class="stop-name">{place} {badge}</div>
                <div class="stop-times">
                  Άφιξη: <b>{arr_s}</b>
                  {"&nbsp;·&nbsp;Απαιτούμενη: <b>" + req_s + "</b>" if req else ""}
                </div>
                {dist_info}
                {dep_info}
              </div>
            </div>"""

        st.markdown(f'<div class="route-card">{rows_html}</div>', unsafe_allow_html=True)

    with tab2:
        m = build_map(result, req_times)
        st_folium(m, use_container_width=True, height=520)

else:
    # Placeholder αρχικής οθόνης
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #94a3b8;">
        <div style="font-size: 64px;">🗺️</div>
        <div style="font-size: 20px; font-weight: 600; color: #475569; margin-top: 16px;">
            Ρύθμισε τις παραμέτρους στο πλευρικό μενού
        </div>
        <div style="font-size: 14px; margin-top: 8px;">
            Επίλεξε αφετηρία, τερματισμό, ενδιάμεσες στάσεις και πάτα <b>Υπολόγισε Διαδρομή</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
