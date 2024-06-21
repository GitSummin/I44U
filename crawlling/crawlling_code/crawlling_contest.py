import requests
from bs4 import BeautifulSoup
import csv
import time

# CSV 파일에 저장할 때 사용할 헤더
headers = ['공모전명', '포스터', '주최', '주관', '접수기간', '분야', '응모대상', '시상내역']

def get_contest_info(contest_url):
    response = requests.get(contest_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    contest_info = {}
    
    try:
        contest_info['공모전명'] = soup.find('h1').text.strip()
    except AttributeError:
        pass
    
    poster_div = soup.find('div', class_='contest_poster')
    if poster_div:
        poster_img = poster_div.find('img')
        if poster_img:
            contest_info['포스터'] = poster_img['src']
    
    host_th = soup.find('th', class_='title_host')
    if host_th:
        host_td = host_th.find_next_sibling('td')
        if host_td:
            contest_info['주최'] = host_td.text.strip()

    organizer_th = soup.find('th', class_='title_organizer')
    if organizer_th:
        organizer_td = organizer_th.find_next_sibling('td')
        if organizer_td:
            contest_info['주관'] = organizer_td.text.strip()

    date_th = soup.find('th', class_='title_date')
    if date_th:
        date_td = date_th.find_next_sibling('td')
        if date_td:
            contest_info['접수기간'] = date_td.text.strip()

    cate_th = soup.find('th', class_='title_cate')
    if cate_th:
        cate_td = cate_th.find_next_sibling('td')
        if cate_td:
            contest_info['분야'] = cate_td.text.strip()

    target_th = soup.find('th', class_='title_target')
    if target_th:
        target_td = target_th.find_next_sibling('td')
        if target_td:
            contest_info['응모대상'] = target_td.text.strip()
    
    award_th = soup.find('th', class_='title_award')
    if award_th:
        award_td = award_th.find_next_sibling('td')
        if award_td:
            contest_info['시상내역'] = award_td.text.strip()
    
    return contest_info

def main():
    with open('new_contest_info.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for contest_id in range(509068, 513694):
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
