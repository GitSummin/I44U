from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.common.by import By
import time
import requests
from bs4 import BeautifulSoup
import csv
from selenium.common.exceptions import NoSuchElementException


# 서비스 객체를 생성하여 크롬 드라이버 경로를 설정
service = Service()
driver = webdriver.Chrome(service=service)

# 로그인 페이지 URL
login_url = 'https://plaza.inha.ac.kr/plaza/2110/subview.do'
url="https://plaza.inha.ac.kr/plaza/2100/subview.do?enc=Zm5jdDF8QEB8JTJGcGxhemFCYnMlMkZwbGF6YSUyRjEwMDA3JTJGYXJ0Y2xMaXN0LmRvJTNG"


# 로그인할 사용자 정보
username = '학번'
password = '비밀번호'

# 로그인 페이지 접속
driver.get(login_url)

# 로그인 정보 입력 및 제출
driver.find_element(By.ID, 'userId').send_keys(username)
driver.find_element(By.ID, 'userPwd').send_keys(password) 
driver.find_element(By.CLASS_NAME, 'btn_login').click()  # 로그인 버튼

# 로그인 후 게시글 페이지 접속을 위한 대기 시간
time.sleep(3) 
driver.get(url)

current_page=1
def collect_data_from_page(driver):
    # 현재 페이지의 데이터를 수집하는 함수
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    article_info = []

    # div>table>tbody>
    # tbody 태그 내부의 게시글 정보를 찾기
    tbody = soup.find('tbody')
    table = soup.find('table', class_='artclTable artclHorNum1')
    

    # '_fnctWrap _articleTable' 클래스를 가진 'div' 태그 내부의 'tbody' 태그 찾기
    article_div = soup.find('div', class_=["_fnctWrap _articleTable"])
    if article_div:
        tbody = article_div.find('tbody')
        if tbody:
            # 'tr' 태그들 찾기
            for row in tbody.find_all('tr', {'class': ['thumbLi _artclEven', 'thumbLi _artclOdd']}):
                title_cell = row.find('td', class_='_artclTdTitle')
                date_cell = row.find('td', class_='_artclTdRdate')
                link_tag = title_cell.find('a', href=True) if title_cell else None

                # 제목, 날짜, 링크 정보 추출
                if title_cell and date_cell and link_tag:
                    title = title_cell.get_text(strip=True)
                    date = date_cell.get_text(strip=True)
                    link = link_tag['href']
                    full_link = requests.compat.urljoin(url, link)
                    article_info.append({'title': title, 'date': date, 'link': full_link})
                else:
                    print("Information not found for a row")
        else:
            print("tbody not found inside the article div")
        
    else:
        print("Article container div not found")

    return article_info

all_article_info = []

while current_page<=11:
    # 현재 페이지에서 데이터 수집
    all_article_info.extend(collect_data_from_page(driver))
    
    try:
        # 다음 페이지로 이동
        next_page_number = current_page + 1
        driver.execute_script(f"page_link({next_page_number});") #javascript:page_link(n)

        time.sleep(2)
        current_page = next_page_number
    
    except NoSuchElementException:
        # '다음' 버튼이 없으면 마지막 페이지이므로 반복 중단
        break

# 크롤링이 끝난 후 드라이버 종료
driver.quit()
csv_file_path = 'C:\\Users\\kaebi\\OneDrive\\바탕 화면\\인하대\\2학년\\파이썬기반 응용 프로그래밍\\0428\\plazadata.csv'

# 파일로 저장
with open(csv_file_path, mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.DictWriter(file, fieldnames=['title', 'date', 'link'])
    writer.writeheader()
    writer.writerows(all_article_info)
    # for item in all_article_info:
    #     writer.writerow(item)

# 저장된 CSV 파일의 경로 반환 
print(csv_file_path)