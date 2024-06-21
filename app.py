import pandas as pd
import os
import requests
import math

# 조회수 처리를 위한 모듈 임포트
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, func, distinct, desc
from sqlalchemy.orm import sessionmaker
from flask import Flask, request, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, confirm_login
# from werkzeug.security import generate_password_hash
# from sqlalchemy import Table, Column, Integer, ForeignKey
# from sqlalchemy import or_
# from sqlalchemy.orm import relationship
# from bs4 import BeautifulSoup


#### 1. Flask로 App 생성 ####
app = Flask(__name__) # Flask Application 생성
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_database.db' # DB URI 설정 / .db 파일 지정
app.config['SECRET_KEY'] = 'A+주고10조' # 보안 키 설정
app.config['UPLOAD_FOLDER'] = "static/contest_img"
db = SQLAlchemy(app)
migrate = Migrate(app, db) # 마이크레이션 코드 추가

#### 2. 데이터베이스 생성 ####
login_manager = LoginManager() # 로그인 기능 생성
login_manager.init_app(app) # SQLAlchemy - Flask와 로그인 기능 연결

## (상세 페이지에 필요한 이미지 파일 경로) ##
CONTEST_FOLDER = "static/contest_img"
app.config['CONTEST_FOLDER'] = CONTEST_FOLDER
ACTIVITY_FOLDER = "static/activity_img"
app.config['ACTIVITY_FOLDER'] = ACTIVITY_FOLDER

## 2-1. 공모전 데이터 저장 ##
def save_contest_csv_to_db():
    contest_path = "crawlling/result_contest.csv"
    df = pd.read_csv(contest_path)

    # 컬럼명 변경
    df.rename(columns={'공모전명': 'name', '주최': 'host', '주관': 'organizer',
                       '접수기간': 'date', '분야': 'type', '응모대상': 'target',
                       '시상내역': 'award', '조회수' : 'views'}, inplace=True)
    
    # 데이터베이스에 데이터프레임 저장
    df.to_sql('contest', con=db.engine, if_exists='append', index=False)

## 2-2. 대외활동 데이터 저장 ##
def save_activities_csv_to_db():
    activity_path = "crawlling/result_activity.csv"
    df = pd.read_csv(activity_path)

    # 컬럼명 변경
    df.rename(columns={'대외활동명': 'name', '주최': 'host', '주관': 'organizer',
                       '접수기간': 'date', '분야': 'type', '응모대상': 'target',
                       '혜택': 'profit', '조회수' : 'views'}, inplace=True)
    
    # 데이터베이스에 데이터프레임 저장
    df.to_sql('activity', con=db.engine, if_exists='append', index=False)

## 2-3. 취업 / 인턴 데이터 저장 ##
def save_career_csv_to_db():
    career_path = "crawlling/result_career.csv"
    df = pd.read_csv(career_path, encoding='utf-8-sig')  # Adjust encoding if needed
    
    # Iterate through each row in the DataFrame and save it to the database
    for index, row in df.iterrows():
        career = Career(
            reg_date=row['시작일'],
            name=row['취업/인턴명'],
            company=row['회사'],
            url=row['세부사항'],
            deadline=row['종료일'],
            location=row['위치'],
            experience=row['경력조건'],
            jobtype=row['채용조건'],
            category=row['분야'],
            views=row['조회수']
        )
        db.session.add(career)

    db.session.commit()

## 2-4. 교내활동 데이터 저장 ##
def save_campus_csv_to_db():
    campus_path = "crawlling/result_campus.csv"
    df = pd.read_csv(campus_path, encoding='utf-8-sig')

    # 컬럼명 변경
    df.rename(columns={
        '교내활동명': 'title',
        '개시일': 'date',
        '세부사항': 'link',
        '조회수': 'views'
    }, inplace=True)
    
    df.to_sql('campus', con=db.engine, if_exists='append', index=False)


#### 3. DB 내 데이터 모델 정의 ####
## 3-1. 사용자(User) 데이터 모델 정의 ##
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128))
    email = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    school = db.Column(db.String(100))
    grade = db.Column(db.String(10))
    department = db.Column(db.String(100))
    activity_interests = db.Column(db.String(255))
    job_interests = db.Column(db.String(255))
    past_activities = db.Column(db.String(500))

    # 다대다 관계 설정
    activities = db.relationship('Activity', secondary='user_activity', backref=db.backref('users', lazy='dynamic'))

## 3-2. 공모전(Contest) 데이터 모델 정의 ##
class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    host = db.Column(db.String(100))
    organizer = db.Column(db.String(100))
    date = db.Column(db.String(100))
    type = db.Column(db.String(50))
    target = db.Column(db.String(100))
    award = db.Column(db.String(300))
    views = db.Column(db.Integer) # 조회수 정보 추가

    
## 3-3. 대외활동(Activity) 데이터 모델 정의 ##
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    host = db.Column(db.String(100))
    organizer = db.Column(db.String(100))
    date = db.Column(db.String(100))
    type = db.Column(db.String(50))
    target = db.Column(db.String(100))
    profit = db.Column(db.String(300))
    views = db.Column(db.Integer) # 조회수 정보 추가
    image_path = db.Column(db.String(300))  # 이미지 경로 추가


