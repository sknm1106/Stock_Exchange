# 🎓 Engineering Stock Exchange (공과대학 모의 주식 거래소)

> **공과대학 12개 학과를 하나의 "주식 상품"으로 만들어 학생들이 가상 코인으로 투자하는 모의 주식 거래 웹서비스**

---

## 🌟 주요 특징

1. **🚀 QR 코드 접속 & 간편 자동 로그인**
   - 별도의 회원가입 없이 **학번 + 이름** 입력만으로 즉시 로그인됩니다.
   - **최초 로그인 보상**: 처음 접속한 참가자에게만 **100 Coin**이 자동 지급됩니다.
   - 기존 사용자는 접속 시 보유 자산(코인 및 학과 주식)을 그대로 불러옵니다.

2. **📊 실시간 증권 플랫폼 스타일 메인 화면**
   - 공과대학 12개 학과 주식 시세표 (현재가, 전일/전시간 대비 등락, 변동률).
   - 최고 상승 학과, 최대 하락 학과, 평균 주가 등 시장 개요 카드.
   - 학과명 및 코드 실시간 검색 필터링.
   - 공과대학 최근 뉴스 및 호재/악재 공시 게시판.

3. **🔍 학과 상세 페이지 & 매수/매도 거래**
   - Plotly 기반의 인터렉티브 주가 차트 (최고가/최저가 표시, 마우스 호버 등).
   - 보유 코인 잔액 기반 **매수 (Buy)** 및 보유 수량 기반 **매도 (Sell)**.
   - 빠른 주문을 위한 **25% / 50% / 최대 (100%)** 수량 자동 계산 버튼.

4. **💼 포트폴리오 관리**
   - 보유 현금 코인, 주식 평가금액, 총 자산, 투자 원금 및 총 평가손익 (수익률 %) 한눈에 확인.
   - Plotly 도넛 차트를 활용한 자산 구성비 (Asset Allocation) 시각화.
   - 학과별 보유 수량, 평단가, 현재가, 평가손익 및 나의 상세 거래 내역 Log.

5. **⏰ 매 1시간 자동 주가 변동 시스템 (APScheduler)**
   - 백그라운드 스케줄러가 매 1시간마다 학과 주가를 자동 업데이트 및 가격 기록(`price_history`) 저장.

6. **⚙️ 관리자 컨트롤 센터 (Admin Page)**
   - 암호 인증 (기본: `admin123`).
   - 학과 현재가 즉시 수정 및 수동 1시간 변동 즉시 실행 테스트 버튼.
   - CSV 파일 일괄 주가 업로드.
   - 참가자 학번 검색 및 이벤트 코인 지급/차감.
   - 학과 뉴스 및 공시 등록 (BULLISH / BEARISH / NEUTRAL).
   - 전체 데이터베이스 초기화 (Reset).

---

## 🏛️ 학과 목록 (9개)

1. 사회환경공학부
2. 기계·로봇·자동차공학부
3. 전기전자공학부
4. 화공·생명·에너지공학부
5. 컴퓨터공학부
6. 재료공학과
7. 항공우주·모빌리티공학과
8. 생물공학과
9. 산업공학과

---

## 📂 프로젝트 구조

```
Stock_Exchange/
├── app.py                      # 메인 진입점 및 라우팅
├── pages/
│   ├── 1_Login.py             # 로그인 (학번 + 이름)
│   ├── 2_Home.py              # 메인 주식 시세표 & 시장 개요
│   ├── 3_Department.py        # 학과 상세 & 매수/매도 거래
│   ├── 4_Portfolio.py         # 내 포트폴리오 & 자산 현황
│   └── 5_Admin.py             # 관리자 페이지 (비밀번호: admin123)
├── database/
│   ├── db.py                  # SQLite DB 초기화 & 커넥션
│   ├── models.py              # 데이터 모델 정의
│   └── seed.py                # 디폴트 학과 및 시세 시드 데이터
├── scheduler/
│   └── scheduler.py           # APScheduler 기반 1시간 주가 자동 변동
├── utils/
│   ├── auth.py                # 로그인 & 사용자 관리
│   ├── trade.py               # 주식 매수/매도 & 포트폴리오 계산
│   ├── graph.py               # Plotly 차트 생성기
│   ├── database.py            # SQLite 쿼리 유틸리티
│   └── ui.py                  # 커스텀 테마 CSS & 헤더 바
├── data/
│   ├── departments.csv        # 12개 학과 정보 CSV
│   └── prices.csv             # 초기 시세 이력 CSV
├── requirements.txt           # 의존성 패키지 목록
└── README.md                  # 안내 문서
```

---

## 💻 로컬 실행 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. Streamlit 앱 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속하여 확인합니다.

---

## 🚀 배포 가이드 (Deploy Guide)

### 옵션 1: Streamlit Community Cloud (권장)
1. 본 프로젝트를 GitHub 리포지토리에 푸시합니다.
2. [share.streamlit.io](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.
3. `New App` 클릭 후 해당 Repository, Branch(`main`), Main file path (`app.py`)를 선택하고 `Deploy`를 클릭합니다.

### 옵션 2: Render / Heroku
1. Render([render.com](https://render.com))에서 `Web Service` 생성.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

---

## 🎪 행사장 운영 꿀팁 (QR 코드 비치)

1. 배포 후 생성된 URL (예: `https://engineering-stock.streamlit.app`)을 무료 QR 코드 생성 사이트(예: [qr-code-generator.com](https://www.qr-code-generator.com/))에서 QR 코드로 변환합니다.
2. QR 코드를 포스터나 안내판에 출력하여 행사장에 비치합니다.
3. 학생들은 별도 앱 설치 없이 스마트폰 카메라로 QR 코드를 스캔하여 접속, **학번과 이름**만 입력하면 바로 **100 Coin**을 받아 주식 거래에 참여할 수 있습니다!
