import streamlit as st
import requests
import pandas as pd
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide")
st.title("💀 Torn Weak Player Finder")

API_KEY = st.text_input("LIMITED API KEY", type="password")

scan_amount = st.slider("Scan Players", 100, 5000, 1500)

min_level = st.slider("Min Level",1,100,10)
max_level = st.slider("Max Level",1,100,35)

inactive_only = st.checkbox("Inactive Only",True)

threads = st.slider("Threads",5,40,20)

session = requests.Session()

def weakness_rank(rank):

    weak_ranks = [
        "Absolute beginner",
        "Beginner",
        "Inexperienced",
        "Rookie",
        "Novice"
    ]

    return rank in weak_ranks


def fetch(uid):

    try:
        url=f"https://api.torn.com/user/{uid}?selections=profile&key={API_KEY}"
        r=session.get(url,timeout=5).json()

        if "error" in r:
            return None

        level=r["level"]
        rank=r["rank"]
        status=r["last_action"]["status"]

        if inactive_only and status.lower()=="online":
            return None

        if not(min_level<=level<=max_level):
            return None

        if not weakness_rank(rank):
            return None

        score=(100-level)

        return {
            "ID":uid,
            "Name":r["name"],
            "Level":level,
            "Rank":rank,
            "Status":status,
            "Weak Score":score,
            "Attack":
            f"https://www.torn.com/loader.php?sid=attack&user2ID={uid}"
        }

    except:
        return None


if st.button("🔥 Scan Weak Targets"):

    ids=random.sample(range(600000,3200000),scan_amount)

    results=[]
    progress=st.progress(0)

    with ThreadPoolExecutor(max_workers=threads) as ex:

        futures=[ex.submit(fetch,i) for i in ids]

        done=0

        for f in as_completed(futures):

            res=f.result()

            if res:
                results.append(res)

            done+=1
            progress.progress(done/scan_amount)

    if results:

        df=pd.DataFrame(results)
        df=df.sort_values("Weak Score",ascending=False)

        st.success(f"Found {len(df)} weak targets")

        st.dataframe(df,use_container_width=True)

    else:
        st.warning("Try increasing scan amount")
