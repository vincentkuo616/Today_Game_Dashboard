from datetime import datetime
import json
import requests

# 🌟 自動獲取當天日期 (格式：2026-06-10)
today_str = datetime.now().strftime("%Y-%m-%d")

url = f"https://atplayertw.com.tw/wp-json/atplayertw/v1/sport-games/cpbl?date={today_str}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    output_games = []

    if response.status_code == 200:
        data = response.json()

        if data.get("ok") and data.get("games"):
            for game in data["games"]:
                home_data = game.get("home", {})
                away_data = game.get("away", {})

                # 防禦機制：處理比分為 None 的狀況
                home_score = home_data.get("score")
                away_score = away_data.get("score")
                if home_score is None:
                    home_score = "-"
                if away_score is None:
                    away_score = "-"

                status_long = game.get("status_long", "Unknown")
                status_key = game.get("status_key", "")

                # 建立結構化的乾淨資料給前端
                game_info = {
                    "id": game.get("id"),
                    "venue": game.get("venue_local"),
                    "display_time": game.get("display_time"),
                    "status_long": status_long,
                    "status_key": status_key,
                    "home_name": home_data.get("name_local"),
                    "away_name": away_data.get("name_local"),
                    "home_score": home_score,
                    "away_score": away_score,
                }
                output_games.append(game_info)

    # 寫入 json 檔案，供前端網頁讀取
    with open("cpbl_live.json", "w", encoding="utf-8") as f:
        json.dump(output_games, f, indent=2, ensure_ascii=False)
    print(f"📝 CPBL 數據同步成功！已寫入 cpbl_live.json (今日賽事: {len(output_games)} 場)")

except Exception as e:
    print(f"❌ CPBL 腳本執行失敗: {e}")
