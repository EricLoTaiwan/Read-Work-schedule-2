import streamlit as st
import pandas as pd
import re
import json
import os
import glob
from datetime import datetime
import pytz
import requests 

# ----------------- 嘗試載入 AI 相關套件 -----------------
try:
    from PIL import Image 
    import google.generativeai as genai 
    HAS_AI_MODULES = True
except ImportError:
    HAS_AI_MODULES = False
# --------------------------------------------------------

# 頁面基本設定
st.set_page_config(page_title="共用智慧班表系統", page_icon="✈️", layout="wide")

SHARED_FILE = "shared_schedule.json"
HISTORY_DIR = "schedule_history"
FLIGHT_DB_FILE = "flight_db.json"  

os.makedirs(HISTORY_DIR, exist_ok=True)

# ----------------- 動態航班資料庫管理模組 -----------------
def get_seed_flight_db():
    return {
        # === 東南亞區域線 ===
        "BR211": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 曼谷 (BKK)", "std": "08:20", "sta": "11:10", "duration": "3h 50m", "coords": [13.6900, 100.7501]},
        "BR212": {"aircraft": "B77M", "route": "曼谷 (BKK) ➔ 台北 (TPE)", "std": "12:10", "sta": "16:45", "duration": "3h 35m", "coords": [25.0797, 121.2342]},
        "BR201": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 曼谷 (BKK)", "std": "09:40", "sta": "12:25", "duration": "3h 45m", "coords": [13.6900, 100.7501]},
        "BR202": {"aircraft": "B77M", "route": "曼谷 (BKK) ➔ 台北 (TPE)", "std": "14:40", "sta": "19:15", "duration": "3h 35m", "coords": [25.0797, 121.2342]},
        "BR227": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 吉隆坡 (KUL)", "std": "09:30", "sta": "14:15", "duration": "4h 45m", "coords": [2.7456, 101.7099]},
        "BR228": {"aircraft": "B77M", "route": "吉隆坡 (KUL) ➔ 台北 (TPE)", "std": "15:25", "sta": "20:15", "duration": "4h 50m", "coords": [25.0797, 121.2342]},
        "BR237": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 雅加達 (CGK)", "std": "09:00", "sta": "13:20", "duration": "5h 20m", "coords": [-6.1256, 106.6558]},
        "BR238": {"aircraft": "B77M", "route": "雅加達 (CGK) ➔ 台北 (TPE)", "std": "14:20", "sta": "20:45", "duration": "5h 25m", "coords": [25.0797, 121.2342]},
        "BR391": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 胡志明市 (SGN)", "std": "09:20", "sta": "11:40", "duration": "3h 20m", "coords": [10.8188, 106.6519]},
        "BR392": {"aircraft": "B77M", "route": "胡志明市 (SGN) ➔ 台北 (TPE)", "std": "12:50", "sta": "17:15", "duration": "3h 25m", "coords": [25.0797, 121.2342]},
        "BR271": {"aircraft": "A321", "route": "台北 (TPE) ➔ 馬尼拉 (MNL)", "std": "09:10", "sta": "11:30", "duration": "2h 20m", "coords": [14.5090, 121.0194]},
        "BR272": {"aircraft": "A321", "route": "馬尼拉 (MNL) ➔ 台北 (TPE)", "std": "12:40", "sta": "15:00", "duration": "2h 20m", "coords": [25.0797, 121.2342]},
        "BR265": {"aircraft": "A333", "route": "台北 (TPE) ➔ 金邊 (PNH)", "std": "08:45", "sta": "11:10", "duration": "3h 25m", "coords": [11.5466, 104.8441]},
        "BR266": {"aircraft": "A333", "route": "金邊 (PNH) ➔ 台北 (TPE)", "std": "12:10", "sta": "16:35", "duration": "3h 25m", "coords": [25.0797, 121.2342]},
        "BR281": {"aircraft": "B78P", "route": "台北 (TPE) ➔ 宿霧 (CEB)", "std": "07:10", "sta": "10:05", "duration": "2h 55m", "coords": [10.3075, 123.9794]},
        "BR282": {"aircraft": "B78P", "route": "宿霧 (CEB) ➔ 台北 (TPE)", "std": "11:05", "sta": "14:00", "duration": "2h 55m", "coords": [25.0797, 121.2342]},
        "BR257": {"aircraft": "A321", "route": "台北 (TPE) ➔ 清邁 (CNX)", "std": "07:15", "sta": "10:30", "duration": "4h 15m", "coords": [18.7668, 98.9626]},
        "BR258": {"aircraft": "A321", "route": "清邁 (CNX) ➔ 台北 (TPE)", "std": "11:35", "sta": "16:35", "duration": "4h 00m", "coords": [25.0797, 121.2342]},
        "BR397": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 河內 (HAN)", "std": "09:00", "sta": "11:05", "duration": "3h 05m", "coords": [21.2212, 105.8072]},
        "BR398": {"aircraft": "B77M", "route": "河內 (HAN) ➔ 台北 (TPE)", "std": "12:05", "sta": "15:55", "duration": "2h 50m", "coords": [25.0797, 121.2342]},
        "BR383": {"aircraft": "A321", "route": "台北 (TPE) ➔ 峴港 (DAD)", "std": "09:45", "sta": "11:40", "duration": "2h 55m", "coords": [16.0439, 108.1994]},
        "BR384": {"aircraft": "A321", "route": "峴港 (DAD) ➔ 台北 (TPE)", "std": "14:10", "sta": "18:05", "duration": "2h 55m", "coords": [25.0797, 121.2342]},
        "BR231": {"aircraft": "A333", "route": "台北 (TPE) ➔ 檳城 (PEN)", "std": "09:20", "sta": "13:50", "duration": "4h 30m", "coords": [5.2971, 100.2769]},
        "BR232": {"aircraft": "A333", "route": "檳城 (PEN) ➔ 台北 (TPE)", "std": "14:50", "sta": "19:45", "duration": "4h 55m", "coords": [25.0797, 121.2342]},
        "BR233": {"aircraft": "A321", "route": "台北 (TPE) ➔ 克拉克 (CRK)", "std": "09:00", "sta": "11:00", "duration": "2h 00m", "coords": [15.1858, 120.5599]},
        "BR234": {"aircraft": "A321", "route": "克拉克 (CRK) ➔ 台北 (TPE)", "std": "12:00", "sta": "14:00", "duration": "2h 00m", "coords": [25.0797, 121.2342]},
        "BR255": {"aircraft": "A333", "route": "台北 (TPE) ➔ 峇里島 (DPS)", "std": "10:00", "sta": "15:20", "duration": "5h 20m", "coords": [-8.7482, 115.1675]},
        "BR256": {"aircraft": "A333", "route": "峇里島 (DPS) ➔ 台北 (TPE)", "std": "16:20", "sta": "21:35", "duration": "5h 15m", "coords": [25.0797, 121.2342]},
        "BR277": {"aircraft": "A333", "route": "台北 (TPE) ➔ 馬尼拉 (MNL)", "std": "15:30", "sta": "17:50", "duration": "2h 20m", "coords": [14.5090, 121.0194]},  
        "BR278": {"aircraft": "A333", "route": "馬尼拉 (MNL) ➔ 台北 (TPE)", "std": "18:50", "sta": "21:10", "duration": "2h 20m", "coords": [25.0797, 121.2342]},  
        # 📌 新增 BR1383, BR1384
        "BR1383": {"aircraft": "A321", "route": "台北 (TPE) ➔ 峴港 (DAD)", "std": "07:10", "sta": "09:05", "duration": "2h 55m", "coords": [16.0439, 108.1994]},
        "BR1384": {"aircraft": "A321", "route": "峴港 (DAD) ➔ 台北 (TPE)", "std": "10:20", "sta": "14:05", "duration": "2h 45m", "coords": [25.0797, 121.2342]},

        # === 東北亞與兩岸線 ===
        "BR178": {"aircraft": "B78N", "route": "台北 (TPE) ➔ 大阪 (KIX)", "std": "06:30", "sta": "10:10", "duration": "2h 40m", "coords": [34.4320, 135.2304]},
        "BR177": {"aircraft": "B78N", "route": "大阪 (KIX) ➔ 台北 (TPE)", "std": "11:10", "sta": "13:05", "duration": "2h 55m", "coords": [25.0797, 121.2342]},
        "BR130": {"aircraft": "B781", "route": "台北 (TPE) ➔ 大阪 (KIX)", "std": "13:35", "sta": "17:15", "duration": "2h 40m", "coords": [34.4320, 135.2304]},
        "BR129": {"aircraft": "B781", "route": "大阪 (KIX) ➔ 台北 (TPE)", "std": "18:30", "sta": "20:30", "duration": "3h 00m", "coords": [25.0797, 121.2342]},
        "BR198": {"aircraft": "B78P", "route": "台北 (TPE) ➔ 成田 (NRT)", "std": "08:50", "sta": "13:15", "duration": "3h 25m", "coords": [35.7647, 140.3863]},
        "BR197": {"aircraft": "B78P", "route": "成田 (NRT) ➔ 台北 (TPE)", "std": "14:15", "sta": "16:55", "duration": "3h 40m", "coords": [25.0797, 121.2342]},
        "BR189": {"aircraft": "A333", "route": "松山 (TSA) ➔ 羽田 (HND)", "std": "10:50", "sta": "13:30", "duration": "3h 40m", "coords": [35.5494, 139.7798]},
        "BR190": {"aircraft": "A333", "route": "羽田 (HND) ➔ 松山 (TSA)", "std": "14:30", "sta": "17:05", "duration": "3h 35m", "coords": [25.0697, 121.5526]},
        "BR158": {"aircraft": "A333", "route": "台北 (TPE) ➔ 小松 (KMQ)", "std": "06:35", "sta": "10:25", "duration": "2h 50m", "coords": [36.3934, 136.4070]},
        "BR157": {"aircraft": "A333", "route": "小松 (KMQ) ➔ 台北 (TPE)", "std": "11:45", "sta": "13:55", "duration": "3h 10m", "coords": [25.0797, 121.2342]},
        "BR106": {"aircraft": "A333", "route": "台北 (TPE) ➔ 福岡 (FUK)", "std": "08:10", "sta": "11:15", "duration": "2h 05m", "coords": [33.5859, 130.4507]},
        "BR105": {"aircraft": "A333", "route": "福岡 (FUK) ➔ 台北 (TPE)", "std": "12:15", "sta": "13:50", "duration": "2h 35m", "coords": [25.0797, 121.2342]},
        "BR116": {"aircraft": "A333", "route": "台北 (TPE) ➔ 札幌 (CTS)", "std": "09:30", "sta": "14:05", "duration": "3h 35m", "coords": [42.7752, 141.6923]},
        "BR115": {"aircraft": "A333", "route": "札幌 (CTS) ➔ 台北 (TPE)", "std": "15:20", "sta": "18:40", "duration": "4h 20m", "coords": [25.0797, 121.2342]},
        "BR122": {"aircraft": "A321", "route": "台北 (TPE) ➔ 青森 (AOJ)", "std": "10:00", "sta": "14:30", "duration": "3h 30m", "coords": [40.7344, 140.6900]},
        "BR121": {"aircraft": "A321", "route": "青森 (AOJ) ➔ 台北 (TPE)", "std": "15:30", "sta": "18:45", "duration": "4h 15m", "coords": [25.0797, 121.2342]},
        "BR118": {"aircraft": "A321", "route": "台北 (TPE) ➔ 仙台 (SDJ)", "std": "10:05", "sta": "14:25", "duration": "3h 20m", "coords": [38.1397, 140.9169]},
        "BR117": {"aircraft": "A321", "route": "仙台 (SDJ) ➔ 台北 (TPE)", "std": "16:05", "sta": "19:00", "duration": "3h 55m", "coords": [25.0797, 121.2342]},
        "BR160": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 首爾 (ICN)", "std": "15:15", "sta": "18:45", "duration": "2h 30m", "coords": [37.4602, 126.4407]},
        "BR159": {"aircraft": "B77M", "route": "首爾 (ICN) ➔ 台北 (TPE)", "std": "19:45", "sta": "21:40", "duration": "2h 55m", "coords": [25.0797, 121.2342]},
        "BR164": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 首爾 (ICN)", "std": "07:20", "sta": "10:50", "duration": "2h 30m", "coords": [37.4602, 126.4407]},  
        "BR163": {"aircraft": "B77M", "route": "首爾 (ICN) ➔ 台北 (TPE)", "std": "11:40", "sta": "13:35", "duration": "2h 55m", "coords": [25.0797, 121.2342]},  
        "BR156": {"aircraft": "A333", "route": "松山 (TSA) ➔ 首爾 (GMP)", "std": "09:20", "sta": "12:50", "duration": "2h 30m", "coords": [37.5583, 126.7906]},
        "BR155": {"aircraft": "A333", "route": "首爾 (GMP) ➔ 松山 (TSA)", "std": "13:50", "sta": "15:45", "duration": "2h 55m", "coords": [25.0697, 121.5526]},
        "BR120": {"aircraft": "A321", "route": "台北 (TPE) ➔ 釜山 (PUS)", "std": "07:55", "sta": "11:05", "duration": "2h 10m", "coords": [35.1795, 128.9382]},
        "BR119": {"aircraft": "A321", "route": "釜山 (PUS) ➔ 台北 (TPE)", "std": "12:05", "sta": "13:45", "duration": "2h 40m", "coords": [25.0797, 121.2342]},
        "BR716": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 北京 (PEK)", "std": "16:20", "sta": "19:35", "duration": "3h 15m", "coords": [40.0799, 116.6031]},
        "BR715": {"aircraft": "B77M", "route": "北京 (PEK) ➔ 台北 (TPE)", "std": "20:35", "sta": "23:45", "duration": "3h 10m", "coords": [25.0797, 121.2342]},
        "BR712": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 上海浦東 (PVG)", "std": "10:10", "sta": "12:05", "duration": "1h 55m", "coords": [31.1443, 121.8083]},
        "BR711": {"aircraft": "B77M", "route": "上海浦東 (PVG) ➔ 台北 (TPE)", "std": "13:10", "sta": "15:05", "duration": "1h 55m", "coords": [25.0797, 121.2342]},
        "BR772": {"aircraft": "A333", "route": "松山 (TSA) ➔ 上海虹橋 (SHA)", "std": "14:40", "sta": "16:40", "duration": "2h 00m", "coords": [31.1979, 121.3363]},
        "BR771": {"aircraft": "A333", "route": "上海虹橋 (SHA) ➔ 松山 (TSA)", "std": "19:40", "sta": "21:45", "duration": "2h 05m", "coords": [25.0697, 121.5526]},
        "BR707": {"aircraft": "B77M", "route": "台北 (TPE) ➔ 廣州 (CAN)", "std": "08:25", "sta": "10:35", "duration": "2h 10m", "coords": [23.3924, 113.2988]},
        "BR708": {"aircraft": "B77M", "route": "廣州 (CAN) ➔ 台北 (TPE)", "std": "11:55", "sta": "14:00", "duration": "2h 05m", "coords": [25.0797, 121.2342]},
        "BR891": {"aircraft": "A321", "route": "台北 (TPE) ➔ 廈門 (XMN)", "std": "09:50", "sta": "11:35", "duration": "1h 45m", "coords": [24.5440, 118.1277]},
        "BR892": {"aircraft": "A321", "route": "廈門 (XMN) ➔ 台北 (TPE)", "std": "13:00", "sta": "14:45", "duration": "1h 45m", "coords": [25.0797, 121.2342]},
        "BR765": {"aircraft": "A333", "route": "台北 (TPE) ➔ 成都 (TFU)", "std": "14:30", "sta": "18:15", "duration": "3h 45m", "coords": [30.2725, 104.4372]},
        "BR766": {"aircraft": "A333", "route": "成都 (TFU) ➔ 台北 (TPE)", "std": "19:30", "sta": "22:50", "duration": "3h 20m", "coords": [25.0797, 121.2342]},
        "BR739": {"aircraft": "A321", "route": "台北 (TPE) ➔ 重慶 (CKG)", "std": "14:35", "sta": "17:50", "duration": "3h 15m", "coords": [29.7196, 106.6416]},
        "BR740": {"aircraft": "A321", "route": "重慶 (CKG) ➔ 台北 (TPE)", "std": "18:50", "sta": "21:50", "duration": "3h 00m", "coords": [25.0797, 121.2342]},
        "BR758": {"aircraft": "A333", "route": "台北 (TPE) ➔ 杭州 (HGH)", "std": "16:25", "sta": "18:25", "duration": "2h 00m", "coords": [30.2295, 120.4345]},  
        "BR757": {"aircraft": "A333", "route": "杭州 (HGH) ➔ 台北 (TPE)", "std": "19:35", "sta": "21:30", "duration": "1h 55m", "coords": [25.0797, 121.2342]},  
        "BR851": {"aircraft": "A321", "route": "台北 (TPE) ➔ 香港 (HKG)", "std": "08:15", "sta": "10:05", "duration": "1h 50m", "coords": [22.3080, 113.9185]},
        "BR852": {"aircraft": "A321", "route": "香港 (HKG) ➔ 台北 (TPE)", "std": "11:15", "sta": "13:00", "duration": "1h 45m", "coords": [25.0797, 121.2342]},
        "BR867": {"aircraft": "B781/B77M", "route": "台北 (TPE) ➔ 香港 (HKG)", "std": "10:05", "sta": "12:05", "duration": "2h 00m", "coords": [22.3080, 113.9185]},
        "BR868": {"aircraft": "B781/B77M", "route": "香港 (HKG) ➔ 台北 (TPE)", "std": "13:30", "sta": "15:20", "duration": "1h 50m", "coords": [25.0797, 121.2342]},
        "BR871": {"aircraft": "B781", "route": "台北 (TPE) ➔ 香港 (HKG)", "std": "16:40", "sta": "18:30", "duration": "1h 50m", "coords": [22.3080, 113.9185]},
        "BR872": {"aircraft": "B781", "route": "香港 (HKG) ➔ 台北 (TPE)", "std": "19:40", "sta": "21:30", "duration": "1h 50m", "coords": [25.0797, 121.2342]},
        "BR869": {"aircraft": "B781/B77M", "route": "台北 (TPE) ➔ 香港 (HKG)", "std": "12:40", "sta": "14:45", "duration": "2h 05m", "coords": [22.3080, 113.9185]}, 
        "BR870": {"aircraft": "B781/B77M", "route": "香港 (HKG) ➔ 台北 (TPE)", "std": "15:25", "sta": "17:20", "duration": "1h 55m", "coords": [25.0797, 121.2342]}, 

        # === 美洲長程線 ===
        "BR10":  {"aircraft": "B77B", "route": "台北 (TPE) ➔ 溫哥華 (YVR)", "std": "23:55", "sta": "19:40", "duration": "11h 45m", "coords": [49.1967, -123.1815]}, 
        "BR9":   {"aircraft": "B77B", "route": "溫哥華 (YVR) ➔ 台北 (TPE)", "std": "02:00", "sta": "05:25", "duration": "13h 25m", "coords": [25.0797, 121.2342]},
        "BR18":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 舊金山 (SFO)", "std": "19:40", "sta": "16:00", "duration": "11h 20m", "coords": [37.6189, -122.3750]},
        "BR17":  {"aircraft": "B77M", "route": "舊金山 (SFO) ➔ 台北 (TPE)", "std": "01:00", "sta": "05:25", "duration": "13h 25m", "coords": [25.0797, 121.2342]},
        "BR12":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 洛杉磯 (LAX)", "std": "19:20", "sta": "16:10", "duration": "11h 50m", "coords": [33.9416, -118.4085]},
        "BR11":  {"aircraft": "B77M", "route": "洛杉磯 (LAX) ➔ 台北 (TPE)", "std": "00:05", "sta": "05:10", "duration": "14h 05m", "coords": [25.0797, 121.2342]},
        "BR32":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 紐約 (JFK)", "std": "19:10", "sta": "22:05", "duration": "14h 55m", "coords": [40.6413, -73.7781]},
        "BR31":  {"aircraft": "B77M", "route": "紐約 (JFK) ➔ 台北 (TPE)", "std": "01:25", "sta": "05:15", "duration": "15h 50m", "coords": [25.0797, 121.2342]},
        "BR26":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 西雅圖 (SEA)", "std": "23:40", "sta": "19:30", "duration": "10h 50m", "coords": [47.4502, -122.3088]},
        "BR25":  {"aircraft": "B77M", "route": "西雅圖 (SEA) ➔ 台北 (TPE)", "std": "01:50", "sta": "05:10", "duration": "12h 20m", "coords": [25.0797, 121.2342]},
        "BR56":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 芝加哥 (ORD)", "std": "20:00", "sta": "20:30", "duration": "14h 30m", "coords": [41.9742, -87.9073]},
        "BR55":  {"aircraft": "B77M", "route": "芝加哥 (ORD) ➔ 台北 (TPE)", "std": "00:30", "sta": "05:00", "duration": "15h 30m", "coords": [25.0797, 121.2342]},
        "BR52":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 休士頓 (IAH)", "std": "22:00", "sta": "22:25", "duration": "14h 25m", "coords": [29.9902, -95.3368]},
        "BR51":  {"aircraft": "B77M", "route": "休士頓 (IAH) ➔ 台北 (TPE)", "std": "00:15", "sta": "05:55", "duration": "16h 40m", "coords": [25.0797, 121.2342]},
        "BR40":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 華盛頓 (IAD 模擬)", "std": "19:30", "sta": "21:30", "duration": "14h 00m", "coords": [38.9531, -77.4565]},
        "BR39":  {"aircraft": "B77M", "route": "華盛頓 (IAD 模擬) ➔ 台北 (TPE)", "std": "23:55", "sta": "05:30", "duration": "15h 35m", "coords": [25.0797, 121.2342]},
        
        # === 歐洲長程線 ===
        "BR87":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 巴黎 (CDG)", "std": "23:50", "sta": "08:45", "duration": "14h 55m", "coords": [49.0097, 2.5479]},
        "BR88":  {"aircraft": "B77M", "route": "巴黎 (CDG) ➔ 台北 (TPE)", "std": "11:20", "sta": "06:30", "duration": "13h 10m", "coords": [25.0797, 121.2342]},
        "BR67":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 倫敦 (LHR)", "std": "08:40", "sta": "19:25", "duration": "17h 45m", "coords": [51.4700, -0.4543]},
        "BR68":  {"aircraft": "B77M", "route": "倫敦 (LHR) ➔ 台北 (TPE)", "std": "21:35", "sta": "21:15", "duration": "16h 40m", "coords": [25.0797, 121.2342]},
        "BR65":  {"aircraft": "B78P", "route": "台北 (TPE) ➔ 維也納 (VIE)", "std": "23:30", "sta": "07:15", "duration": "14h 45m", "coords": [48.1103, 16.5697]},
        "BR66":  {"aircraft": "B78P", "route": "維也納 (VIE) ➔ 台北 (TPE)", "std": "12:25", "sta": "06:30", "duration": "12h 05m", "coords": [25.0797, 121.2342]},
        "BR71":  {"aircraft": "B78P", "route": "台北 (TPE) ➔ 慕尼黑 (MUC)", "std": "23:25", "sta": "07:25", "duration": "14h 00m", "coords": [48.3537, 11.7861]},
        "BR72":  {"aircraft": "B78P", "route": "慕尼黑 (MUC) ➔ 台北 (TPE)", "std": "11:40", "sta": "06:40", "duration": "13h 00m", "coords": [25.0797, 121.2342]},
        "BR95":  {"aircraft": "B78P", "route": "台北 (TPE) ➔ 米蘭 (MXP)", "std": "23:15", "sta": "06:30", "duration": "14h 15m", "coords": [45.6301, 8.7231]},
        "BR96":  {"aircraft": "B78P", "route": "米蘭 (MXP) ➔ 台北 (TPE)", "std": "11:20", "sta": "06:20", "duration": "13h 00m", "coords": [25.0797, 121.2342]},
        "BR75":  {"aircraft": "B77M", "route": "台北 (TPE) ➔ 阿姆斯特丹 (AMS)", "std": "08:40", "sta": "19:35", "duration": "16h 55m", "coords": [52.3105, 4.7683]},
        "BR76":  {"aircraft": "B77M", "route": "阿姆斯特丹 (AMS) ➔ 台北 (TPE)", "std": "21:40", "sta": "20:05", "duration": "16h 25m", "coords": [25.0797, 121.2342]},
    }

