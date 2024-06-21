import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import pandas as pd

def crawling(cat_mcls):
    for cat in cat_mcls:
        cat_id = cat[0] 
        cat_name = cat[1]
        max_pages = 25

        with open(f'{cat_name}.csv', 'w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(['reg_date', 'title', 'company', 'URL', 'deadline', 'location', 'experience', 'jobtype', 'category'])

            for page in range(1, max_pages + 1):
                response = requests.get(
                    f'https://www.saramin.co.kr/zf_user/search?cat_mcls={cat_id}&recruitPage={page}&recruitSort=reg_dt',
                    headers={'User-Agent': 'Mozilla/5.0'})
                html = BeautifulSoup(response.text, 'html.parser')
                jobs = html.select('div.item_recruit')

                for job in jobs:
                    try:
                        today = job.select('span.job_day')[0].text.strip()
                    except:
                        #print(f'job_day is NULL, page_num: {page}')
                        today = 'NULL'

                    try:
                        title = job.select_one('a')['title'].strip().replace(',', '')
                    except:
                        print(f'title is NULL, page_num: {page}')
                        title = 'NULL'

                    try:
                        company = job.select_one('div.area_corp > strong > a').text.strip()
                    except:
                        #print(f'company is NULL, page_num: {page}')
                        company = 'NULL'

                    try:
                        url = 'https://www.saramin.co.kr' + job.select_one('a')['href']
                    except:
                        #print(f'url is NULL, page_num: {page}')
                        url = 'NULL'

                    try:
                        deadline = job.select_one('span.date').text.strip()
                    except:
                        #print('deadline is NULL, page_num: {page}')
                        deadline = 'NULL'

                    try:
                        location = job.select('div.job_condition > span')[0].text.strip()
                    except:
                        #print(f'location is NULL, page_num: {page}')
                        location = 'NULL'

                    try:
                        experience = job.select('div.job_condition > span')[1].text.strip()
                    except:
                        #print(f'experience is NULL, page_num: {page}')
                        experience = 'NULL'

                    try:
                        requirement = job.select('div.job_condition > span')[2].text.strip()
                    except:
                        #print(f'requirement is NULL, page_num: {page}')
                        requirement = 'NULL'

                    try:
                        jobtype = job.select('div.job_condition > span')[3].text.strip()
                    except:
                        #print(f'jobtype is NULL, page_num: {page}')
                        jobtype = 'NULL'

                    writer.writerow([today, title, company, url, deadline, location, experience, jobtype, cat_name])
                if page % 10 == 0:
                        print(f'{cat_name}.csv {page}/{max_pages} ')
        print(f'{cat_name}.csv completed')

def concat(cat_mcls):
    names = [item[1] for item in cat_mcls]
    li = []
    date_pattern = r'\d{2}/\d{2}/\d{2}'
    for name in names:
        filename = os.path.join(os.getcwd(), f'{name}.csv')
        
        # 파일이 존재하는지 확인
        if os.path.exists(filename):
            df = pd.read_csv(filename, index_col=None, header=0)
            
            # reg_date 열의 값 변환
            df['reg_date'] = df['reg_date'].apply(lambda x: re.findall(date_pattern, x)[0] if re.findall(date_pattern, x) else x)
            
            li.append(df)

    # 데이터프레임을 하나로 결합
    frame = pd.concat(li, axis=0, ignore_index=True)

    # 결합된 데이터프레임을 CSV 파일로 저장
    combined_csv_path = os.path.join(os.getcwd(), "combined_csv.csv")
    frame.to_csv(combined_csv_path, encoding="utf-8-sig", index=False)

    print(f"CSV 파일이 성공적으로 저장되었습니다: {combined_csv_path}")

if __name__ == '__main__':
    # 카테고리 목록
    cat_mcls = [[2, "IT개발·데이터"], [3, "회계·세무·재무"], [4, "총무·법무·사무"], [5, "인사·노무·HRD"],
                [6, "의료"], [7, "운전·운송·배송"], [8, "영업·판매·무역"], [9, "연구·R&D"],
                [10, "서비스"], [11, "생산"], [12, "상품기획·MD"], [13, "미디어·문화·스포츠"],
                [14, "마케팅·홍보·조사"], [15, "디자인"], [16, "기획·전략"], [17, "금융·보험"], [18, "구매·자재·물류"],
                [19, "교육"], [20, "공공·복지"], [21, "고객상담"], [22, "건설·건축"]]
    crawling(cat_mcls)
    concat(cat_mcls)