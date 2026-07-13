import requests
import time
import random
import re
import json
import os

SONGS_FILE = "songs.json"
ARTISTS_FILE = "artists.json"
CRAWLED_RECORD = "crawled.json"

BASE_HEADERS = {
    "Referer": "https://music.163.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

COOKIE = "YOUR_COOKIE_HERE"

def load_crawled_record():
    if os.path.exists(CRAWLED_RECORD):
        with open(CRAWLED_RECORD, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("artist_ids", [])), set(data.get("song_ids", []))
    return set(), set()

def save_crawled_record(artist_ids, song_ids):
    data = {"artist_ids": list(artist_ids), "song_ids": list(song_ids)}
    with open(CRAWLED_RECORD, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_lyric(raw_lyric):
    lyric_text = re.sub(r'\[\d{2}:\d{2}\.\d{2,3}]', '', raw_lyric)
    lines = [line.strip() for line in lyric_text.split('\n') if line.strip()]
    return '\n'.join(lines)

def safe_get(url, params=None, max_retry=3):
    for retry in range(max_retry):
        try:
            headers = BASE_HEADERS.copy()
            headers["User-Agent"] = random.choice(USER_AGENTS)
            headers["Cookie"] = COOKIE
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            time.sleep(random.uniform(1,2))
            return response.json()
        except Exception as e:
            print(f"请求失败，第{retry + 1}次重试，错误：{e}")
            time.sleep(2)
    print(f"请求最终失败：{url}")
    return None

def get_artist_list(cat_id):
    url = f"https://music.163.com/discover/artist/cat?id={cat_id}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://music.163.com/",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"  获取歌手列表失败: {e}")
        return []
    pattern = r'/artist\?id=(\d+)"[^>]*>([^<]+)</a>'
    artists = re.findall(pattern, response.text)
    seen = set()
    result = []
    for aid, name in artists:
        if aid not in seen:
            seen.add(aid)
            result.append({"id": int(aid), "name": name})
    return result

def get_artist_songs_and_info(artist_id):
    url = f"https://music.163.com/api/artist/{artist_id}"
    res = safe_get(url)
    if res and res.get("code") == 200:
        artist_info = {
            "artist_id": artist_id,
            "artist_name": res["artist"]["name"],
            "artist_pic": res["artist"]["picUrl"],
            "artist_url": f"https://music.163.com/artist?id={artist_id}",
            "brief_desc": res["artist"].get("briefDesc", "")
        }
        hot_songs = res.get("hotSongs", [])
        return artist_info, hot_songs
    return None, []

def get_song_lyric(song_id):
    url = "https://music.163.com/api/song/lyric"
    params = {"id": song_id, "lv": -1}
    res = safe_get(url, params)
    if res and res.get("code") == 200 and "lrc" in res:
        raw_lyric = res["lrc"].get("lyric", "") or ""
        return clean_lyric(raw_lyric)
    return ""

def get_artist_brief_desc(artist_id):
    url = "https://music.163.com/api/artist/introduction"
    params = {"id": artist_id}
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    headers["Cookie"] = COOKIE

    for retry in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 200:
                return data.get("briefDesc", "")
        except Exception as e:
            print(f"获取简介失败，第{retry + 1}次重试：{e}")
            time.sleep(1)
    return ""

def main():
    crawled_artist_ids, crawled_song_ids = load_crawled_record()
    print(f"已爬歌手：{len(crawled_artist_ids)} 位，已爬歌曲：{len(crawled_song_ids)} 首")
    if len(crawled_song_ids) >= 2000:
        print("\n之前已达到2000首歌曲目标，无需爬取")
        return 0
    all_artists = []
    all_songs = []
    if os.path.exists(ARTISTS_FILE):
        with open(ARTISTS_FILE, "r", encoding="utf-8") as f:
            all_artists = json.load(f)
    if os.path.exists(SONGS_FILE):
        with open(SONGS_FILE, "r", encoding="utf-8") as f:
            all_songs = json.load(f)
    cat_list = [1001, 1002]
    cat_name_map = {1001: "华语男歌手", 1002: "华语女歌手"}
    for current_cat in cat_list:
        cat_name=cat_name_map[current_cat]
        print(f"\n正在爬取 {cat_name} 歌手列表...")
        artists = get_artist_list(current_cat)
        if not artists:
            print(f" {cat_name} 歌手列表为空，跳过")
            continue
        print(f"共获取到 {len(artists)} 位 {cat_name}")
        for idx,artist in enumerate(artists,1):
            artist_id = str(artist["id"])
            if artist_id in crawled_artist_ids:
                print(f" [{idx}/{len(artists)}] 歌手 {artist['name']} 已爬过，跳过")
                continue
            print(f" [{idx}/{len(artists)}] 正在处理歌手：{artist['name']} (ID:{artist_id})")
            artist_info, hot_songs = get_artist_songs_and_info(artist_id)
            if not artist_info:
                print(f"歌手 {artist['name']} 信息获取失败，跳过")
                continue
            brief_desc = get_artist_brief_desc(artist_id)
            if brief_desc:
                artist_info["brief_desc"] = brief_desc
            all_artists.append(artist_info)
            song_count = 0
            for song in hot_songs:
                if song_count >= 20:
                    break
                song_id = str(song["id"])
                if song_id in crawled_song_ids:
                    continue
                print(f"  正在爬取歌曲：{song['name']} (ID:{song_id})")
                lyric = get_song_lyric(song_id)
                song_data = {
                    "song_id": song_id,
                    "song_name": song["name"],
                    "artist_name": artist_info["artist_name"],
                    "artist_id": artist_id,
                    "album_pic": song.get("album", {}).get("picUrl", ""),
                    "song_url": f"https://music.163.com/song?id={song_id}",
                    "lyric": lyric
                }
                all_songs.append(song_data)
                crawled_song_ids.add(song_id)
                song_count += 1
            crawled_artist_ids.add(artist_id)
            with open(ARTISTS_FILE, "w", encoding="utf-8") as f:
                json.dump(all_artists, f, ensure_ascii=False, indent=2)
            with open(SONGS_FILE, "w", encoding="utf-8") as f:
                json.dump(all_songs, f, ensure_ascii=False, indent=2)
            save_crawled_record(crawled_artist_ids, crawled_song_ids)
            print(f"  已保存进度，当前累计歌手：{len(crawled_artist_ids)}，累计歌曲：{len(crawled_song_ids)}")
            if len(crawled_song_ids) >= 2000:
                print("\n已达到2000首歌曲目标，停止爬取")
                print(f"\n爬取完成！共爬取歌手 {len(all_artists)} 位，歌曲 {len(all_songs)} 首")
                print(f"数据已保存到 {SONGS_FILE} 和 {ARTISTS_FILE}")
                return 0
    print(f"\n全部爬取完成！共爬取歌手 {len(all_artists)} 位，歌曲 {len(all_songs)} 首")
    print(f"数据已保存到 {SONGS_FILE} 和 {ARTISTS_FILE}")
    return 0

main()