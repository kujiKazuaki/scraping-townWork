import main_scraping
import schedule
import time


def main_townWork():
    counter = 7  # ページ枚数

    # 計算用(doda_2以降も作る場合に備えて設置)
    dodaCount = 0
    pageNumber = counter * dodaCount + 1
    forCounter = pageNumber + counter - 1

    for i in range(pageNumber, forCounter + 1):
        print(f"TownWorkURLの{i}ページ目を実行しています")
        main_scraping.scraping_townWork(i)


schedule.every().wednesday.at("9:00").do(main_townWork)


while True:
    schedule.run_pending()  # 3. 指定時間が来てたら実行、まだなら何もしない
    time.sleep(1)  # 待ち
