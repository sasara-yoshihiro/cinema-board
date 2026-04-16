"""SQLAlchemy モデル定義"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class Cinema(Base):
    """映画館マスタ"""
    __tablename__ = 'cinemas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)   # 劇場コード (例: "078")
    name = Column(String, nullable=False)                 # 映画館名
    region = Column(String, default='')                   # 地区 (例: "関東地区")
    prefecture = Column(String, default='')               # 都道府県 (例: "東京都")
    api_url = Column(String, nullable=False)              # スケジュールAPI URL


class Schedule(Base):
    """上映スケジュール"""
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cinema_code = Column(String, nullable=False, index=True)
    show_date = Column(String, nullable=False, index=True)   # YYYYMMDD
    movie_name = Column(String, nullable=False)
    movie_name_en = Column(String, default='')
    movie_code = Column(String, default='')
    duration = Column(String, default='')
    screen_name = Column(String, default='')
    start_time = Column(String, default='')
    end_time = Column(String, default='')
    seat_status = Column(String, default='')
    fetched_at = Column(DateTime, default=datetime.utcnow)


# --- DB 初期化 ---------------------------------------------------------------
DATABASE_URL = 'sqlite:///cinemaboard.db'
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """テーブル作成"""
    Base.metadata.create_all(engine)
