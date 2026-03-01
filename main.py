import streamlit as st
import requests
import pandas as pd
import random
import time
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(layout="wide")

st.title("💀 Torn Predator AI - Mug Target Scanner")

# =====================
# INPUT
# =====================

API_KEY = st.text_input("Limited API Key", type="password")

scan_amount = st.slider("Jumlah Scan Player", 100, 5000, 1000)

min_level = st.slider("Min Level", 1, 100, 10)
max_level = st.slider("Max Level", 1, 100, 30)

min_networth = st.number_input(
    "Minimum Networth",
    value=5_000_000
)

max_total_stats = st.number_input(
    "Maximum Total Battle Stats",
    value=2_000_000
)

# =====================
# API CALL
# =====================

def fetch_player(user_id):

    url = f"https://api.torn.com/user/{user_id}?selections=profile,personalstats&key={API_KEY}"

    try:
        r = requests.get(url, timeout=5).json()

        if "error" in r:
            return None

        strength = r["personalstats"].get("strength",0)
        defense = r["personalstats"].get("defense",0)
        speed = r["personalstats"].get("speed",0)
        dexterity = r["personalstats"].get("dexterity",0)

        total_stats = strength+defense+speed+dexterity
        networth = r.get("networth",0)

        if total_stats == 0:
            return None

        mug_score = networth / total_stats

        return {
            "id": user_id,
            "name": r["name"],
            "level": r["level"],
            "networth": networth,
            "total_stats": total_stats,
            "mug_score": round(mug_score,2),
            "status": r["last_action"]["status"]
        }

    except:
        return None


# =====================
# SCANNER
# =====================

if st.button("🔥 START PREDATOR SCAN"):

    results = []

    progress = st.progress(0)

    ids = random.sample(range(1, 3_000_000), scan_amount)

    def worker(uid):

        player = fetch_player(uid)

        if not player:
            return None

        if (
            min_level <= player["level"] <= max_level
            and player["networth"] >= min_networth
            and player["total_stats"] <= max_total_stats
        ):
            return player

        return None

    with ThreadPoolExecutor(max_workers=15) as executor:

        for i, res in enumerate(executor.map(worker, ids)):

            if res:
                results.append(res)

            progress.progress((i+1)/scan_amount)

            time.sleep(0.05)

    if results:

        df = pd.DataFrame(results)

        df = df.sort_values(
            by="mug_score",
            ascending=False
        )

        df["attack"] = df["id"].apply(
            lambda x:
            f"https://www.torn.com/loader.php?sid=attack&user2ID={x}"
        )

        st.success(f"✅ Found {len(df)} JUICY TARGETS")

        st.dataframe(df, use_container_width=True)

    else:
        st.warning("No good prey found 🥲")
