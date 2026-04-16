/**
 * 表示テキスト正規化ユーティリティ
 */

/** 全角英数・括弧を半角に変換 */
function toHalfWidth(s: string): string {
    return (
        s
            // 全角英数 → 半角
            .replace(/[Ａ-Ｚａ-ｚ０-９]/g, (ch) =>
                String.fromCharCode(ch.charCodeAt(0) - 0xfee0),
            )
            // 全角括弧・スペース
            .replace(/（/g, "(")
            .replace(/）/g, ")")
            .replace(/　/g, " ")
    );
}

/** 映画館名の表示用テキストを生成 ("TOHOシネマズ " を除去 + 半角化) */
export function displayCinemaName(name: string): string {
    return toHalfWidth(name.replace(/^TOHOシネマズ\s*/, ""));
}

/** 映画名の表示用テキストを生成 (半角化のみ) */
export function displayMovieName(name: string): string {
    return toHalfWidth(name);
}

// ---------------------------------------------------------------------------
// 地区・都道府県の表示順序定義
// ---------------------------------------------------------------------------
const REGION_ORDER: string[] = [
    "北海道地区",
    "東北地区",
    "関東地区",
    "中部地区",
    "関西地区",
    "中国地区",
    "四国地区",
    "九州地区",
];

const PREFECTURE_ORDER: string[] = [
    // 北海道
    "北海道",
    // 東北
    "宮城県",
    "福島県",
    "山形県",
    "岩手県",
    "秋田県",
    "青森県",
    // 関東
    "東京都",
    "神奈川県",
    "千葉県",
    "埼玉県",
    "栃木県",
    "群馬県",
    "山梨県",
    "茨城県",
    // 中部
    "静岡県",
    "愛知県",
    "岐阜県",
    "長野県",
    "新潟県",
    "石川県",
    "富山県",
    "福井県",
    // 関西
    "大阪府",
    "京都府",
    "兵庫県",
    "滋賀県",
    "奈良県",
    "三重県",
    "和歌山県",
    // 中国
    "岡山県",
    "広島県",
    "鳥取県",
    "島根県",
    "山口県",
    // 四国
    "香川県",
    "愛媛県",
    "徳島県",
    "高知県",
    // 九州
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
];

/** 地区の並び順インデックスを返す (未登録は末尾) */
export function regionSortIndex(region: string): number {
    const idx = REGION_ORDER.indexOf(region);
    return idx === -1 ? REGION_ORDER.length : idx;
}

/** 都道府県の並び順インデックスを返す (未登録は末尾) */
export function prefectureSortIndex(prefecture: string): number {
    const idx = PREFECTURE_ORDER.indexOf(prefecture);
    return idx === -1 ? PREFECTURE_ORDER.length : idx;
}
