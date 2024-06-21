# Information for You (I44U) - 대학생 맞춤형 활동 추천 시스템

## 프로젝트 개요

이 프로젝트는 대학생들을 위해 데이터베이스 기반 맞춤형 활동 추천 시스템을 개발한 것입니다. 학생들이 회원가입 시 제공한 간단한 정보 및 관심사를 바탕으로 학생들이 활동을 찾는 데 소모되는 시간을 줄여주고, 활동의 기회를 놓치는 것을 방지하고자 합니다.

## 주요 기능

- **활동 추천**: 사용자 관심사에 기반한 맞춤형 활동 추천
- **활동 상세 정보 제공**: 각 활동에 대한 상세 정보 확인 가능
- **팀 모집**: 활동별 팀 모집 기능
- **프로필 관리**: 사용자 프로필 및 관심사 관리
- **즐겨찾기**: 관심 있는 활동 즐겨찾기 기능
- **자동 포트폴리오**: 참여한 활동을 자동으로 포트폴리오에 업로드 가능

## 파일 구조

```plaintext
project/
├── crawlling/
│   ├── __pycache__/
│   └── crawlling_code/
│       ├── result_activity.csv
│       ├── result_campus.csv
│       ├── result_career.csv
│       └── result_contest.csv
├── instance/
│   └── app_database.db
├── templates/
│   ├── activities.html
│   ├── activity_detail.html
│   ├── add_team_recruitment.html
│   ├── campus.html
│   ├── campus_detail.html
│   ├── career_detail.html
│   ├── careers.html
│   ├── contest.html
│   ├── contest_detail.html
│   ├── dashboard.html
│   ├── edit_profile.html
│   ├── favorites.html
│   ├── home.html
│   ├── interests.html
│   ├── portfolio.html
│   ├── profile.html
│   ├── search_results.html
│   ├── team_recruitment.html
│   ├── team_recruitment_detail.html
│   └── app.py
```

## 설치 및 실행 방법
### 사전 준비
1. Python 설치 (버전 3.6 이상 권장)
2. Git 설치

### 가상 환경 설정
1. 프로젝트를 클론합니다.
```plaintext
git clone https://github.com/yourusername/yourproject.git
cd yourproject
```
2. 가상 환경을 생성하고 활성화합니다.
```plaintext
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```
## 데이터베이스 설정

1. instance 폴더 내의 app_database.db 파일을 확인합니다.

2. 필요한 경우 데이터베이스를 초기화합니다.
```plaintext
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
```
## 어플리케이션 실행

1. 어플리케이션을 실행합니다.
```plaintext
python app.py
```
2. 웹 브라우저를 열고 http://localhost:5000 에 접속합니다.

# 스크린샷 및 데모

![image](https://github.com/GitSummin/I44U/assets/121507209/ecc900bf-f8de-432d-94d4-e866fa666731)
![image](https://github.com/GitSummin/I44U/assets/121507209/569cca3a-8b0a-405e-bb80-4179cfacc9d5)


