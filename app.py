import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
from itertools import permutations
from math import factorial
from datetime import datetime, timedelta, time as dt_time

st.set_page_config(
    page_title="Βελτιστοποιητής Διαδρομής",
    page_icon="🗺️",
    layout="wide",
)

# Session state
for key, val in [
    ('result', None), ('all_feasible', None),
    ('req_times', {}), ('speed_used', 30), ('tol_used', 5),
    ('start_used', ''), ('end_used', ''),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Δεδομένα ──
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


# ── Λογική ──
def km_to_td(km, speed):
    return timedelta(seconds=(km / speed) * 3600)

def evaluate_route(path, start_dt, req_times, speed, tol_min=5):
    cur = start_dt
    arrivals = {}
    dist_total, wait_total, late_total = 0.0, timedelta(0), timedelta(0)
    feasible = True
    tol = timedelta(minutes=tol_min)

    for i, place in enumerate(path):
        is_last = (i == len(path) - 1)
        if i == 0:
            arr = cur
            if req_times.get(place):
                tgt = req_times[place]
                if arr > tgt + tol:
                    feasible = False; late_total += arr - tgt
                elif arr < tgt:
                    wait_total += tgt - arr; arr = tgt; cur = tgt
            arrivals[place] = arr
            # Δεν προσθέτουμε STOP_DURATION στην αφετηρία (δεν είναι στάση)
            continue

        prev = path[i - 1]
        d = geodesic(locations[prev], locations[place]).km
        dist_total += d
        arr = cur + km_to_td(d, speed)

        if req_times.get(place):
            tgt = req_times[place]
            if arr > tgt + tol:
                feasible = False; late_total += arr - tgt
                arrivals[place] = arr; cur = arr
            else:
                if arr < tgt: wait_total += tgt - arr; arr = tgt
                arrivals[place] = arr; cur = arr
        else:
            arrivals[place] = arr; cur = arr

        # STOP_DURATION μόνο στις ενδιάμεσες (όχι στην τελευταία)
        if not is_last:
            cur += STOP_DURATION

    return {
        'path': path, 'feasible': feasible, 'arrivals': arrivals,
        'dist_km': dist_total, 'total_time': cur - start_dt,
        'wait': wait_total, 'lateness': late_total,
    }

def greedy_path(start, end, inter, req_times, start_dt, speed):
    path, remaining, cur, cur_t = [start], inter.copy(), start, start_dt
    while remaining:
        def score(x, _c=cur, _t=cur_t):
            d = geodesic(locations[_c], locations[x]).km
            arr = _t + km_to_td(d, speed)
            p = max(timedelta(0), arr - req_times[x]).total_seconds() if req_times.get(x) else 0
            return d + p * 0.01
        nxt = min(remaining, key=score)
        d = geodesic(locations[cur], locations[nxt]).km
        cur_t += km_to_td(d, speed) + STOP_DURATION
        path.append(nxt); remaining.remove(nxt); cur = nxt
    return path + [end]

def optimize(start, end, inter, start_dt, req_times, speed, tol_min=5):
    if inter and factorial(len(inter)) > 40320:
        p = greedy_path(start, end, inter, req_times, start_dt, speed)
        candidates = [evaluate_route(p, start_dt, req_times, speed, tol_min)]
    elif inter:
        candidates = [evaluate_route([start]+list(p)+[end], start_dt, req_times, speed, tol_min)
                      for p in permutations(inter)]
    else:
        candidates = [evaluate_route([start, end], start_dt, req_times, speed, tol_min)]
    feasible = [c for c in candidates if c['feasible']]
    if feasible:
        return min(feasible, key=lambda x: (x['total_time'], x['dist_km'])), True
    return min(candidates, key=lambda x: (x['lateness'], x['dist_km'])), False


# ── Sidebar ──
with st.sidebar:
    st.title("🗺️ Ρυθμίσεις")

    st.subheader("🏠 Αφετηρία")
    st.caption("Από πού ξεκινάς (π.χ. σπίτι)")
    start_loc      = st.selectbox("Περιοχή αφετηρίας", SORTED_LOCS, index=SORTED_LOCS.index("Κηφισιά"), key="start")
    use_start_time = st.checkbox("Ορισμός ώρας αναχώρησης", key="use_st")
    start_time     = st.time_input("Ώρα αναχώρησης", value=dt_time(9, 0), key="st_time") if use_start_time else None

    st.divider()

    st.subheader("🏁 Τερματισμός")
    st.caption("Πού θέλεις να καταλήξεις (π.χ. σπίτι πάλι)")
    # Επιτρέπουμε ίδια αφετηρία/τερματισμός
    end_loc      = st.selectbox("Περιοχή τερματισμού", SORTED_LOCS, index=SORTED_LOCS.index("Κηφισιά"), key="end")
    use_end_time = st.checkbox("Ορισμός ώρας επιστροφής", key="use_et")
    end_time     = st.time_input("Ώρα επιστροφής", value=dt_time(17, 0), key="et_time") if use_end_time else None

    st.divider()

    st.subheader("🚗 Παράμετροι")
    speed_kmh = st.slider("Ταχύτητα (km/h)", 10, 120, 40, 5)
    tol_min   = st.slider("Ανοχή ώρας (λεπτά)", 0, 30, 5, 1)

    st.divider()

    st.subheader("📍 Στάσεις")
    st.caption("Οι περιοχές που θέλεις να επισκεφτείς")
    num_stops = st.number_input("Πλήθος στάσεων", 1, 12, 3, 1)

    intermediate_stops = []
    # Εξαιρούμε μόνο ήδη επιλεγμένες στάσεις (ΟΧΙ αφετηρία/τερματισμό)
    for i in range(int(num_stops)):
        st.markdown(f"**Στάση #{i+1}**")
        used  = {s['loc'] for s in intermediate_stops}
        avail = [l for l in SORTED_LOCS if l not in used]
        loc   = st.selectbox("Τοποθεσία", avail, key=f"stop_{i}")
        use_t = st.checkbox("Συγκεκριμένη ώρα άφιξης;", key=f"use_t_{i}")
        req_t = st.time_input("Ώρα άφιξης", value=dt_time(min(10+i, 23), 0), key=f"t_{i}") if use_t else None
        intermediate_stops.append({'loc': loc, 'req_time': req_t})

    st.divider()

    pressed = st.button("🔍 Υπολόγισε Διαδρομή", use_container_width=True, type="primary")

    if pressed:
        # Έλεγχος διπλότυπων μόνο ανάμεσα στις ενδιάμεσες στάσεις
        stop_locs = [s['loc'] for s in intermediate_stops]
        if len(stop_locs) != len(set(stop_locs)):
            st.error("Υπάρχουν διπλότυπες στάσεις!")
        else:
            now      = datetime.now()
            ref      = now.date()
            start_dt = datetime.combine(ref, start_time) if start_time else now

            req_times = {}
            for s in intermediate_stops:
                if s['req_time']:
                    req_times[s['loc']] = datetime.combine(ref, s['req_time'])
            if use_end_time and end_time:
                req_times[end_loc] = datetime.combine(ref, end_time)

            with st.spinner("⏳ Υπολογισμός βέλτιστης διαδρομής..."):
                res, feas = optimize(
                    start_loc, end_loc, stop_locs,
                    start_dt, req_times, speed_kmh, tol_min
                )

            st.session_state['result']       = res
            st.session_state['all_feasible'] = feas
            st.session_state['req_times']    = req_times
            st.session_state['speed_used']   = speed_kmh
            st.session_state['tol_used']     = tol_min
            st.session_state['start_used']   = start_loc
            st.session_state['end_used']     = end_loc


# ── Κύριο περιεχόμενο ──
st.title("🗺️ Βελτιστοποιητής Διαδρομής Αθήνας")

if st.session_state['result'] is None:
    st.info("👈 Ρύθμισε τις παραμέτρους στο πλευρικό μενού και πάτα **Υπολόγισε Διαδρομή**.")
    st.stop()

result       = st.session_state['result']
all_feasible = st.session_state['all_feasible']
req_times    = st.session_state['req_times']
speed_used   = st.session_state['speed_used']
tol_used     = st.session_state['tol_used']
start_used   = st.session_state['start_used']
end_used     = st.session_state['end_used']

if all_feasible:
    st.success("✅ Βρέθηκε διαδρομή που ικανοποιεί **όλες** τις καθορισμένες ώρες!")
else:
    st.warning("⚠️ Δεν υπάρχει τέλεια διαδρομή — εμφανίζεται αυτή με τη **μικρότερη καθυστέρηση**.")

# Στατιστικά
total_min = int(result['total_time'].total_seconds() / 60)
wait_min  = int(result['wait'].total_seconds() / 60)
late_min  = int(result['lateness'].total_seconds() / 60)

c1, c2, c3, c4 = st.columns(4)
c1.metric("📏 Απόσταση",          f"{result['dist_km']:.1f} km")
c2.metric("⏱️ Συνολικός χρόνος",  f"{total_min} λεπτά")
c3.metric("⏳ Αναμονή",           f"{wait_min} λεπτά")
c4.metric("🔴 Καθυστέρηση",       f"{late_min} λεπτά")

st.divider()

tab1, tab2 = st.tabs(["📋 Χρονοδιάγραμμα", "🗺️ Χάρτης"])

with tab1:
    path = result['path']

    # ── Αφετηρία ──
    start_arr = result['arrivals'].get(path[0])
    start_s   = start_arr.strftime('%H:%M') if start_arr else '—'
    st.markdown(f"### 🏠 Αναχώρηση από **{start_used}**")
    st.write(f"**Ώρα αναχώρησης:** {start_s}")
    st.divider()

    # ── Ενδιάμεσες στάσεις (όλες εκτός πρώτης και τελευταίας) ──
    for i in range(1, len(path) - 1):
        place = path[i]
        arr   = result['arrivals'].get(place)
        arr_s = arr.strftime('%H:%M') if arr else '—'
        req   = req_times.get(place)
        req_s = req.strftime('%H:%M') if req else '—'

        st.markdown(f"### 📍 Στάση {i}: **{place}**")

        col_a, col_b = st.columns(2)
        col_a.write(f"**Άφιξη:** {arr_s}")
        if req:
            diff = (arr - req).total_seconds() / 60 if arr else 0
            if diff > tol_used:
                col_b.write(f"**Απαιτούμενη:** {req_s} ⚠️ +{diff:.0f}' αργά")
            elif diff < -1:
                col_b.write(f"**Απαιτούμενη:** {req_s} ✅ {abs(diff):.0f}' νωρίς")
            else:
                col_b.write(f"**Απαιτούμενη:** {req_s} ✅ εντός")

        prev = path[i-1]
        d    = geodesic(locations[prev], locations[place]).km
        t_m  = int(km_to_td(d, speed_used).total_seconds() / 60)
        st.caption(f"↳ από {prev}: {d:.2f} km · {t_m} λεπτά οδήγησης")

        if arr:
            dep = (arr + STOP_DURATION).strftime('%H:%M')
            st.caption(f"🕒 Στάση 20 λεπτά → Αναχώρηση: {dep}")

        st.divider()

    # ── Τερματισμός ──
    end_arr = result['arrivals'].get(path[-1])
    end_s   = end_arr.strftime('%H:%M') if end_arr else '—'
    prev    = path[-2]
    d_end   = geodesic(locations[prev], locations[path[-1]]).km
    t_end   = int(km_to_td(d_end, speed_used).total_seconds() / 60)
    req_end = req_times.get(path[-1])
    req_end_s = req_end.strftime('%H:%M') if req_end else '—'

    st.markdown(f"### 🏁 Επιστροφή στο **{end_used}**")
    col_a, col_b = st.columns(2)
    col_a.write(f"**Άφιξη:** {end_s}")
    if req_end:
        diff = (end_arr - req_end).total_seconds() / 60 if end_arr else 0
        if diff > tol_used:
            col_b.write(f"**Απαιτούμενη:** {req_end_s} ⚠️ +{diff:.0f}' αργά")
        else:
            col_b.write(f"**Απαιτούμενη:** {req_end_s} ✅")
    st.caption(f"↳ από {prev}: {d_end:.2f} km · {t_end} λεπτά οδήγησης")

with tab2:
    m = folium.Map(location=locations[path[0]], zoom_start=11, tiles="CartoDB positron")

    for i, place in enumerate(path):
        arr   = result['arrivals'].get(place)
        arr_s = arr.strftime('%H:%M') if arr else '—'
        req   = req_times.get(place)
        req_s = req.strftime('%H:%M') if req else '—'

        if i == 0:
            color = 'green'
            label = f"🏠 Αναχώρηση: {arr_s}"
        elif i == len(path) - 1:
            color = 'red'
            label = f"🏁 Επιστροφή: {arr_s}"
        else:
            color = 'blue'
            label = f"📍 Στάση {i}: {arr_s}"

        folium.Marker(
            locations[place],
            popup=f"<b>{place}</b><br>{label}<br>{'Απαιτούμενη: ' + req_s if req else ''}",
            tooltip=f"{i}. {place} ({arr_s})",
            icon=folium.Icon(color=color)
        ).add_to(m)

    folium.PolyLine([locations[p] for p in path], color="#2563eb", weight=5).add_to(m)
    st_folium(m, use_container_width=True, height=520)