## 3-4. 취업/인턴(Career) 데이터 모델 정의 ##
class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_date = db.Column(db.String(50))
    name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    url = db.Column(db.String(300))
    deadline = db.Column(db.String(50))
    location = db.Column(db.String(100))
    experience = db.Column(db.String(300))
    jobtype = db.Column(db.String(50))
    category = db.Column(db.String(100))
    views = db.Column(db.Integer) # 조회수 정보 추가

## 3-5. 교내활동(Campus) 데이터 모델 정의 ##
class Campus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100)) 
    date = db.Column(db.String(50))
    link = db.Column(db.String(300))
    views = db.Column(db.Integer) # 조회수 정보 추가

## 사용자(User) - 공모전(Contest) M:N 관계 설정
user_contest = db.Table('user_contest',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('contest_id', db.Integer, db.ForeignKey('contest.id'))
)

## 사용자(User) - 대외활동(Activity) M:N 관계 설정
user_activity = db.Table('user_activity',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'))
)

## 사용자(User) - 취업/인턴(Career) M:N 관계 설정
user_career = db.Table('user_career',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('career_id', db.Integer, db.ForeignKey('career.id'))
)

## 사용자(User) - 교내활동(Campus) M:N 관계 설정
user_campus = db.Table('user_campus',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('campus_id', db.Integer, db.ForeignKey('campus.id'))
)

#### 4. 프로필 페이지 ####
## 4-1. 기본 프로필 페이지 ##
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

## 4-2. 사용자 정보 수정 기능 ##
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # 사용자가 입력한 아이디와 비밀번호
        entered_username = request.form['username']
        entered_password = request.form['password']
        
        # 현재 로그인된 사용자와 비밀번호 확인
        if current_user.username == entered_username and current_user.password == entered_password:
            # 사용자의 정보 업데이트
            current_user.username = request.form['username']
            current_user.password = request.form['password']
            current_user.name = request.form['name']
            current_user.email = request.form['email']
            current_user.birthdate = request.form['birthdate']
            current_user.gender = request.form['gender']
            current_user.school = request.form['school']
            current_user.grade = request.form['grade']
            current_user.department = request.form['department']

            # 공모전 / 대외활동 관심 분야를 체크박스로 처리
            activity_interests = request.form.getlist('activity_interests')
            current_user.activity_interests = ','.join(activity_interests)

            # 취업 / 인턴 관심 분야를 체크박스로 처리
            job_interests = request.form.getlist('job_interests')
            current_user.job_interests = ','.join(job_interests)

            current_user.past_activities = request.form.get('past_activities', '')

            db.session.commit()

            return redirect(url_for('profile'))
        else:
            # 아이디나 비밀번호가 일치하지 않는 경우에 대한 처리
            flash('아이디나 비밀번호가 일치하지 않습니다. 다시 시도해주세요.', 'error')

    return render_template('edit_profile.html', user=current_user)

## 4-3. 계정 삭제 기능 ##
@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # 현재 로그인한 사용자 가져오기
        user = current_user

        # 로그인한 사용자 정보 제거
        db.session.delete(user)
        db.session.commit()

        flash('계정이 성공적으로 삭제되었습니다.', 'success')
        return redirect(url_for('logout'))  # 로그아웃 페이지로 리다이렉트


#### 5. 사용자 인스턴스 로드 ####
# Flask-Login을 위한 사용자 로더 함수: 사용자 ID를 기반으로 사용자 인스턴스를 로드합니다.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#### 6. 홈페이지 기능 ####
## 6-1. 홈페이지 라우트: 루트 URL에 접속했을 때 보여지는 페이지 ##
@app.route('/')
def home():

    # 최신순 상위 5개 가져오기
    top_5_contests = Contest.query.limit(5).all()
    top_5_activities = Activity.query.limit(5).all()
    top_5_careers = Career.query.limit(5).all()
    top_5_campus = Campus.query.limit(5).all()
    top_5_recruitments = TeamRecruitment.query.order_by(TeamRecruitment.posted_date.desc()).limit(5).all()

    # 조회수별 상위 5개 가져오기
    top_5_contests_view = Contest.query.order_by(Contest.views.desc()).limit(5).all()
    top_5_activities_view = Activity.query.order_by(Activity.views.desc()).limit(5).all()
    top_5_careers_view = Career.query.order_by(Career.views.desc()).limit(5).all()
    top_5_campus_view = Campus.query.order_by(Campus.views.desc()).limit(5).all()

    return render_template('home.html', 
                           top_5_contests=top_5_contests, 
                           top_5_activities=top_5_activities, 
                           top_5_careers=top_5_careers, 
                           top_5_campus=top_5_campus,
                           top_5_recruitments=top_5_recruitments, 

                           top_5_contests_view=top_5_contests_view,
                           top_5_activities_view=top_5_activities_view,
                           top_5_careers_view=top_5_careers_view,
                           top_5_campus_view=top_5_campus_view)