def load_flight_db():
    seed_db = get_seed_flight_db()
    if os.path.exists(FLIGHT_DB_FILE):
        try:
            with open(FLIGHT_DB_FILE, 'r', encoding='utf-8') as f:
                saved_db = json.load(f)
                saved_db.update(seed_db) 
                return saved_db
        except:
            pass
            
    save_flight_db(seed_db)
    return seed_db

def save_flight_db(db_data):
    with open(FLIGHT_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=4)

def update_flight_db_with_ai(missing_flights, api_key):
    try:
        clean_key = api_key.strip()
        genai.configure(api_key=clean_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        你是一個長榮航空的航班資料庫。請提供以下航班的固定標準資訊：{missing_flights}
        請嚴格輸出 JSON Object (Dictionary)，鍵名為航班號碼。
        絕對不要包含 Markdown 標記，只能輸出 {{ 開頭的純 JSON 結構。
        範例格式：
        {{
            "BR130": {{"aircraft": "B781", "route": "台北 (TPE) ➔ 大阪 (KIX)", "std": "13:00", "sta": "16:30", "duration": "2h 30m", "coords": [34.4320, 135.2304]}}
        }}
        其中 coords 為目的地機場的 [緯度, 經度]。如果該航班是回台灣，coords請填台灣機場座標。
        """
        response = model.generate_content(prompt)
        raw_text = response.text
        
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            new_data = json.loads(match.group(0))
            current_db = load_flight_db()
            current_db.update(new_data)
            save_flight_db(current_db)
            return True
    except Exception as e:
        pass 
    return False

# ----------------- AI 視覺辨識核心模組 -----------------
if HAS_AI_MODULES:
    def extract_schedule_with_ai(image_source, api_key):
        try:
            clean_key = api_key.strip()
            genai.configure(api_key=clean_key)
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Quota" in error_msg:
                    raise ValueError("API 呼叫次數已達上限。")
                elif "400" in error_msg or "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
                    raise ValueError("API_KEY_INVALID")
                else:
                    raise ValueError(f"無法存取 Gemini 模型清單，請確認 API Key。錯誤: {e}")
            
            target_model = None
            for keyword in ['flash', 'pro', 'gemini']:
                matches = [m for m in available_models if keyword in m.lower()]
                if matches:
                    target_model = matches[0]
                    break
            if not target_model: raise ValueError("找不到支援內容生成的模型！")
            
            model = genai.GenerativeModel(target_model)
            img = Image.open(image_source)
            prompt = """
            你是一個專業的長榮航空班表分析專家。請嚴格分析這張班表截圖，提取每一天的「日期 (Date)」、「星期幾 (Day)」、以及格子內的「文字內容 (Content)」。
            請以 JSON Array 格式輸出。絕對不要包含 Markdown 標記。
            """
            response = model.generate_content([prompt, img])
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                raise ValueError("無法提取 JSON 陣列。")
        except Exception as e:
            error_str = str(e)
            if "API_KEY_INVALID" in error_str or "400" in error_str:
                st.error("🔑 **API Key 無效或格式錯誤 (400)**\n\n系統無法驗證您的身份！請確認您左側輸入的 Gemini API Key 是否完整且正確（不要多複製到空白），或是該金鑰已被刪除。")
            elif "429" in error_str or "Quota exceeded" in error_str:
                st.warning("⏳ **API 免費額度暫時用盡 (Quota Exceeded)** 請稍等約 1 分鐘後再試。")
            else:
                st.error(f"⚠️ AI 辨識失敗：\n{error_str}")
            return None

@st.cache_data(ttl=1800)
def get_real_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()['current_weather']
            temp = data['temperature']
            code = data['weathercode']
            rain = "有雨" if code in [51,53,55,61,63,65,80,81,82,95,96,99] else "無雨"
            snow = "有雪" if code in [71,73,75,77,85,86] else "無雪"
            return {"temp": f"{temp}°C", "rain": rain, "snow": snow}
    except Exception:
        pass 
    return {"temp": "--°C", "rain": "未知", "snow": "未知"}

@st.cache_data
def fetch_flight_info(flight_num):
    db = load_flight_db()
    
    if flight_num in db:
        info = db[flight_num].copy()
    else:
        info = {
            "aircraft": "依派遣而定",
            "route": "長榮航空航線 (詳細資料建檔中)",
            "std": "--:--",
            "sta": "--:--",
            "duration": "--h --m",
            "coords": [25.0797, 121.2342] 
        }

    weather_data = get_real_weather(info['coords'][0], info['coords'][1])
    info['weather'] = weather_data
    return info

# 📌 整合者更新：讓 Regex 能順利捕捉包含 PNC 或 (TSA) 的各種班表標記
def extract_flights_from_content(content):
    lines = str(content).split('\n')
    flights = []
    for line in lines:
        line = line.strip()
        if re.match(r'^(?:BR)?\d+(?:\s*PNC)?(?:\s*\(?TSA\)?)?$', line, flags=re.IGNORECASE):
            num = re.search(r'\d+', line).group()
            flights.append(f"BR{num}")
    return flights

def parse_and_format_content(content, enable_parsing=True, active_schedule_name=""):
    if not enable_parsing:
        return f"<div style='font-size:15px;'>{str(content).replace(chr(10), '<br>')}</div>"

    lines = str(content).split('\n')
    formatted_lines = []
    red_codes = ['DO', 'ADO', 'AL', 'YH', 'YI']
    active_sched_param = f"&schedule={active_schedule_name}" if active_schedule_name else ""
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line in ['AL']: 
            formatted_lines.append("<div style='color:#FF3B30; font-weight:700; font-size:16px; margin: 4px 0;'>🏖️ 特休 (AL)</div>")
        elif line in ['DO', 'ADO']: 
            formatted_lines.append(f"<div style='color:#FF3B30; font-weight:700; font-size:16px; margin: 4px 0;'>🏠 休假 ({line})</div>")
        elif line in ['YA', 'YB', 'YC']: 
            formatted_lines.append(f"<div style='color:#FF3B30; font-weight:700; font-size:16px; margin: 4px 0;'>🏖️ 指定休假 ({line})</div>")
        
        elif re.match(r'^\(\d+\)$', line): 
            formatted_lines.append(f"<div style='color:#8E8E93; font-size: 13px; font-weight:600; margin-bottom: 4px;'>{line}</div>")
        elif "SCS" in line: 
            formatted_lines.append(f"<div style='color:#FF9500; font-weight:800; font-size:16px; margin: 4px 0;'>🚨 待命 ({line.split()[0]})</div>")
        elif re.match(r'^\d{2}:\d{2}-\d{2}:\d{2}$', line): 
            formatted_lines.append(f"<div style='color:#AF52DE; font-weight:700; font-size:15px; margin: 4px 0;'>🕒 {line.replace('-', '~')}</div>")
        
        # 📌 整合者更新：先處理 PNC (乘客返回) 標籤
        elif "PNC" in line.upper() and re.search(r'\d+', line):
            f_num = re.search(r'\d+', line).group()
            flight_url = f"?flight=BR{f_num}{active_sched_param}"
            formatted_lines.append(f"<a href='{flight_url}' target='_self' style='display:inline-block; text-decoration:none; color:#007AFF; font-weight:800; font-size:16px; margin: 4px 0; background-color:#E5F1FF; padding:2px 6px; border-radius:6px; border: 1px dashed #007AFF;'>💺 BR{f_num} (乘客返回)</a>")
        
        # 📌 整合者更新：再處理 TSA (松山起降) 標籤
        elif "TSA" in line.upper() and re.search(r'\d+', line):
            f_num = re.search(r'\d+', line).group()
            flight_url = f"?flight=BR{f_num}{active_sched_param}"
            formatted_lines.append(f"<a href='{flight_url}' target='_self' style='display:inline-block; text-decoration:none; color:#10B981; font-weight:800; font-size:16px; margin: 4px 0; background-color:#D1FAE5; padding:2px 6px; border-radius:6px; border: 1px dashed #10B981;'>✈️ BR{f_num} (松山)</a>")
            
        elif re.match(r'^\d+$', line): 
            flight_url = f"?flight=BR{line}{active_sched_param}"
            formatted_lines.append(f"<a href='{flight_url}' target='_self' style='display:inline-block; text-decoration:none; color:#007AFF; font-weight:800; font-size:16px; margin: 4px 0; background-color:#E5F1FF; padding:2px 6px; border-radius:6px;'>✈️ BR{line}</a>")
        
        elif re.match(r'^[AB]\d{2,3}[a-zA-Z0-9]?$', line): 
            formatted_lines.append(f"<div style='color:#34C759; font-weight:700; font-size:15px; margin: 4px 0;'>🛩️ 機型: {line}</div>")
        elif line in red_codes: 
            formatted_lines.append(f"<div style='color:#FF3B30; font-weight:700; font-size:16px; margin: 4px 0;'>{line}</div>")
        else: 
            formatted_lines.append(f"<div style='font-size:15px; margin: 4px 0;'>{line}</div>")
            
    return "".join(formatted_lines)

def display_flight_info_panel(flight_num):
    info = fetch_flight_info(flight_num)
    st.markdown(f"### 🛫 航班詳細資訊: {flight_num}")
    st.markdown(f"<span style='font-size:18px;'>**🛬 回程航班:** {flight_num}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:18px;'>**✈️ 機型:** {info['aircraft']}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:18px;'>**🏢 航線:** {info['route']}</span>", unsafe_allow_html=True)
    
    weather_html = f"<div style='background-color: #007AFF; padding: 18px; border-radius: 12px; color: white; margin-top: 15px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,122,255,0.2);'><div style='font-size: 15px; margin-bottom: 8px; font-weight: 600; opacity: 0.9;'>☁️ 目的地/外站 出發天氣</div><div style='font-size: 20px; font-weight: 800; letter-spacing: 1px;'>🌡️ {info['weather']['temp']} &nbsp;|&nbsp; ☁️ {info['weather']['rain']} &nbsp;|&nbsp; ❌ {info['weather']['snow']}</div></div>"
    st.markdown(weather_html, unsafe_allow_html=True)
    
    st.markdown(f"<span style='font-size:16px;'>**⏱️ STD:**</span> <span style='float:right; font-weight:bold; font-size:18px;'>{info['std']}</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 12px 0px; border-top: 1px solid #E5E5EA;'>", unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:16px;'>**🛬 STA:**</span> <span style='float:right; font-weight:bold; font-size:18px;'>{info['sta']}</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 12px 0px; border-top: 1px solid #E5E5EA;'>", unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:16px;'>**⏱️ 總時間:**</span> <span style='float:right; font-weight:900; color:#007AFF; font-size:18px;'>{info['duration']}</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        flight_digits = re.search(r'\d+', flight_num).group()
    except AttributeError:
        flight_digits = ""
        
    url_domain = "zh-tw.flightaware.com"
    url_path = f"/live/flight/EVA{flight_digits}"
    flightaware_url = "https://" + url_domain + url_path

    st.link_button("✈️ 開啟 FlightAware 航班雷達動態", url=flightaware_url, type="primary", use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)

def main():
    tw_now = datetime.now(pytz.timezone('Asia/Taipei'))
    current_day_number = tw_now.day

    if 'initialized' not in st.session_state:
        st.session_state.selected_date = current_day_number
        st.session_state.selected_flight = None
        st.session_state.active_schedule = None
        st.session_state.api_key = "AIzaSyDfVqv1YsSBMr1RwapIrcHtwTuhFDz49Jg" 
        st.session_state.initialized = True

    if "schedule" in st.query_params:
        sched_name = st.query_params["schedule"]
        reconstruct_path = os.path.join(HISTORY_DIR, sched_name)
        if os.path.exists(reconstruct_path):
            st.session_state.active_schedule = reconstruct_path
    if "date" in st.query_params:
        st.session_state.selected_date = int(st.query_params["date"])
        st.session_state.selected_flight = None
    if "flight" in st.query_params:
        st.session_state.selected_flight = st.query_params["flight"]
        st.session_state.selected_date = None
    if st.query_params:
        st.query_params.clear()

    with st.sidebar:
        st.header("⚙️ 班表管理設定")
        if HAS_AI_MODULES:
            with st.expander("🔑 系統進階設定 (AI 辨識)", expanded=False):
                st.session_state.api_key = st.text_input("請輸入 Google Gemini API Key", value=st.session_state.api_key, type="password")
        else:
            st.error("⚠️ 缺少 AI 辨識套件！請安裝 google-generativeai 與 pillow")
        
        st.markdown("---")
        st.subheader("🖼️ 上傳新班表圖片")
        
        uploaded_image = st.file_uploader("請選擇班表圖片", type=['png', 'jpg', 'jpeg'])
        if uploaded_image is not None:
            save_path = os.path.join(HISTORY_DIR, uploaded_image.name)
            base_name = os.path.splitext(uploaded_image.name)[0]
            json_path = os.path.join(HISTORY_DIR, f"{base_name}.json")
            
            try:
                with open(save_path, "wb") as f:
                    f.write(uploaded_image.getbuffer())
                
                if not os.path.exists(json_path):
                    if HAS_AI_MODULES and st.session_state.api_key:
                        with st.spinner('🤖 AI 視覺模組正在努力解讀班表中，請稍候...'):
                            ai_data = extract_schedule_with_ai(save_path, st.session_state.api_key)
                            if ai_data:
                                with open(json_path, 'w', encoding='utf-8') as f:
                                    json.dump(ai_data, f, ensure_ascii=False, indent=4)
                                st.success("✨ AI 班表辨識成功！")
                                
                                all_parsed_flights = []
                                for day_data in ai_data:
                                    all_parsed_flights.extend(extract_flights_from_content(day_data.get('Content', '')))
                                unique_flights = list(set(all_parsed_flights))
                                
                                db = load_flight_db()
                                missing = [f for f in unique_flights if f not in db]
                                if missing:
                                    with st.spinner(f'🚀 發現 {len(missing)} 筆新航班！正在自動擴充內部資料庫...'):
                                        is_updated = update_flight_db_with_ai(missing, st.session_state.api_key)
                                        if is_updated:
                                            st.toast("✅ 新航班已永久學習並寫入隱性資料庫！")
                                
                            else:
                                pass 
                    else:
                        st.warning("✅ 圖片上傳成功，但未啟用 AI 解析。")
            except Exception as e:
                st.error(f"儲存失敗: {e}")
                        
        st.markdown("---")
        st.subheader("🔄 選擇並套用班表")
        
        files = glob.glob(os.path.join(HISTORY_DIR, "*.*"))
        img_files = sorted([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=os.path.getmtime, reverse=True)
        
        if not img_files:
            st.warning("目前沒有班表紀錄，請先上傳圖片。")
        else:
            options_dict = {f: f"📅 {os.path.basename(f)}" for f in img_files}
            default_index = img_files.index(st.session_state.active_schedule) if st.session_state.active_schedule in img_files else 0
                
            selected_file = st.selectbox("切換歷史班表：", options=img_files, format_func=lambda x: options_dict[x], index=default_index)
            
            if st.button("✅ 確定套用此班表", type="primary", use_container_width=True):
                st.session_state.active_schedule = selected_file
                st.rerun()
                
            if st.session_state.active_schedule and os.path.exists(st.session_state.active_schedule):
                st.markdown("<br>", unsafe_allow_html=True)
                st.image(st.session_state.active_schedule, caption="👁️ 目前生效的班表對照圖", use_container_width=True)
                
                if HAS_AI_MODULES and st.session_state.api_key:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🔄 強制 AI 重新辨識並覆寫資料", use_container_width=True):
                        with st.spinner('🤖 正在嚴格分析此班表並尋找適合的 AI 模型，請稍候...'):
                            ai_data = extract_schedule_with_ai(st.session_state.active_schedule, st.session_state.api_key)
                            if ai_data:
                                base_name = os.path.splitext(os.path.basename(st.session_state.active_schedule))[0]
                                active_json_path = os.path.join(HISTORY_DIR, f"{base_name}.json")
                                with open(active_json_path, 'w', encoding='utf-8') as f:
                                    json.dump(ai_data, f, ensure_ascii=False, indent=4)
                                st.success("✨ 覆寫成功！資料已強制更新為圖片內容。")
                                
                                all_parsed_flights = []
                                for day_data in ai_data:
                                    all_parsed_flights.extend(extract_flights_from_content(day_data.get('Content', '')))
                                unique_flights = list(set(all_parsed_flights))
                                db = load_flight_db()
                                missing = [f for f in unique_flights if f not in db]
                                if missing:
                                    with st.spinner(f'🚀 發現 {len(missing)} 筆新航班！正在自動擴充內部資料庫...'):
                                        update_flight_db_with_ai(missing, st.session_state.api_key)
                                        
                                st.rerun()

    st.title("✈️ 共享智慧班表系統")
    
    df = pd.DataFrame()
    if st.session_state.active_schedule:
        base_name = os.path.splitext(os.path.basename(st.session_state.active_schedule))[0]
        active_json_path = os.path.join(HISTORY_DIR, f"{base_name}.json")
        if os.path.exists(active_json_path):
            with open(active_json_path, 'r', encoding='utf-8') as f:
                df = pd.DataFrame(json.load(f))
    
    col1, col2 = st.columns([1, 1])
    with col1:
        enable_parsing = st.toggle("✨ 啟動智慧解讀模式", value=True)
    with col2:
        st.markdown(f"<div style='text-align: right; color: #8E8E93; font-weight: 600;'>🇹🇼 台灣現在時間: {tw_now.strftime('%m/%d %H:%M')}</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_sel, col_info = st.columns([1, 2])
    with col_sel:
        st.subheader("🔍 航班快速查詢")
        st.info("💡 點擊下方日曆的日期或航班號碼，右側即會展開詳細資訊！", icon="👆")

    with col_info:
        if st.session_state.selected_flight:
            with st.container():
                display_flight_info_panel(st.session_state.selected_flight)
        elif st.session_state.selected_date and not df.empty:
            date_val = st.session_state.selected_date
            selected_day_data = df[df['Date'] == date_val]
            if not selected_day_data.empty:
                flights_on_date = extract_flights_from_content(selected_day_data.iloc[0]['Content'])
                if flights_on_date:
                    st.markdown(f"#### 📅 {date_val} 號 執勤航班總覽")
                    for idx, f in enumerate(flights_on_date):
                        with st.container():
                            display_flight_info_panel(f)
                else:
                    st.info(f"📅 您選擇的日期 ({date_val} 號) 無排定航班，或為休假/待命。好好休息！☕")
        else:
            st.warning("👈 尚未選擇航班或日期。請點擊下方日曆。")

    st.markdown("---")
    st.subheader("🗓️ 班表總覽")
    
    if df.empty:
        if st.session_state.active_schedule:
            empty_html = f"""
            <div style='text-align: center; padding: 50px; background-color: #FFF3CD; border-radius: 15px; border: 2px dashed #FFC107; margin-top: 20px;'>
                <h2 style='color: #856404;'>⚠️ 班表圖片已選擇，但尚未生成資料</h2>
                <p style='color: #856404; font-size: 18px;'>這可能是因為初次上傳時 AI 遇到網路延遲或額度限制。<br>請檢查左側的 <b>API Key 是否正確</b>，然後點擊左側選單最下方的 <b>「🔄 強制 AI 重新辨識並覆寫資料」</b> 按鈕來生成專屬日曆！</p>
            </div>
            """
        else:
            empty_html = "<div style='text-align: center; padding: 50px; background-color: #f8f9fa; border-radius: 15px; border: 2px dashed #ccc; margin-top: 20px;'><h2 style='color: #6c757d;'>📭 系統目前是空的</h2><p style='color: #6c757d; font-size: 18px;'>請上傳班表截圖，AI 會為您生成日曆！</p></div>"
        st.markdown(empty_html, unsafe_allow_html=True)
    else:
        days_of_week = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        first_day_str = str(df.iloc[0]['Day']).upper()
        start_day_index = days_of_week.index(first_day_str) if first_day_str in days_of_week else 0

        grid_html = "<div style='width: 100%; overflow-x: auto; padding-bottom: 15px;'><div style='display: grid; grid-template-columns: repeat(7, minmax(130px, 1fr)); gap: 12px; min-width: 900px;'>"
        for day in days_of_week:
            color = "#FF3B30" if day in ["SUN", "SAT"] else "#1C1C1E"
            grid_html += f"<div style='text-align: center; color: {color}; font-weight:800; font-size:16px; padding-bottom: 8px; border-bottom: 2px solid #E5E5EA;'>{day}</div>"

        current_day = 1
        total_days = len(df) 
        active_schedule_name = os.path.basename(st.session_state.active_schedule) if st.session_state.active_schedule else ""

        for week in range(6):
            if current_day > total_days: break
            for day_idx in range(7):
                if week == 0 and day_idx < start_day_index:
                    grid_html += "<div style='height: 180px; background-color: #F2F2F7; border-radius: 12px;'></div>"
                elif current_day <= total_days:
                    day_data = df[df['Date'] == current_day].iloc[0]
                    parsed_html = parse_and_format_content(day_data['Content'], enable_parsing, active_schedule_name)
                    
                    is_today = (current_day == current_day_number)
                    bg_color = "#FFFFE5" if is_today else ("#FFFAFA" if day_idx in [0, 6] else "#FFFFFF")
                    border_style = "2px solid #007AFF" if is_today else "1px solid #E5E5EA"
                    box_shadow = "0 4px 12px rgba(0, 122, 255, 0.15)" if is_today else "0 2px 8px rgba(0, 0, 0, 0.04)"
                    today_badge = "<span style='float: right; background-color: #007AFF; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight:800;'>TODAY</span>" if is_today else ""
                    date_color = "#FF3B30" if day_idx in [0, 6] else "#1C1C1E"
                    
                    active_sched_param = f"&schedule={active_schedule_name}" if active_schedule_name else ""
                    date_link_html = f"<a href='?date={current_day}{active_sched_param}' target='_self' style='text-decoration:none; color:{date_color}; cursor:pointer;'>{current_day}</a>"

                    grid_html += f"<div style='height: 180px; padding: 12px; background-color: {bg_color}; border: {border_style}; border-radius: 12px; box-shadow: {box_shadow}; overflow-y: auto; line-height: 1.6;'><div style='font-size: 18px; font-weight: 800; border-bottom: 1px solid #E5E5EA; padding-bottom: 4px; margin-bottom: 8px;'>{date_link_html} {today_badge}</div><div>{parsed_html}</div></div>"
                    current_day += 1
                else:
                    grid_html += "<div style='height: 180px; background-color: #F2F2F7; border-radius: 12px;'></div>"

        grid_html += "</div></div>" 
        st.markdown(grid_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()