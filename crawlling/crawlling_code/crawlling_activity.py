import requests
from bs4 import BeautifulSoup
import csv
import time

# CSV 파일에 저장할 때 사용할 헤더
headers = ['대외활동명', '포스터', '주최', '주관', '접수기간', '분야', '응모대상', '혜택']

def get_contest_info(contest_url):
    # 공모전 페이지의 HTML을 가져옴
    response = requests.get(contest_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 각 정보를 추출
    try:
        poster = soup.find('div', class_='contest_poster').find('img')['src']
    except AttributeError:
        poster = 'Not found'

    try:
        host = soup.find('th', class_='title_host').find_next_sibling('td').text.strip()
    except AttributeError:
        host = 'Not found'

    try:
        organizer = soup.find('th', class_='title_organizer').find_next_sibling('td').text.strip()
    except AttributeError:
        organizer = 'Not found'

    try:    
        reception_period = soup.find('th', class_='title_date').find_next_sibling('td').text.strip()
    except AttributeError:
        reception_period = 'Not found'

    try:
        field = soup.find('th', class_='title_cate').find_next_sibling('td').text.strip()
    except AttributeError:
        field = 'Not found'

    try:
        target = soup.find('th', class_='title_target').find_next_sibling('td').text.strip()
    except AttributeError:
        target = 'Not found'
    
    try:
        award = soup.find('th', class_='title_award').find_next_sibling('td').text.strip()
    except AttributeError:
        award = 'Not found'
    
    try:
        contest_name = soup.find('h1').text.strip()
    except AttributeError:
        contest_name = 'Not found'
    
    return [contest_name, poster, host, organizer, reception_period, field, target, award]

def main():
    with open('activity_info.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for contest_id in range(490434, 513710):
            contest_url = f'https://www.all-con.co.kr/view/contest/{contest_id}'

            try:
                response = requests.get(contest_url)
                response.raise_for_status()

                contest_info = get_contest_info(contest_url)
                if contest_info:
                    writer.writerow(contest_info)
                
            except requests.exceptions.RequestException as e:
                print(f"Error accessing {contest_url}: {e}")
                time.sleep(1)

    print("Scraping complete. Data written to contest_info.csv")

if __name__ == '__main__':
    main()
