import gspread
from google.oauth2.service_account import Credentials


def sheetInfo(sheetName):
    # スプレッドシートIDを変数に格納する。
    SPREADSHEET_KEY = "1298CrtqplbK9GtShY0EjHRaphyTf461UXGIxCkbxHFI"

    gc = authorize_google_sheets_api()
    # スプレッドシート（ブック）を開く
    workbook = gc.open_by_key(SPREADSHEET_KEY)

    print("workbook", workbook)
    worksheet = workbook.worksheet(sheetName)

    return worksheet


"""
『アタックリストシート』『スクレイピング結果反映シート』にある企業には無いもののみ配列に入れなおす関数
@param {Object} sheet - 『アタックリストシート』情報
@param {Array<Object>} - 企業名 & 求人URL情報
@param {Object} sheet_scraping - 『スクレイピング結果反映シート』情報
@returns {Array<Object>} clearing_items - [{company: "", company: "", }]
"""


def ref_endClientList(sheet, items, sheet_scraping):
    # 『アタックリストシート』の企業名列の値を取得
    sheet_column_b = sheet.col_values(get_column_number(sheet, "企業名", 2))
    # 『スクレイピング結果反映シート』の企業名列の値を取得
    sheet_scraping_column_b = sheet_scraping.col_values(
        get_column_number(sheet_scraping, "企業名")
    )

    # 空の値を除外してsheet_company_values配列に格納します
    sheet_company_values = [value for value in sheet_column_b if value]
    sheet_scraping_company_values = [
        value for value in sheet_scraping_column_b if value
    ]

    clearing_items = []
    for item in items:
        # 『アタックリストシート』と『スクレイピング結果反映シート』のB列にitemの値が存在しなければclearing_items配列に格納する
        company = item["company"]
        if (
            company not in sheet_company_values
            and company not in sheet_scraping_company_values
        ):
            clearing_items.append(item)

    return clearing_items


# Google Sheets APIの認証と権限の取得
def authorize_google_sheets_api():
    # お決まりの文句
    # 2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    # ダウンロードしたjsonファイル名をクレデンシャル変数に設定。
    credentials = Credentials.from_service_account_file(
        "./scraping-townwork.json", scopes=scope
    )
    # OAuth2の資格情報を使用してGoogle APIにログイン。
    gc = gspread.authorize(credentials)

    return gc


# シートのタイトルから列番号を取得
def get_column_number(sheet, title, rowNum=1):
    header_row = sheet.row_values(rowNum)
    for i, value in enumerate(header_row):
        if value == title:
            return i + 1

    print(f"Title '{title}' not found.")
    return None


"""
シートの最終行を取得する関数
@param {Object} sheet - シート情報
@returns {Number} last_row - 最終行
"""


def getLastRow(sheet):
    # シートの最終行を取得(値の有無関係なし)
    last_row = sheet.row_count

    # 最終行から上方向にセルの値を検索(最初に値が見つかった行を取得する)
    while last_row > 0:
        # last_row行目のB列目のセルの値を取得
        cell_value = sheet.cell(last_row, 2).value
        if cell_value:
            break
        last_row -= 1

    return last_row


"""
『スクレイピング結果反映シート』の必要項目に値を設置する関数
@param {Array<Array<String>>} settingSrc_items - 設置する値
[['https://www.touzai.jp/', '東西株式会社 千葉ニュータウンオフィス[403]M-gi'], ...]
@param {Object} sheet_scraping - 『スクレイピング結果反映シート』情報
"""


def setting_Sheet(sheet_scraping, settingSrc_items, site_name=""):
    # label_columnNum = get_column_number(sheet_scraping, "ラベル")
    # company_columnNum = get_column_number(sheet_scraping, "企業名")
    # HRURL_columnNum = get_column_number(sheet_scraping, "HP URL")

    last_row = getLastRow(sheet_scraping)
    print("設置する行", last_row + 1)

    # settingSrc_itemsの要素分繰り返し処理
    # enumerate(settingSrc_items) - settingSrc_itemsの各要素とインデックスの組み合わせを返します。
    for r, item in enumerate(settingSrc_items):
        row_values = [site_name, item[0], item[1]]
        # insert_row(追加する値, 追加する行)
        sheet_scraping.insert_row(row_values, index=last_row + 1 + r)

    # 追加した行の数分を一度に出力
    # 追加した行の数に基づいてセルの範囲を指定し、その範囲の値を取得
    num_rows_added = len(settingSrc_items)
    # セルの範囲を指定 f"A{スタート}:C{終わり}"
    cell_range = f"A{last_row}:C{last_row + num_rows_added - 1}"
    # 指定の範囲のセルの値を取得
    # get() - 2次元のリストとして値を返す
    sheet_scraping.get(cell_range)
    # for row in cell_values:
    #     print(row)
