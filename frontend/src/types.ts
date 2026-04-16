/** スケジュール1件の型定義 */
export interface ScheduleItem {
  cinemaCode: string
  movieName: string
  movieNameEn: string
  movieCode: string
  duration: string
  screenName: string
  startTime: string
  endTime: string
  seatStatus: string
  showDate: string
}

/** 映画館の型定義 */
export interface Cinema {
  code: string
  name: string
  region: string
  prefecture: string
}
