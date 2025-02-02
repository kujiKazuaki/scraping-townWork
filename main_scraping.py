import requests
from bs4 import BeautifulSoup
import urllib
import Plugins.GoogleSpredSheet as PG
import re


def scraping_townWork(page_number):
    sheet = PG.sheetInfo("アタックリストシート")
    sheet_scraping = PG.sheetInfo("スクレイピング結果反映シート")

    # @returns [{'company': 'リーサコンサルティング株式会社', 'beforeURL': "https://townwork.net/detail/clc_2017755001/joid_U0611BU2/"}...]
    items = getItems_TownWork(page_number)

    if len(items) == 0:
        print("itemsに値はありません")
        return

    # 『アタックリストシート』『スクレイピング結果反映シート』にある企業には無いもののみ配列に入れなおす
    clearing_items = PG.ref_endClientList(sheet, items, sheet_scraping)

    if len(clearing_items) == 0:
        print("clearing_itemsに値はありません")
        return

    # print("clearing_items", clearing_items)

    # beforeURLを企業URLに変換させる処理
    settingSrc_items = []
    for i in range(len(clearing_items)):
        item = clearing_items[i]
        company = item["company"]

        # companyが特定の値を含む場合(企業名)はスキップする(明らかにエンドでもSESでもないと判断した企業)
        refused_company_List = refused_company_Func()
        passage = True
        for refused_company in refused_company_List:
            pattern = re.compile(refused_company)  # 正規表現にする

            if re.search(pattern, str(company)):
                passage = False
                break

        if not passage:
            continue

        before_url = item["beforeURL"]
        after_url = refine_url(before_url)

        # 『undefind』の場合(正規表現に引っかかった場合)の処理
        if after_url in ["undefind", None, ""]:
            continue

        data = []
        data.append(company)
        data.append(after_url)  # リストに要素を追加するには append() メソッドを使用します
        settingSrc_items.append(data)

    # settingSrc_items 配列の形
    # [['https://pfs.persol-group.co.jp/', 'パーソルフィールドスタッフ株式会社'],,,]

    if len(settingSrc_items) == 0:
        print("settingSrc_itemsに値はありません")
        return

    print("settingSrc_items", settingSrc_items)
    PG.setting_Sheet(sheet_scraping, settingSrc_items, "タウンワーク")


"""
URL先から各企業の企業名とbeforeURLを取得する関数
@param {Number} page_number - ページ数
@returns {Array<Object>} items - 企業URLと企業名
ex) [ { "company": company, "beforeURL": url,} ...]
"""


def getItems_TownWork(page_number=1):
    base_url = "https://townwork.net/joSrchRsltList/?jc=005&ac=041&emc=04&ds=03&page="

    url = base_url + str(page_number)
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    # HTMLコンテンツの取得
    soup = BeautifulSoup(response.content, "html.parser")

    items = []
    judge_items = []
    for elements in soup.find_all(class_="job-lst-main-box-inner"):
        # url - 各企業の求人サイトへのURL
        url = elements.get("href")
        # urllibライブラリ(相対URLを絶対URLに変換する)の使用
        url = urllib.parse.urljoin(base_url, url)
        company = elements.find("h3").text.strip()

        # 『/』があれば以降の値を削除する
        if "/" in company:
            company = company.split("/")[0]

        # 『株式会社』の次の値が空白であれば『株式会社』までの値のみにする
        pattern = r"株式会社　"  # 「株式会社」の後に全角空白を含むパターン
        match = re.search(pattern, company)
        if match:
            company = company[: match.end() - 1]  # 最後の文字（全角空白）を除外

        if not company in judge_items:
            judge_items.append(company)
            data = {
                "company": company,
                "beforeURL": url,
            }
            items.append(data)

    return items


"""
before_urlを企業URLに変換する関数
@param {String} before_url - 求人サイトのURL
@returns {String} after_url - 企業URL or undefined(正規表現に引っかかった場合)
"""


def refine_url(before_url):
    after_url = before_url

    response = requests.get(before_url)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.content, "html.parser")

    # 特定のクラスに該当するHTMLコンテンツの取得(複数あるため、該当箇所があり、なおかつ『仕事内容』の項目が子要素にあるものに対し処理を行うようにする)
    html = soup.find_all("dl", class_="job-ditail-tbl-inner")
    if len(html) == 0:
        # html変数が無い場合の処理
        after_url = "(not supposed_URL)★" + str(before_url)
        return after_url

    for i in range(len(html)):
        element = html[i]

        if element.find("dt", text="仕事内容"):
            # <dt>仕事内容</dt>の子要素の<p>タグの値を取得
            text_content = (
                element.find("dt", text="仕事内容")
                .find_next_sibling("dd")
                .find("p")
                .get_text(strip=True)
            )

            pattern = r"(?:コンサル|客先常駐|業務委託|派遣|SES|クライアント|受託開発)"
            pattern_Page_tendency = r"(?:電話|未経験|お客様|企業様|サポート)"
            flags = re.I | re.S
            filters = re.compile(pattern, flags)
            filters_Page_tendency = re.compile(pattern_Page_tendency, flags)

            if filters.search(text_content) or filters_Page_tendency.search(
                text_content
            ):
                result = False
            else:
                result = True

            # 『仕事内容』欄の内容が正規表現に引っかからなかった場合
            if result == True:
                # 『ホームページリンク』欄のURLの取得
                html = soup.find(class_="jsc-thumb-link")
                if html:
                    after_url = html.get_text(strip=True)
                    return after_url
                else:
                    after_url = "(not HP URL)★" + str(before_url)
                    return after_url
            after_url = "undefind"
            return after_url
        elif i == (len(html) - 1):
            # 『仕事内容』欄の無い企業に対して行われる処理

            # 『ホームページリンク』欄のURLの取得
            html = soup.find(class_="jsc-thumb-link")
            if html:
                # HP URLがあるならその値を返す
                after_url = html.get_text(strip=True)
                return after_url
            else:
                # HP URLが無ければHP URLが無い旨とbefore_urlを返す
                after_url = "(not HP URL)★" + str(before_url)
                return after_url


"""
お断り企業をリスト化した関数
@returns {Array<String>} refused_company_List - お断り企業が含まれる配列
"""


def refused_company_Func():
    refused_company_List = [r"ハロー！パソコン教室"]

    return refused_company_List
