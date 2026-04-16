"""
TOHOシネマズの上映スケジュールを取得するモジュール。

対象ページ: https://hlo.tohotheater.jp/net/schedule/{vg_cd}/TNPI2000J01.do
※ ページ上のスケジュールはJavaScriptで動的に読み込まれるため、
   内部APIから直接JSONデータを取得する。
"""

import logging
import os
import re
import time
from datetime import datetime

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# TOHOシネマズ スケジュールAPIベースURL
SCHEDULE_API_BASE = (
    "https://api2.tohotheater.jp/api/schedule/v1/schedule/{vg_cd}/TNPI3050J02"
)

# 劇場一覧ページ
THEATER_LIST_URL = "https://www.tohotheater.jp/theater/find.html"

# 座席状況コードの日本語マッピング
SEAT_STATUS_MAP = {
    "A": "余裕あり",
    "B": "残りわずか",
    "G": "販売終了",
    "X": "満席",
}


def fetch_theaters() -> list:
    """
    TOHOシネマズの劇場一覧を公式サイトから取得する。

    Returns:
        [{'code': '078', 'name': 'TOHOシネマズ 仙台', 'region': '東北地区', 'prefecture': '宮城県'}, ...]
    """
    response = requests.get(THEATER_LIST_URL, timeout=30)
    if response.status_code != 200:
        raise Exception(f"劇場一覧の取得に失敗しました (HTTP {response.status_code})")

    response.encoding = "shift_jis"
    html = response.text

    # HTML構造: theater-list-section(地区) > theater-list-area(都道府県) > theater links
    sections = re.split(r'<section class="theater-list-section">', html)
    seen: dict[str, dict] = {}

    for sec in sections[1:]:
        region_match = re.search(r"<h3[^>]*>([^<]+)", sec)
        region = region_match.group(1).strip() if region_match else ""

        # 地区セクションのみ使用 (IMAX劇場一覧等の重複セクションを除外)
        if not region.endswith("地区"):
            continue

        areas = re.split(r'<section class="theater-list-area">', sec)
        for area in areas[1:]:
            pref_match = re.search(r"<h4[^>]*>\s*([^<]+)", area)
            prefecture = pref_match.group(1).strip() if pref_match else ""

            theaters = re.findall(
                r'<a href="/net/schedule/(\d{3})/[^"]*"><span>([^<]+)',
                area,
            )
            for code, name in theaters:
                if code not in seen:
                    seen[code] = {
                        "code": code,
                        "name": name.strip(),
                        "region": region,
                        "prefecture": prefecture,
                    }

    return sorted(seen.values(), key=lambda t: t["code"])


def fetch_schedule(cinema_code: str, show_day: str) -> list:
    """
    TOHOシネマズの上映スケジュールをAPIから取得する。

    Args:
        cinema_code: 劇場コード (例: '078')
        show_day: 取得対象日 (YYYYMMDD形式)

    Returns:
        上映スケジュール情報の辞書リスト

    Raises:
        Exception: API呼び出しに失敗した場合
    """
    api_url = SCHEDULE_API_BASE.format(vg_cd=cinema_code)
    params = {
        "__type__": "html",
        "__useResultInfo__": "no",
        "vg_cd": cinema_code,
        "show_day": show_day,
        "term": "99",
        "isMember": "N",
        "enter_kbn": "",
        "_dc": str(int(time.time() * 1000)),
    }

    response = requests.get(api_url, params=params, timeout=30)
    logger.debug(f"status code: {response.status_code}")
    if response.status_code != 200:
        return []  # APIエラーの場合は空リストを返す

    data = response.json()
    logger.debug(f'status: {data.get("status")}')
    if data.get("status") != "0":
        return []  # APIエラーの場合は空リストを返す

    return _parse_schedule(data)


def _parse_schedule(data: dict) -> list:
    """APIレスポンスから上映スケジュール情報を抽出する。"""
    schedule_list = []

    for entry in data.get("data", []):
        date = entry.get("showDay", {}).get("date", "")

        for theater_group in entry.get("list", []):
            for movie in theater_group.get("list", []):
                movie_name = movie.get("name", "")
                movie_ename = movie.get("ename", "")
                movie_code = movie.get("mcode", "")
                duration = movie.get("hours", "")

                for screen in movie.get("list", []):
                    screen_name = screen.get("name", "")

                    for showing in screen.get("list", []):
                        start_time = showing.get("showingStart", "")
                        end_time = showing.get("showingEnd", "")

                        if not start_time:
                            continue

                        seat_info = showing.get("unsoldSeatInfo")
                        seat_status = ""
                        if seat_info:
                            code = seat_info.get("unsoldSeatStatus", "")
                            seat_status = SEAT_STATUS_MAP.get(code, code)

                        schedule_list.append(
                            {
                                "日付": date,
                                "映画名": movie_name,
                                "映画名(英語)": movie_ename,
                                "映画コード": movie_code,
                                "上映時間(分)": duration,
                                "スクリーン": screen_name,
                                "開始時間": start_time,
                                "終了時間": end_time,
                                "座席状況": seat_status,
                            }
                        )

    return schedule_list


def save_to_csv(
    schedule_list: list,
    csv_path: str,
    cinema_code: str = "",
) -> str:
    """
    スケジュールデータをCSVファイルに追記保存する。

    Args:
        schedule_list: スケジュール情報の辞書リスト
        csv_path: 出力先ファイルパス
        cinema_code: 映画館コード (カラムとして挿入)

    Returns:
        保存したファイルパス
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # cinema_code カラムを日付の次に挿入
    rows = []
    for item in schedule_list:
        row = {}
        for k, v in item.items():
            row[k] = v
            if k == "日付":
                row["映画館コード"] = cinema_code
        rows.append(row)

    df = pd.DataFrame(rows)

    file_exists = os.path.isfile(csv_path)
    df.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig",
        mode="a" if file_exists else "w",
        header=not file_exists,
    )

    return csv_path
