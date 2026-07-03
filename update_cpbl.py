from datetime import datetime, timedelta
import json
import requests

# 🌟 自動獲取：今天、昨天、前天 三天的日期清單 (依序列出達成倒序)
dates_to_fetch = [
    datetime.now().strftime("%Y-%m-%d"),  # 今天
    (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),  # 昨天
    (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),  # 前天
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

cpbl_three_days_data = []

print(f"🚀 開始同步 CPBL 三日數據... ({dates_to_fetch[-1]} ~ {dates_to_fetch[0]})")

import sys
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# 建立具備指數退避（Exponential Backoff）的重試策略
retry_strategy = Retry(
    total=3,  # 最多重試 3 次
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=2,  # 每次重試間隔時間加倍 (2s, 4s, 8s)
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)

for date_str in dates_to_fetch:
    url = f"https://atplayertw.com.tw/wp-json/atplayertw/v1/sport-games/cpbl?date={date_str}"
    day_info = {"date": date_str, "games": []}

    try:
        # 強制設定 timeout=(連線逾時, 讀取逾時) 秒數，防止無限阻塞
        response = session.get(url, headers=headers, timeout=(5, 10))
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("games"):
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

        # 無論當天有沒有比賽，都把結構塞進去，確保前端知道這天沒事
        cpbl_three_days_data.append(day_info)

    except Exception as e:
        print(f"❌ 擷取 {date_str} 數據失敗: {e}")
        cpbl_three_days_data.append(day_info)

# 寫入 json 檔案
with open("cpbl_live.json", "w", encoding="utf-8") as f:
    json.dump(cpbl_three_days_data, f, indent=2, ensure_ascii=False)

print("📝 CPBL 三日歷史數據已完美寫入 cpbl_live.json！")
