"""CinemaBoard バックエンド — FastAPI アプリケーション"""

import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import Cinema, Schedule, SessionLocal, init_db
from scheduler import (
    CSV_OUTPUT_DIR,
    purge_past_schedules,
    refresh_schedule,
    sync_theaters,
)

# ---------------------------------------------------------------------------
# .env 読み込み
# ---------------------------------------------------------------------------
load_dotenv(Path(__file__).resolve().parent / ".env")

# ---------------------------------------------------------------------------
# ロギング
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 設定値 (.env から読み込み)
# ---------------------------------------------------------------------------
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "5"))
CSV_DUMP_ENABLED = os.getenv("CSV_DUMP_ENABLED", "false").lower() in (
    "true",
    "1",
    "yes",
)

# ---------------------------------------------------------------------------
# APScheduler
# ---------------------------------------------------------------------------
bg_scheduler = BackgroundScheduler()
_fetch_lock = threading.Lock()


def _do_fetch_all():
    """全映画館の1週間分スケジュールを取得する (排他制御付き)"""
    if not _fetch_lock.acquire(blocking=False):
        logger.info("スケジュール取得中のためスキップ")
        return
    try:
        # 過去のスケジュールを先に削除
        purge_past_schedules()

        session = SessionLocal()
        try:
            cinemas = session.query(Cinema).all()
        finally:
            session.close()

        base = datetime.now()
        days = [(base + timedelta(days=i)).strftime("%Y%m%d") for i in range(7)]

        # 1周期1ファイル
        csv_path = ""
        if CSV_DUMP_ENABLED:
            os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)
            csv_path = os.path.join(
                CSV_OUTPUT_DIR,
                f'schedule_{base.strftime("%Y%m%d_%H%M")}.csv',
            )

        for cinema in cinemas:
            for day in days:
                try:
                    refresh_schedule(
                        cinema.code,
                        day,
                        csv_dump=CSV_DUMP_ENABLED,
                        csv_path=csv_path,
                    )
                except Exception:
                    logger.exception("取得失敗: %s (day=%s)", cinema.name, day)
    finally:
        _fetch_lock.release()


def _scheduled_fetch():
    """定期ジョブ: 全映画館スケジュール取得"""
    _do_fetch_all()


def _scheduled_sync_theaters():
    """劇場一覧を同期するジョブ"""
    try:
        sync_theaters()
    except Exception:
        logger.exception("劇場一覧の同期に失敗")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    init_db()
    # 起動時に劇場一覧を同期
    try:
        sync_theaters()
    except Exception:
        logger.exception("初回劇場同期に失敗")
    bg_scheduler.add_job(
        _scheduled_sync_theaters,
        "interval",
        hours=24,
        id="sync_theaters",
        replace_existing=True,
    )
    bg_scheduler.add_job(
        _scheduled_fetch,
        "interval",
        minutes=FETCH_INTERVAL_MINUTES,
        id="fetch_schedule",
        replace_existing=True,
    )
    bg_scheduler.start()
    logger.info("スケジューラ起動 (間隔: %d 分)", FETCH_INTERVAL_MINUTES)
    # 起動時にも全スケジュールを取得 (バックグラウンドで実行)
    threading.Thread(target=_do_fetch_all, daemon=True).start()
    yield
    # 終了時
    bg_scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="CinemaBoard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------
def _schedule_to_dict(r: Schedule) -> dict:
    return {
        "cinemaCode": r.cinema_code,
        "movieName": r.movie_name,
        "movieNameEn": r.movie_name_en,
        "movieCode": r.movie_code,
        "duration": r.duration,
        "screenName": r.screen_name,
        "startTime": r.start_time,
        "endTime": r.end_time,
        "seatStatus": r.seat_status,
        "showDate": r.show_date,
    }


@app.get("/api/cinemas")
def list_cinemas():
    """映画館一覧を返す"""
    session = SessionLocal()
    try:
        cinemas = session.query(Cinema).all()
        return [
            {
                "code": c.code,
                "name": c.name,
                "region": c.region,
                "prefecture": c.prefecture,
            }
            for c in cinemas
        ]
    finally:
        session.close()


@app.get("/api/schedules")
def get_all_schedules(
    show_day: str = Query(..., pattern=r"^\d{8}$", description="YYYYMMDD"),
):
    """全映画館のスケジュールを返す"""
    session = SessionLocal()
    try:
        rows = (
            session.query(Schedule)
            .filter_by(show_date=show_day)
            .order_by(Schedule.cinema_code, Schedule.start_time)
            .all()
        )
        return [_schedule_to_dict(r) for r in rows]
    finally:
        session.close()


@app.get("/api/schedules/{cinema_code}")
def get_schedule(
    cinema_code: str,
    show_day: str = Query(..., pattern=r"^\d{8}$", description="YYYYMMDD"),
):
    """指定映画館・日付のスケジュールを返す"""
    session = SessionLocal()
    try:
        rows = (
            session.query(Schedule)
            .filter_by(cinema_code=cinema_code, show_date=show_day)
            .order_by(Schedule.start_time)
            .all()
        )
        return [_schedule_to_dict(r) for r in rows]
    finally:
        session.close()