## 6-1 (a) 공모전 세부 정보 ##
@app.route('/contest')
def show_contest():
    sort_by = request.args.get('sort_by', 'latest')
    page = int(request.args.get('page', 1))
    items_per_page = 10

    # 정렬 기준에 따른 쿼리 설정
    if sort_by == 'views':
        query = Contest.query.order_by(desc(Contest.views))
    elif sort_by == 'date':
        query = Contest.query.order_by(Contest.date)  # 'date' 필드를 datetime으로 저장하는 것을 권장합니다.
    else:
        query = Contest.query.order_by(desc(Contest.id))  # 최신순

    total_items = query.count()
    total_pages = math.ceil(total_items / items_per_page)

    contests = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

    return render_template('contest.html', 
                           contests=contests, 
                           page=page, 
                           total_pages=total_pages, 
                           sort_by=sort_by)

## 6-1 (b) 대외활동 세부 정보 ##
@app.route('/activities')
def show_activities():
    sort_by = request.args.get('sort_by', 'latest')
    page = int(request.args.get('page', 1))
    items_per_page = 10

    # 정렬 기준에 따른 쿼리 설정
    if sort_by == 'views':
        query = Activity.query.order_by(desc(Activity.views))
    elif sort_by == 'date':
        query = Activity.query.order_by(Activity.date)  # 'date' 필드를 datetime으로 저장하는 것을 권장합니다.
    else:
        query = Activity.query.order_by(desc(Activity.id))  # 최신순

    total_items = query.count()
    total_pages = math.ceil(total_items / items_per_page)

    activities = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

    return render_template('activities.html', 
                           activities=activities, 
                           page=page, 
                           total_pages=total_pages, 
                           sort_by=sort_by)


## 6-1 (c) 취업 / 인턴 세부 정보 ##
@app.route('/career')
def show_jobs():
    sort_by = request.args.get('sort_by', 'latest')
    page = int(request.args.get('page', 1))
    items_per_page = 10

    # 정렬 기준에 따른 쿼리 설정
    if sort_by == 'views':
        query = Career.query.order_by(desc(Career.views))
    elif sort_by == 'deadline':
        query = Career.query.order_by(Career.deadline)  # 'date' 필드를 datetime으로 저장하는 것을 권장합니다.
    else:
        query = Career.query.order_by(desc(Career.id))  # 최신순

    total_items = query.count()
    total_pages = math.ceil(total_items / items_per_page)

    careers = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

    return render_template('careers.html', 
                           careers=careers, 
                           page=page, 
                           total_pages=total_pages, 
                           sort_by=sort_by)


## 6-1 (d) 교내활동 세부 정보 ##
@app.route('/campus')
def show_campus():
    sort_by = request.args.get('sort_by', 'latest')
    page = int(request.args.get('page', 1))
    items_per_page = 10

    # 정렬 기준에 따른 쿼리 설정
    if sort_by == 'views':
        query = Campus.query.order_by(desc(Campus.views))
    elif sort_by == 'deadline':
        query = Campus.query.order_by(Campus.deadline)  # 'date' 필드를 datetime으로 저장하는 것을 권장합니다.
    else:
        query = Campus.query.order_by(desc(Campus.id))  # 최신순

    total_items = query.count()
    total_pages = math.ceil(total_items / items_per_page)

    campuses = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

    return render_template('campus.html', 
                           campuses=campuses, 
                           page=page, 
                           total_pages=total_pages, 
                           sort_by=sort_by)


#### 7. 검색 페이지 ####

## 7-1. 활동 검색 및 필터링 페이지 ##
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        activity_name = request.form.get('activity_name')
        activity_type = request.form.get('activity_type')

        print("Activity Name:", activity_name)
        print("Activity Type:", activity_type)

        return redirect(url_for('search_results', 
                                activity_name=activity_name, 
                                activity_type=activity_type))

    return render_template('search.html')


## 7-2 활동 검색 결과 페이지 ##
@app.route('/search_results')
def search_results():
    activity_type = request.args.get('activity_type', '').capitalize()
    activity_name = request.args.get('activity_name', '').lower()

    query = db.session.query(Contest, Activity, Career, Campus) if not activity_type else db.session.query(eval(activity_type))

    if activity_name:
        if activity_type == 'Campus':
            query = query.filter(Campus.title.ilike(f"%{activity_name}%"))
        elif activity_type:
            query = query.filter(eval(activity_type).name.ilike(f"%{activity_name}%"))
        else:
            # Combine queries from all models if activity_type is empty
            conditions = []
            for model in [Contest, Activity, Career, Campus]:
                if hasattr(model, 'name'):
                    conditions.append(model.name.ilike(f"%{activity_name}%"))
                elif hasattr(model, 'title'):  # Assuming Campus uses 'title' instead of 'name'
                    conditions.append(Campus.title.ilike(f"%{activity_name}%"))

            from sqlalchemy import or_
            query = db.session.query(Contest, Activity, Career, Campus).filter(or_(*conditions))

    results = query.all()
    return render_template('search_results.html', search_results=results, activity_type=activity_type or "All")


