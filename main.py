import streamlit as st
import requests
import pandas as pd
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==============================
# STREAMLIT CONFIG
# ==============================

st.set_page_config(layout="wide")
st.title("💀 Torn Predator AI - Fast Mug Scanner")

# ==============================
# INPUT
# ==============================

API_KEY = st.text_input("Torn LIMITED API Key", type="password")

scan_amount = st.slider("Players to Scan", 100, 10000, 2000)

min_level = st.slider("Min Level", 1, 100, 10)
max_level = st.slider("Max Level", 1, 100, 30)

min_networth = st.number_input(
    "Minimum Networth ($)",
    value=5_000_000
)

inactive_only = st.checkbox("Prefer Inactive Targets", value=True)

threads = st.slider("Scan Speed (Threads)", 5, 50, 25)

# ==============================
# OPTIMIZED REQUEST SESSION
# ==============================

session = requests.Session()

# ==============================
# FETCH PLAYER
# ==============================

def fetch_player(user_id):

    url = f"https://api.torn.com/user/{user_id}?selections=profile&key={API_KEY}"

    try:
        r = session.get(url, timeout=5).json()

        if "error" in r:
            return None

        level = r.get("level", 0)
        networth = r.get("networth", 0)

        if level == 0 or networth == 0:
            return None

        last_action = r["last_action"]["status"]

        if inactive_only:
            if last_action.lower() == "online":
                return None

        # ===== Weakness Estimation =====
        # Kaya tapi level kecil = empuk
        weak_score = networth / (level + 1)

        return {
            "ID": user_id,
            "Name": r["name"],
            "Level": level,
            "Networth": networth,
            "Last Action": last_action,
            "Weak Score": round(weak_score, 2),
            "Attack Link":
                f"https://www.torn.com/loader.php?sid=attack&user2ID={user_id}"
        }

    except:
        return None


# ==============================
# FAST SCANNER
# ==============================

def run_scan():

    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Smart player range (aktif area)
    ids = random.sample(range(500_000, 3_200_000), scan_amount)

    completed = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:

        futures = [executor.submit(fetch_player, uid) for uid in ids]

        for future in as_completed(futures):

            player = future.result()

            if player:
                if (
                    min_level <= player["Level"] <= max_level
                    and player["Networth"] >= min_networth
                ):
                    results.append(player)

            completed += 1

            progress_bar.progress(completed / scan_amount)
            status_text.text(
                f"Scanning {completed}/{scan_amount} players..."
            )

    return results


# ==============================
# START BUTTON
# ==============================

if st.button("🔥 START FAST SCAN"):

    if not API_KEY:
        st.error("Insert API Key first")
        st.stop()

    start = time.time()

    data = run_scan()

    end = time.time()

    if len(data) == 0:
        st.warning("No juicy targets found 😢")
    else:

        df = pd.DataFrame(data)

        df = df.sort_values(
            by="Weak Score",
            ascending=False
        )

        st.success(
            f"✅ Found {len(df)} Targets | Scan Time: {round(end-start,2)}s"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download Target List",
            csv,
            "torn_targets.csv",
            "text/csv"
        )
