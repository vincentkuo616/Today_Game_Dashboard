from datetime import datetime, timedelta
import json
import os  # ◄── 新增：用於檢查檔案是否存在
import sys
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import requests

# 🌟 自動獲取：今天、昨天、前天 三天的日期清單
dates_to_fetch = [
    datetime.now().strftime("%Y-%m-%d"),  # 今天
    (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),  # 昨天
    (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),  # 前天
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ==============================================================================
# 🛡️ 強化機制 A：載入現有的 JSON 檔案作為【歷史備份快取】
# ==============================================================================
existing_games_cache = {}  # 結構將會是：{"2026-07-03": [...games], "2026-07-02": [...]}
if os.path.exists("cpbl_live.json"):
    try:
        with open("cpbl_live.json", "r", encoding="utf-8") as f:
            old_data = json.load(f)
            # 將陣列結構扁平化為字典，方便後續用日期（Date Key）極速盲測比對
            for item in old_data:
                if "date" in item and "games" in item:
                    existing_games_cache[item["date"]] = item["games"]
        print(
            f"💾 成功讀取本機快取，已載入 {list(existing_games_cache.keys())} 的歷史數據備用。"
        )
    except Exception as e:
        print(f"⚠️ 讀取歷史舊檔失敗 ({e})，本次執行將不套用備份還原。")

cpbl_three_days_data = []

print(f"🚀 開始同步 CPBL 三日數據... ({dates_to_fetch[-1]} ~ {dates_to_fetch[0]})")

# 建立具備指數退避的重試策略
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=2,
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)

for date_str in dates_to_fetch:
    url = f"https://atplayertw.com.tw/wp-json/atplayertw/v1/sport-games/cpbl?date={date_str}"
    day_info = {"date": date_str, "games": []}
    fetch_success = False  # ◄── 狀態鎖：用來精確標記當天「線上資料」是否完美獲取

    try:
        response = session.get(url, headers=headers, timeout=(5, 10))
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("games"):
                fetch_success = True  # 線上通訊成功，且確實有撈到賽事陣列
                for game in data["games"]:
                    home_data = game.get("home", {})
                    away_data = game.get("away", {})

                    # 比分防禦
                    home_score = home_data.get("score")
                    away_score = away_data.get("score")
                    if home_score is None:
                        home_score = "-"
                    if away_score is None:
                        away_score = "-"

                    game_info = {
                        "id": game.get("id"),
                        "venue": game.get("venue_local"),
                        "display_time": game.get("display_time"),
                        "status_long": game.get("status_long", "Unknown"),
                        "status_key": game.get("status_key", ""),
                        "home_name": home_data.get("name_local"),
                        "away_name": away_data.get("name_local"),
                        "home_score": home_score,
                        "away_score": away_score,
                    }
                    day_info["games"].append(game_info)
            else:
                print(f"💡 {date_str} 遠端資料庫回傳 ok=False 或今日無任何一軍賽事。")
        else:
            print(f"⚠️ {date_str} 遠端伺服器回應狀態碼錯誤: {response.status_code}")

    except Exception as e:
        print(f"❌ 擷取 {date_str} 數據發生網路層或解析層異常: {e}")

    # ==============================================================================
    # 🛡️ 強化機制 B：斷線容錯與歷史資料智能還原（安全網）
    # ==============================================================================
    if not fetch_success:
        # 如果線上抓取失敗（不管是超時拋 Exception，還是狀態碼非 200），檢查舊檔案有沒有這天的資料
        if date_str in existing_games_cache:
            print(
                f"♻️  [防禦覆蓋] {date_str} 抓取失敗！已成功從舊 json 還原歷史暫存數據（共 {len(existing_games_cache[date_str])} 場賽事）。"
            )
            day_info["games"] = existing_games_cache[date_str]
        else:
            print(
                f"ℹ️  {date_str} 抓取失敗且歷史舊檔中無此日期紀錄，保持空賽事結構。"
            )

    cpbl_three_days_data.append(day_info)

# 寫入 json 檔案
with open("cpbl_live.json", "w", encoding="utf-8") as f:
    json.dump(cpbl_three_days_data, f, indent=2, ensure_ascii=False)

print("📝 CPBL 三日數據清洗與增量持久化處理完畢！")