#### 8. 회원가입 페이지 ####
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # 필수 필드 검증
        required_fields = ['username', 'password', 'name', 'email', 'birthdate', 'gender', 'school', 'grade', 'department']
        missing_fields = [field for field in required_fields if not request.form.get(field)]

        if missing_fields:
            return f"Missing fields: {', '.join(missing_fields)}", 400

        # 관심 분야 처리
        activity_interests = ','.join(request.form.getlist('activity_interests'))
        job_interests = ','.join(request.form.getlist('job_interests'))

        # 사용자 정보 저장
        user = User(
            username=request.form['username'],
            password=request.form['password'],
            name=request.form['name'],
            email=request.form['email'],
            birthdate=request.form['birthdate'],
            gender=request.form['gender'],
            school=request.form['school'],
            grade=request.form['grade'],
            department=request.form['department'],
            activity_interests=activity_interests,
            job_interests=job_interests
        )
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))


#### 9. 로그인 페이지 ####
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # 비밀번호 검증
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            # 로그인 실패 시 홈 페이지로 리다이렉트하며 flash 메시지 전송
            flash('Invalid username or password', 'error')

            return redirect(url_for('home'))
    # GET 요청 시 로그인 페이지로 리다이렉트
    return redirect(url_for('home'))


#### 10. 로그인 후 나의 관심분야에 맞는 항목이 표시되는 대시보드 (로그인이 필수적) ####
@app.route('/dashboard')
@login_required
def dashboard():
    # 사용자의 관심 분야 가져오기
    user_activity_interests = current_user.activity_interests.split(',')
    user_job_interests = current_user.job_interests.split(',')


    # 조회수별 상위 5개 가져오기
    top_5_matching_contests_view = Contest.query\
        .filter(Contest.type.in_(user_activity_interests))\
        .order_by(Contest.views.desc())\
        .limit(5).all()
    top_5_matching_activities_view = Activity.query\
        .filter(Activity.type.in_(user_activity_interests))\
        .order_by(Activity.views.desc())\
        .limit(5).all()
    top_5_matching_careers_view = Career.query\
        .filter(Career.category.in_(user_job_interests))\
        .order_by(Career.views.desc())\
        .limit(5).all()
    top_5_matching_campus_view = Campus.query\
        .order_by(Campus.views.desc())\
        .limit(5).all()



    # 사용자의 관심 분야와 일치하는 활동 가져오기
    matching_contests = Contest.query.filter(Contest.type.in_(user_activity_interests)).limit(5).all()
    matching_activities = Activity.query.filter(Activity.type.in_(user_activity_interests)).limit(5).all()
    matching_careers = Career.query.filter(Career.category.in_(user_job_interests)).limit(5).all()
    matching_campuses = Campus.query.limit(5).all()
    top_5_recruitments = TeamRecruitment.query.order_by(TeamRecruitment.posted_date.desc()).limit(5).all()

    return render_template('dashboard.html', 
                           contests=matching_contests, 
                           activities=matching_activities, 
                           careers=matching_careers, 
                           campuses=matching_campuses,

                           top_5_matching_contests_view=top_5_matching_contests_view,
                           top_5_matching_activities_view=top_5_matching_activities_view,
                           top_5_matching_careers_view=top_5_matching_careers_view,
                           top_5_matching_campus_view=top_5_matching_campus_view,
                           
                           top_5_recruitments=top_5_recruitments)


### (상세 활동에서 이미지 로드를 위한 함수) ###
# 이미지 폴더 경로 입력을 위한 폼과 경로 저장 기능 추가
@app.route('/image_folder', methods=['GET', 'POST'])
def image_folder():
    global CONTEST_FOLDER, ACTIVITY_FOLDER
    if request.method == 'POST':
        contest_folder_path = request.form['contest_folder_path']
        activity_folder_path = request.form['activity_folder_path']
        
        CONTEST_FOLDER = contest_folder_path
        ACTIVITY_FOLDER = activity_folder_path
        
        app.config['CONTEST_FOLDER'] = CONTEST_FOLDER
        app.config['ACTIVITY_FOLDER'] = ACTIVITY_FOLDER
        
        return redirect(url_for('home'))  # 홈페이지로 리다이렉트

    # 이미지 폴더 경로를 입력하는 폼을 제공
    return '''
    <form method="post">
        공모전 이미지 폴더 경로: <input type="text" name="contest_folder_path" required><br>
        대외활동 이미지 폴더 경로: <input type="text" name="activity_folder_path" required><br>
        <input type="submit" value="저장">
    </form>
    '''


#### 11. 활동 상세 페이지 ####
## 11-1. 공모전 상세 페이지 ##
@app.route('/dashboard/<int:contest_id>')
def contest_detail(contest_id):
    contest = Contest.query.get(contest_id)

    contest.views += 1
    db.session.commit()
    
    # 이미지 파일 경로 설정
    image_filename = f"{contest_id}"  # 이미지 파일명은 contest_id보다 1 작은 값으로 설정
    image_path = os.path.join(app.config['CONTEST_FOLDER'], f"{image_filename}.jpg")

    # 이미지 파일이 존재하는지 확인
    if os.path.exists(image_path):
        contest.image = f"{app.config['CONTEST_FOLDER']}/{image_filename}.jpg"  # 이미지 경로를 contest 객체에 추가
    else:
        # 만약 .jpg 파일이 존재하지 않으면 다른 확장자를 시도
        possible_extensions = ['.jpg', '.jpeg', '.png', '.gif']  # 여러 확장자 가능성 고려
        for ext in possible_extensions:
            image_path = os.path.join(app.config['CONTEST_FOLDER'], f"{image_filename}{ext}")
            if os.path.exists(image_path):
                contest.image = f"{app.config['CONTEST_FOLDER']}/{image_filename}{ext}"  # 이미지 경로를 contest 객체에 추가
                break

    return render_template('contest_detail.html', contest=contest)


