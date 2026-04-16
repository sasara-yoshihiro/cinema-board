"""スケジュール定期取得 & DB格納サービス"""

import logging
import os
from datetime import datetime

from fetcher import fetch_schedule, fetch_theaters, save_to_csv
from models import Cinema, Schedule, SessionLocal

logger = logging.getLogger(__name__)

# CSV 出力先
CSV_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def purge_past_schedules() -> int:
    """
    show_date が今日より前のスケジュールを DB から削除する。

    Returns:
        削除した件数
    """
    today = datetime.now().strftime("%Y%m%d")
    session = SessionLocal()
    try:
        count = session.query(Schedule).filter(Schedule.show_date < today).delete()
        session.commit()
        if count:
            logger.info("過去スケジュール削除: %d件", count)
        return count
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def sync_theaters() -> int:
    """
    劇場一覧をTOHOシネマズ公式サイトから取得し、DBを更新する。

    Returns:
        取得した劇場数
    """
    theaters = fetch_theaters()
    if not theaters:
        logger.info("劇場データなし")
        return 0

    session = SessionLocal()
    try:
        existing = {c.code: c for c in session.query(Cinema).all()}
        for t in theaters:
            code = t["code"]
            name = t["name"]
            region = t.get("region", "")
            prefecture = t.get("prefecture", "")
            api_url = f"https://api2.tohotheater.jp/api/schedule/v1/schedule/{code}/TNPI3050J02"
            if code in existing:
                if existing[code].name != name:
                    existing[code].name = name
                if existing[code].region != region:
                    existing[code].region = region
                if existing[code].prefecture != prefecture:
                    existing[code].prefecture = prefecture
                if existing[code].api_url != api_url:
                    existing[code].api_url = api_url
            else:
                session.add(
                    Cinema(
                        code=code,
                        name=name,
                        region=region,
                        prefecture=prefecture,
                        api_url=api_url,
                    )
                )
        session.commit()
        logger.info("劇場一覧同期完了: %d件", len(theaters))
        return len(theaters)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def refresh_schedule(
    cinema_code: str,
    show_day: str,
    *,
    csv_dump: bool = False,
    csv_path: str = "",
) -> int:
    """
    指定映画館・日付のスケジュールを取得し、DBへ格納する。

    Returns:
        取得した上映件数
    """
    schedule_list = fetch_schedule(cinema_code, show_day)

    if not schedule_list:
        logger.info("スケジュールデータなし (cinema=%s, day=%s)", cinema_code, show_day)
        return 0

    # デバッグ用CSV出力
    if csv_dump and csv_path:
        try:
            save_to_csv(schedule_list, csv_path=csv_path, cinema_code=cinema_code)
            logger.info(
                "CSV追記: %s (cinema=%s, day=%s)", csv_path, cinema_code, show_day
            )
        except Exception:
            logger.exception("CSV保存に失敗")

    # DB 更新 (同一映画館・日付のデータを差し替え)
    session = SessionLocal()
    try:
        session.query(Schedule).filter_by(
            cinema_code=cinema_code,
            show_date=show_day,
        ).delete()

        now = datetime.utcnow()
        for item in schedule_list:
            session.add(
                Schedule(
                    cinema_code=cinema_code,
                    show_date=show_day,
                    movie_name=item["映画名"],
                    movie_name_en=item.get("映画名(英語)", ""),
                    movie_code=item.get("映画コード", ""),
                    duration=item.get("上映時間(分)", ""),
                    screen_name=item.get("スクリーン", ""),
                    start_time=item.get("開始時間", ""),
                    end_time=item.get("終了時間", ""),
                    seat_status=item.get("座席状況", ""),
                    fetched_at=now,
                )
            )
        session.commit()
        logger.info(
            "DB更新完了: %d件 (cinema=%s, day=%s)",
            len(schedule_list),
            cinema_code,
            show_day,
        )
        return len(schedule_list)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
