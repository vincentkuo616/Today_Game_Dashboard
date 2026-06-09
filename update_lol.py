import requests
import json
from datetime import datetime
from collections import defaultdict

# === 🔐 你的 Bot 資訊 ===
BOT_USER = "Vincent1996616@vincent1996616"        
BOT_PASS = "ai6v4jqkc2a8dcnf1rbfge6um2qfsapq"  
# =======================================

today_str = datetime.now().strftime('%Y-%m-%d')
print(f"今天的日期是：{today_str}")

session = requests.Session()
session.headers.update({
    "User-Agent": "VincentKuoLeagueBot/1.0 (contact: vincent.kuo@example.com)"
})

url = "https://lol.fandom.com/api.php"

try:
    print("【步驟 1】正在獲取登入 Token...")
    init_token_params = {"action": "query", "meta": "tokens", "type": "login", "format": "json"}
    r1 = session.get(url, params=init_token_params).json()
    login_token = r1["query"]["tokens"]["logintoken"]

    print("【步驟 2】正在登入認證 Bot 帳號...")
    login_params = {
        "action": "login",
        "lgname": BOT_USER,
        "lgpassword": BOT_PASS,
        "lgtoken": login_token,
        "format": "json"
    }
    r2 = session.post(url, data=login_params).json()
    
    if r2.get("login", {}).get("result") == "Success":
        print("【步驟 3】登入成功！正在撈取近期的逐場小局數據...")
        
        # 🌟 這裡回復撈取詳細欄位（不讓資料庫做 group，由 Python 來做精準聚合）
        cargo_params = {
            "action": "cargoquery",
            "tables": "ScoreboardGames",
            "fields": "OverviewPage, DateTime_UTC, Team1, Team2, WinTeam",
            "order_by": "DateTime_UTC DESC",
            "limit": "100", 
            "format": "json"
        }
        
        response = session.get(url, params=cargo_params).json()
        
        if "error" in response:
            print("\n❌ 伺服器回傳了錯誤：")
            print(json.dumps(response, indent=2, ensure_ascii=False))
        else:
            print("\n--- 🎉 成功取得原始資料，開始進行系列賽比分統計 ---")
            raw_list = response.get("cargoquery", [])
            
            # 用來聚合 BO 系列賽的字典
            # Key 格式: (OverviewPage, 排序後的兩隊名稱) -> 確保不論選邊怎麼換，都能聚在同一場
            matches_dict = {}
            
            for item in raw_list:
                game = item.get("title", {})
                overview_page = game.get("OverviewPage")
                t1 = game.get("Team1")
                t2 = game.get("Team2")
                win_team = game.get("WinTeam")
                date_time = game.get("DateTime UTC") or game.get("DateTime_UTC")
                
                if not (overview_page and t1 and t2 and win_team):
                    continue
                
                # 🌟 核心魔法：將兩隊名字排序。不論是 (BLG, AL) 還是 (AL, BLG)，排序後都是 ('Anyone\'s Legend', 'Bilibili Gaming')
                teams_key = tuple(sorted([t1, t2]))
                match_id = (overview_page, teams_key)
                
                # 如果這個系列賽還沒記錄過，先初始化
                if match_id not in matches_dict:
                    matches_dict[match_id] = {
                        "OverviewPage": overview_page,
                        "TeamA": teams_key[0],
                        "TeamB": teams_key[1],
                        "ScoreA": 0,
                        "ScoreB": 0,
                        "LatestGameTime": date_time
                    }
                
                # 累加勝場分數
                if win_team == teams_key[0]:
                    matches_dict[match_id]["ScoreA"] += 1
                elif win_team == teams_key[1]:
                    matches_dict[match_id]["ScoreB"] += 1
                    
                # 更新該系列賽最新的一局時間
                if date_time > matches_dict[match_id]["LatestGameTime"]:
                    matches_dict[match_id]["LatestGameTime"] = date_time

            # 轉換成乾淨的清單結構
            all_grouped_matches = list(matches_dict.values())
            
            # 篩選出今天 (2026-06-09) 有打的比賽
            # 註：如果想看昨天的 LPL（6/8），可以把下面的 today_str 改成 "2026-06-08" 測試
            # today_matches = [m for m in all_grouped_matches if m["LatestGameTime"].startswith(today_str)]
            
            # if today_matches:
            #     print(f"🎯 成功！今天 ({today_str}) 的系列賽最終比分如下：")
            #     print(json.dumps(today_matches, indent=2, ensure_ascii=False))
            # else:
            #     print(f"最近抓到的 50 筆小局中，篩選完後剛好沒有今天 ({today_str}) 的比賽。")
            #     print(f"\n💡 為您印出最新的 50 場【系列賽大局結果】（包含歷史對決統計）：")
            #     print(json.dumps(all_grouped_matches[:50], indent=2, ensure_ascii=False))
            print(f"最近抓到的 100 筆小局中。")
            print(f"\n💡 為您印出最新的 50 場【系列賽大局結果】（包含歷史對決統計）：")
            print(json.dumps(all_grouped_matches[:50], indent=2, ensure_ascii=False))
        
    else:
        print(f"❌ 登入失敗：{r2}")

except Exception as e:
    print(f"\n發生錯誤：{e}")

# === 程式碼最末端 ===
# 不管是今天有比賽，還是吐出最近 50 場，我們都統一把結果存成 JSON 檔案
output_data = today_matches if today_matches else all_grouped_matches[:50]

with open('lol_live.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print("📝 成功將最新系列賽比分寫入 lol_live.json！")