## 11-2. 대외활동 상세 페이지 ##
@app.route('/activity/<int:activity_id>')
def activity_detail(activity_id):
    activity = Activity.query.get(activity_id)

    activity.views += 1
    db.session.commit()

    # 이미지 파일 경로 설정
    image_filename = f"{activity_id - 1}"  # 이미지 파일명은 contest_id보다 1 작은 값으로 설정
    image_path = os.path.join(app.config['ACTIVITY_FOLDER'], f"{image_filename}.jpg")

    # 이미지 파일이 존재하는지 확인
    if os.path.exists(image_path):
        activity.image = f"activity_info/{image_filename}.jpg"  # 이미지 경로를 contest 객체에 추가
    else:
        # 만약 .jpg 파일이 존재하지 않으면 다른 확장자를 시도
        possible_extensions = ['.jpg', '.jpeg', '.png', '.gif']  # 여러 확장자 가능성 고려
        for ext in possible_extensions:
            image_path = os.path.join(app.config['ACTIVITY_FOLDER'], f"{image_filename}{ext}")
            if os.path.exists(image_path):
                activity.image = f"activity_info/{image_filename}{ext}"  # 이미지 경로를 contest 객체에 추가
                break

    return render_template('activity_detail.html', activity=activity)

## 11-3. 취업/인턴 상세 페이지 ##
@app.route('/career/<int:career_id>')
def career_detail(career_id):
    career = Career.query.get(career_id)

    career.views += 1
    db.session.commit()
    
    return render_template('career_detail.html', career=career)

## 11-4. 교내활동 상세 페이지 ##
@app.route('/campus/<int:campus_id>')
def campus_detail(campus_id):
    campus = Campus.query.get(campus_id)

    campus.views += 1
    db.session.commit()

    return render_template('campus_detail.html', campus=campus)


#### 12. 즐겨찾기 페이지 ####
## 12-1. 사용자 즐겨찾기 모델 정의 ##
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'))
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'))

## 12-2. 추가 ##
## 공모전 ##
@app.route('/add_to_favorites/contest/<int:contest_id>', methods=['POST'])
@login_required
def add_contest_to_favorites(contest_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    favorite = Favorite.query.filter_by(user_id=current_user.id, contest_id=contest_id).first()
    if favorite:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 즐겨찾기에 추가된 공모전입니다.', 'warning')
    else:
        # 즐겨찾기에 추가되어 있지 않은 경우, 추가합니다.
        favorite = Favorite(user_id=current_user.id, contest_id=contest_id)
        db.session.add(favorite)
        db.session.commit()
        flash('공모전이 즐겨찾기에 추가되었습니다.', 'success')
    return redirect(url_for('contest_detail', contest_id=contest_id))

## 대외활동 ##
@app.route('/add_to_favorites/activity/<int:activity_id>', methods=['POST'])
@login_required
def add_activity_to_favorites(activity_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    favorite = Favorite.query.filter_by(user_id=current_user.id, activity_id=activity_id).first()
    if favorite:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 즐겨찾기에 추가된 대외활동입니다.', 'warning')
    else:
        # 즐겨찾기에 추가되어 있지 않은 경우, 추가합니다.
        favorite = Favorite(user_id=current_user.id, activity_id=activity_id)
        db.session.add(favorite)
        db.session.commit()
        flash('대외활동이 즐겨찾기에 추가되었습니다.', 'success')
    return redirect(url_for('activity_detail', activity_id=activity_id))

## 취업 및 인턴 활동 ##
@app.route('/add_to_favorites/career/<int:career_id>', methods=['POST'])
@login_required
def add_careers_to_favorites(career_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    favorite = Favorite.query.filter_by(user_id=current_user.id, career_id=career_id).first()
    if favorite:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 즐겨찾기에 추가된 대외활동입니다.', 'warning')
    else:
        # 즐겨찾기에 추가되어 있지 않은 경우, 추가합니다.
        favorite = Favorite(user_id=current_user.id, career_id=career_id)
        db.session.add(favorite)
        db.session.commit()
        flash('공고활동이 즐겨찾기에 추가되었습니다.', 'success')
    return redirect(url_for('career_detail', career_id=career_id))

## 교내활동 ##
@app.route('/add_to_favorites/campus/<int:campus_id>', methods=['POST'])
@login_required
def add_campus_to_favorites(campus_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    favorite = Favorite.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
    if favorite:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 즐겨찾기에 추가된 교내활동입니다.', 'warning')
    else:
        # 즐겨찾기에 추가되어 있지 않은 경우, 추가합니다.
        favorite = Favorite(user_id=current_user.id, campus_id=campus_id)
        db.session.add(favorite)
        db.session.commit()
        flash('교내활동이 즐겨찾기에 추가되었습니다.', 'success')
    return redirect(url_for('campus_detail', campus_id=campus_id))


## 12-3.삭제 ##
## 공모전 ##
@app.route('/remove_contests_from_favorites', methods=['POST'])
@login_required
def remove_contests_from_favorites():
    if request.method == 'POST':
        contest_ids = request.form.getlist('contest_ids[]')
        for contest_id in contest_ids:
            favorite = Favorite.query.filter_by(user_id=current_user.id, contest_id=contest_id).first()
            if favorite:
                db.session.delete(favorite)
        db.session.commit()
        flash('선택한 공모전이 즐겨찾기에서 제거되었습니다.', 'success')
        return redirect(url_for('favorites'))

## 대외활동 ##
@app.route('/remove_activities_from_favorites', methods=['POST'])
@login_required
def remove_activities_from_favorites():
    if request.method == 'POST':
        activity_ids = request.form.getlist('activity_ids[]')
        for activity_id in activity_ids:
            favorite = Favorite.query.filter_by(user_id=current_user.id, activity_id=activity_id).first()
            if favorite:
                db.session.delete(favorite)
        db.session.commit()
        flash('선택한 대외활동이 즐겨찾기에서 제거되었습니다.', 'success')
        return redirect(url_for('favorites'))

## 취업 및 인턴 활동 ##
@app.route('/remove_careers_from_favorites', methods=['POST'])
@login_required
def remove_careers_from_favorites():
    if request.method == 'POST':
        career_ids = request.form.getlist('career_ids[]')
        for career_id in career_ids:
            favorite = Favorite.query.filter_by(user_id=current_user.id, career_id=career_id).first()
            if favorite:
                db.session.delete(favorite)
        db.session.commit()
        flash('선택한 대외활동이 즐겨찾기에서 제거되었습니다.', 'success')
        return redirect(url_for('favorites'))

## 교내활동 ##
@app.route('/remove_campus_from_favorites', methods=['POST'])
@login_required
def remove_campus_from_favorites():
    if request.method == 'POST':
        campus_ids = request.form.getlist('campus_ids[]')
        for campus_id in campus_ids:
            favorite = Favorite.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
            if favorite:
                db.session.delete(favorite)
        db.session.commit()
        flash('선택한 교내활동이 즐겨찾기에서 제거되었습니다.', 'success')
        return redirect(url_for('favorites'))
    

## 12-4. 즐겨찾기 페이지 라우트 ##
@app.route('/favorites')
@login_required
def favorites():
    # 사용자의 즐겨찾기 목록 가져오기
    user_favorites = Favorite.query.filter_by(user_id=current_user.id).all()

    # 즐겨찾기에 추가된 공모전과 대외활동 가져오기
    favorite_contests = [Contest.query.get(f.contest_id) for f in user_favorites if f.contest_id]
    favorite_activities = [Activity.query.get(f.activity_id) for f in user_favorites if f.activity_id]
    favorite_careers = [Career.query.get(f.career_id) for f in user_favorites if f.career_id]
    favorite_campus = [Campus.query.get(f.campus_id) for f in user_favorites if f.campus_id]

    return render_template('favorites.html', favorite_contests=favorite_contests, favorite_activities=favorite_activities, 
                           favorite_careers=favorite_careers, favorite_campus=favorite_campus)


#### 13. 포트폴리오 페이지 ####
## 13-1. 사용자 포트폴리오 모델 정의 ##
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    career_id = db.Column(db.Integer, db.ForeignKey('career.id'))
    campus_id = db.Column(db.Integer, db.ForeignKey('campus.id'))

## 13-2. 추가 ##
## 공모전 ##
@app.route('/add_to_portfolio/contest/<int:contest_id>', methods=['POST'])
@login_required
def add_contest_to_portfolio(contest_id):
    # 이미 포트폴리오에 추가되어 있는지 확인
    portfolio = Portfolio.query.filter_by(user_id=current_user.id, contest_id=contest_id).first()
    if portfolio:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 포트폴리오에 추가된 공모전입니다.', 'warning')
    else:
        # 포트폴리오에 추가되어 있지 않은 경우, 추가합니다.
        portfolio = Portfolio(user_id=current_user.id, contest_id=contest_id)
        db.session.add(portfolio)
        db.session.commit()
        flash('공모전이 포트폴리오에 추가되었습니다.', 'success')
    return redirect(url_for('contest_detail', contest_id=contest_id))

## 대외활동 ##
@app.route('/add_to_portfolio/activity/<int:activity_id>', methods=['POST'])
@login_required
def add_activity_to_portfolio(activity_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    portfolio = Portfolio.query.filter_by(user_id=current_user.id, activity_id=activity_id).first()
    if portfolio:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 즐겨찾기에 추가된 대외활동입니다.', 'warning')
    else:
        # 즐겨찾기에 추가되어 있지 않은 경우, 추가합니다.
        portfolio = Portfolio(user_id=current_user.id, activity_id=activity_id)
        db.session.add(portfolio)
        db.session.commit()
        flash('대외활동이 포트폴리오에 추가되었습니다.', 'success')
    return redirect(url_for('activity_detail', activity_id=activity_id))

## 취업 및 인턴 활동 ##
@app.route('/add_to_portfolio/career/<int:career_id>', methods=['POST'])
@login_required
def add_careers_to_portfolio(career_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    portfolio = Portfolio.query.filter_by(user_id=current_user.id, career_id=career_id).first()
    if portfolio:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 포트폴리오에 추가된 대외활동입니다.', 'warning')
    else:
        # 즐겨찾기에 추가되어 있지 않은 경우, 추가합니다.
        portfolio = Portfolio(user_id=current_user.id, career_id=career_id)
        db.session.add(portfolio)
        db.session.commit()
        flash('공고활동이 포트폴리오에 추가되었습니다.', 'success')
    return redirect(url_for('career_detail', career_id=career_id))

## 교내활동 ##
@app.route('/add_to_portfolio/campus/<int:campus_id>', methods=['POST'])
@login_required
def add_campus_to_portfolio(campus_id):
    # 이미 즐겨찾기에 추가되어 있는지 확인
    portfolio = Portfolio.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
    if portfolio:
        # 이미 추가된 경우, 경고 메시지를 보여줍니다.
        flash('이미 포트폴리오에 추가된 교내활동입니다.', 'warning')
    else:
        # 포트폴리오에 추가되어 있지 않은 경우, 추가합니다.
        portfolio = Portfolio(user_id=current_user.id, campus_id=campus_id)
        db.session.add(portfolio)
        db.session.commit()
        flash('교내활동이 포트폴리오에 추가되었습니다.', 'success')
    return redirect(url_for('campus_detail', campus_id=campus_id))

## 13-3.삭제 ##
## 공모전 ##
@app.route('/remove_contests_from_portfolio', methods=['POST'])
@login_required
def remove_contests_from_portfolio():
    if request.method == 'POST':
        contest_ids = request.form.getlist('contest_ids[]')
        for contest_id in contest_ids:
            portfolio = Portfolio.query.filter_by(user_id=current_user.id, contest_id=contest_id).first()
            if portfolio:
                db.session.delete(portfolio)
        db.session.commit()
        flash('선택한 공모전이 포트폴리오에서 제거되었습니다.', 'success')
        return redirect(url_for('portfolio'))

## 대외활동 ##
@app.route('/remove_activities_from_portfolio', methods=['POST'])
@login_required
def remove_activities_from_portfolio():
    if request.method == 'POST':
        activity_ids = request.form.getlist('activity_ids[]')
        for activity_id in activity_ids:
            portfolio = Portfolio.query.filter_by(user_id=current_user.id, activity_id=activity_id).first()
            if portfolio:
                db.session.delete(portfolio)
        db.session.commit()
        flash('선택한 대외활동이 포트폴리오에서 제거되었습니다.', 'success')
        return redirect(url_for('portfolio'))

## 취업 및 인턴 활동 ##
@app.route('/remove_careers_from_portfolio', methods=['POST'])
@login_required
def remove_careers_from_portfolio():
    if request.method == 'POST':
        career_ids = request.form.getlist('career_ids[]')
        for career_id in career_ids:
            portfolio = Portfolio.query.filter_by(user_id=current_user.id, career_id=career_id).first()
            if portfolio:
                db.session.delete(portfolio)
        db.session.commit()
        flash('선택한 대외활동이 포트폴리오에서 제거되었습니다.', 'success')
        return redirect(url_for('portfolio'))

## 교내활동 ##
@app.route('/remove_campus_from_portfolio', methods=['POST'])
@login_required
def remove_campus_from_portfolio():
    if request.method == 'POST':
        campus_ids = request.form.getlist('campus_ids[]')
        for campus_id in campus_ids:
            portfolio = Portfolio.query.filter_by(user_id=current_user.id, campus_id=campus_id).first()
            if portfolio:
                db.session.delete(portfolio)
        db.session.commit()
        flash('선택한 교내활동이 포트폴리오에서 제거되었습니다.', 'success')
        return redirect(url_for('portfolio'))
    

## 13-4. 포트폴리오 페이지 라우트 ##
@app.route('/portfolio')
@login_required
def portfolio():
    # 사용자의 참여활동 목록 가져오기
    user_portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()

    # 포트폴리오에 추가된 공모전과 대외활동 가져오기
    portfolio_contests = [Contest.query.get(f.contest_id) for f in user_portfolios if f.contest_id]
    portfolio_activities = [Activity.query.get(f.activity_id) for f in user_portfolios if f.activity_id]
    portfolio_careers = [Career.query.get(f.career_id) for f in user_portfolios if f.career_id]
    portfolio_campus = [Campus.query.get(f.campus_id) for f in user_portfolios if f.campus_id]

    return render_template('portfolio.html', portfolio_contests=portfolio_contests, portfolio_activities=portfolio_activities, 
                           portfolio_careers=portfolio_careers, portfolio_campus=portfolio_campus, user=current_user)

## 13-5. 포트폴리오 사진 업로드 ##
profile_photos = "static/profile_photos"
app.config['PROFILE_PHOTOS'] = profile_photos


if not os.path.exists(profile_photos):
    os.makedirs(profile_photos)

@app.route('/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    user_id = current_user.id
    file = request.files['photo']
    if file:
        filename = secure_filename(f"{user_id}.jpg")
        file.save(os.path.join(app.config['PROFILE_PHOTOS'], filename))
    return redirect(url_for('portfolio'))

#### 14. 구인구팀 페이지 ####

## 구인구팀(TeamRecruitment) 데이터 모델 정의 ##
class TeamRecruitment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_name = db.Column(db.String(100), nullable=False)
    team_member_count = db.Column(db.Integer, nullable=False)
    recruitment_period = db.Column(db.String(100), nullable=False)
    activity_period = db.Column(db.String(100), nullable=False)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('recruitments', lazy=True))
    comments = db.relationship('Comment', backref='recruitment', lazy=True)

##댓글##
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    posted_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recruitment_id = db.Column(db.Integer, db.ForeignKey('team_recruitment.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

## 14-1. 구인구팀 페이지 ##
@app.route('/team_recruitment')
@login_required
def team_recruitment():
    recruitments = TeamRecruitment.query.order_by(TeamRecruitment.posted_date.desc()).all()
    return render_template('team_recruitment.html', recruitments=recruitments)


## 14-2. 구인구팀 게시글 업로드 ##
@app.route('/add_team_recruitment', methods=['GET', 'POST'])
@login_required
def add_team_recruitment():
    if request.method == 'POST':
        contest_name = request.form.get('contest_name')
        team_member_count = request.form.get('team_member_count')
        recruitment_period = request.form.get('recruitment_period')
        activity_period = request.form.get('activity_period')
        
        # 폼 데이터가 존재하는지 확인
        if not all([contest_name, team_member_count, recruitment_period, activity_period]):
            flash('모든 필드를 입력해주세요.', 'error')
            return redirect(url_for('add_team_recruitment'))

        new_recruitment = TeamRecruitment(
            contest_name=contest_name,
            team_member_count=team_member_count,
            recruitment_period=recruitment_period,
            activity_period=activity_period,
            user_id=current_user.id
        )

        db.session.add(new_recruitment)
        db.session.commit()
        flash('팀 모집글이 성공적으로 등록되었습니다.', 'success')
        return redirect(url_for('team_recruitment'))
    
    return render_template('add_team_recruitment.html')

## 14-3. 구인구팀 게시글 삭제 ##
@app.route('/delete_team_recruitment/<int:id>', methods=['POST'])
@login_required
def delete_team_recruitment(id):
    recruitment = TeamRecruitment.query.get_or_404(id)
    if recruitment.user_id != current_user.id:
        flash('삭제 권한이 없습니다.', 'error')
        return redirect(url_for('team_recruitment'))
    
    db.session.delete(recruitment)
    db.session.commit()
    flash('팀 모집글이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('team_recruitment'))

##14-4. 구인구팀 상세페이지##
@app.route('/team_recruitment/<int:id>', methods=['GET', 'POST'])
def team_recruitment_detail(id):
    recruitment = TeamRecruitment.query.get_or_404(id)
    
    if request.method == 'POST':
        content = request.form['content']
        user_id = current_user.id  # Assuming you have current_user from flask_login
        if content:
            comment = Comment(content=content, user_id=user_id, recruitment_id=id)
            db.session.add(comment)
            db.session.commit()
            flash('댓글이 추가되었습니다!', 'success')
        else:
            flash('댓글 내용을 입력해주세요.', 'error')
        return redirect(url_for('team_recruitment_detail', id=id))
    
    comments = Comment.query.filter_by(recruitment_id=id).order_by(Comment.posted_date.asc()).all()
    return render_template('team_recruitment_detail.html', recruitment=recruitment, comments=comments)

#### 15. 로그아웃 기능 라우트 ####
@app.route('/logout')
@login_required
def logout():
    logout_user()  # 사용자 로그아웃
    return redirect(url_for('home'))  # 홈페이지로 리다이렉트

def load_initial_data():
    """데이터베이스에 초기 데이터를 로드하는 함수"""
    try:
        if not Contest.query.first():  # Contest 테이블이 비어있는지 확인
            save_contest_csv_to_db()  # 공모전 CSV 파일을 데이터베이스에 저장
        if not Activity.query.first():  # Activity 테이블이 비어있는지 확인
            save_activities_csv_to_db()  # 대외활동 CSV 파일을 데이터베이스에 저장
        if not Career.query.first():  # Career 테이블이 비어있는지 확인
            save_career_csv_to_db()  # 취업/인턴 CSV 파일을 데이터베이스에 저장
        if not Campus.query.first():  # Campus 테이블이 비어있는지 확인
            save_campus_csv_to_db()  # 교내활동 CSV 파일을 데이터베이스에 저장
    except IntegrityError:
        db.session.rollback()

#### 앱 실행 ####
if __name__ == '__main__':
    with app.app_context():        
        # 데이터베이스 초기화 및 CSV 파일 데이터 로드
        # db.drop_all()  # 기존 테이블 삭제
        db.create_all()  # 새로운 테이블 생성

        load_initial_data()  # 초기 데이터 로드 로직 실행

        # save_contest_csv_to_db()  # 공모전 CSV 파일을 데이터베이스에 저장
        # save_activities_csv_to_db()  # 대외활동 CSV 파일을 데이터베이스에 저장
        # save_career_csv_to_db()  # 취업/인턴 CSV 파일을 데이터베이스에 저장
        # save_campus_csv_to_db()  # 교내활동 CSV 파일을 데이터베이스에 저장

    app.run(debug=True)  # 디버그 모드로 앱 실행

