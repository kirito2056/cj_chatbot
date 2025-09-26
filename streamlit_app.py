import os
import streamlit as st
import json
import requests
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SerpAPIWrapper
from langchain.agents import create_tool_calling_agent, AgentExecutor, Tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 페이지 설정
st.set_page_config(
    page_title="AI 비서 톡톡이", 
    layout="wide", 
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# 🎨 다크/라이트 모드 관리
def apply_theme_styles(theme):
    """테마에 따른 스타일 적용"""
    if theme == "dark":
        bg_color = "#0e1117"
        text_color = "#fafafa"
        secondary_bg = "#262730"
        border_color = "rgba(255, 255, 255, 0.2)"
        sidebar_bg = "#262730"
        chat_bg = "rgba(255, 255, 255, 0.05)"
        color_scheme = "dark"
        # 다크모드: 어두운 회색 버튼, 흰 글자
        button_bg = "#374151"
        button_text = "white"
        button_hover_bg = "white"
        button_hover_text = "#374151"
    else:  # light mode
        bg_color = "#ffffff"
        text_color = "#262730"
        secondary_bg = "#f0f2f6"
        border_color = "rgba(0, 0, 0, 0.2)"
        sidebar_bg = "#f0f2f6"
        chat_bg = "rgba(0, 0, 0, 0.02)"
        color_scheme = "light"
        # 라이트모드: 흰색 버튼, 검은색 글자
        button_bg = "white"
        button_text = "#374151"
        button_hover_bg = "#374151"
        button_hover_text = "white"
    
    return f"""
    <style>
        /* 전역 테마 설정 - 매우 강제 적용 */
        .stApp, .stApp *, 
        [data-testid="stAppViewContainer"],
        .main, .main *,
        section[data-testid="main"],
        section[data-testid="main"] * {{
            color: {text_color} !important;
        }}
        
        .stApp,
        [data-testid="stAppViewContainer"],
        body,
        html,
        .main,
        section[data-testid="main"] {{
            background-color: {bg_color} !important;
        }}
        
        /* 브라우저 다크모드 무시 - 강제 라이트/다크 적용 */
        html, body {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            color-scheme: {color_scheme} !important;
        }}
        
        /* 메인 콘텐츠 영역 텍스트 색상 */
        .main .block-container, .main .block-container * {{
            color: {text_color} !important;
        }}
        
        /* 메인 헤더 스타일 */
        .main-header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white !important;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .main-header h1 {{
            color: white !important;
            margin: 0;
            font-size: 2.5rem;
        }}
        
        .main-header p {{
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0.5rem 0 0 0;
            font-size: 1.2rem;
        }}
        
        /* 사이드바 스타일 - 매우 강력한 색상 적용 */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        .css-1d391kg,
        .css-1kyxreq {{
            background-color: {sidebar_bg} !important;
        }}
        
        [data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] *,
        .css-1d391kg *,
        .css-1kyxreq * {{
            color: {text_color} !important;
        }}
        
        [data-testid="stSidebar"] .markdown-text-container {{
            color: {text_color} !important;
        }}
        
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stMarkdown *,
        [data-testid="stSidebar"] .element-container,
        [data-testid="stSidebar"] .element-container *,
        section[data-testid="stSidebar"] *,
        .css-1d391kg,
        .css-1d391kg *,
        .css-1kyxreq,
        .css-1kyxreq * {{
            color: {text_color} !important;
        }}
        
        /* 사이드바 내 텍스트 입력 레이블 */
        [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] label {{
            color: {text_color} !important;
            font-weight: bold !important;
        }}
        
        /* 채팅 메시지 스타일 */
        .stChatMessage {{
            background: {chat_bg} !important;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid {border_color};
        }}
        
        .stChatMessage * {{
            color: {text_color} !important;
        }}
        
        /* 입력창 스타일 */
        .stTextInput > div > div > input {{
            background-color: {secondary_bg} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
        }}
        
        .stTextInput label {{
            color: {text_color} !important;
        }}
        
        /* placeholder 텍스트 색상 (API 키 예시 등) */
        .stTextInput > div > div > input::placeholder {{
            color: #888888 !important;
            opacity: 0.7 !important;
        }}
        
        /* 패스워드 입력창 placeholder */
        input[type="password"]::placeholder {{
            color: #888888 !important;
            opacity: 0.7 !important;
        }}
        
        /* 패스워드 입력창 눈 아이콘 (비밀번호 보기 버튼) */
        .stTextInput > div > div > button,
        [data-testid="textInputContainer"] button,
        .stTextInput button {{
            background-color: {text_color} !important;
            color: {bg_color} !important;
            border: 1px solid {border_color} !important;
            border-radius: 4px !important;
        }}
        
        .stTextInput > div > div > button:hover,
        [data-testid="textInputContainer"] button:hover,
        .stTextInput button:hover {{
            background-color: {secondary_bg} !important;
            color: {text_color} !important;
        }}
        
        /* 눈 아이콘 자체 스타일 */
        .stTextInput svg,
        [data-testid="textInputContainer"] svg {{
            fill: {bg_color} !important;
            color: {bg_color} !important;
        }}
        
        .stTextInput button:hover svg,
        [data-testid="textInputContainer"] button:hover svg {{
            fill: {text_color} !important;
            color: {text_color} !important;
        }}
        
        /* 셀렉트박스 스타일 */
        .stSelectbox > div > div > div {{
            background-color: {secondary_bg} !important;
            color: {text_color} !important;
        }}
        
        .stSelectbox label {{
            color: {text_color} !important;
        }}
        
        /* 마크다운 텍스트 */
        .stMarkdown, .stMarkdown * {{
            color: {text_color} !important;
        }}
        
        /* 일반 텍스트 요소들 - 모든 곳에 적용 */
        p, div, span, h1, h2, h3, h4, h5, h6, label, 
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span,
        .element-container, .element-container *,
        .block-container, .block-container *,
        .css-1kyxreq, .css-1kyxreq *,
        .css-1d391kg, .css-1d391kg * {{
            color: {text_color} !important;
        }}
        
        /* 특별히 사이드바의 "🔑 API 키 설정" 텍스트를 위한 스타일 */
        [data-testid="stSidebar"] .stMarkdown h3,
        [data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h3 {{
            color: {text_color} !important;
            font-size: 1.2rem !important;
            margin: 1rem 0 0.5rem 0 !important;
        }}
        
        /* 버튼 스타일 - 테마별 색상 (높은 우선순위) */
        .stApp .stButton > button,
        section[data-testid="stSidebar"] .stButton > button,
        div[data-testid="stSidebar"] .stButton > button,
        .stButton > button {{
            background-color: {button_bg} !important;
            color: {button_text} !important;
            border: 2px solid {button_bg} !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.6s ease !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }}
        
        .stApp .stButton > button:hover,
        section[data-testid="stSidebar"] .stButton > button:hover,
        div[data-testid="stSidebar"] .stButton > button:hover,
        .stButton > button:hover,
        button:hover,
        [data-testid="stSidebar"] button:hover,
        .stApp button:hover {{
            background-color: {button_hover_bg} !important;
            color: {button_hover_text} !important;
            border: 2px solid {button_bg} !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }}
        
        /* 호버 시 텍스트 색상 강제 적용 */
        .stButton > button:hover *,
        button:hover *,
        [data-testid="stSidebar"] button:hover *,
        .stApp button:hover * {{
            color: {button_hover_text} !important;
        }}
        
        /* 특별한 버튼 ID 선택자로 더 강력하게 */
        button[kind="primary"],
        button[kind="secondary"],
        button[data-testid] {{
            background-color: {button_bg} !important;
            color: {button_text} !important;
            border: 2px solid {button_bg} !important;
        }}
        
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        button[data-testid]:hover {{
            background-color: {button_hover_bg} !important;
            color: {button_hover_text} !important;
        }}
        
        /* 매우 강력한 호버 텍스트 색상 적용 */
        .stButton:hover,
        .stButton:hover *,
        .stButton:hover button,
        .stButton:hover button *,
        button:hover span,
        button:hover div,
        button:hover p {{
            color: {button_hover_text} !important;
        }}
        
        /* 대화 기록 삭제 버튼 특별 스타일 */
        .stButton > button[aria-label*="삭제"], 
        .stButton > button:contains("대화 기록 삭제"),
        .stButton > button:contains("🗑️") {{
            background-color: #dc2626 !important;
            color: white !important;
            border: 2px solid #dc2626 !important;
            transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        
        .stButton > button[aria-label*="삭제"]:hover,
        .stButton > button:contains("대화 기록 삭제"):hover,
        .stButton > button:contains("🗑️"):hover {{
            background-color: #b91c1c !important;
            color: white !important;
            border: 2px solid #b91c1c !important;
            transform: translateY(-3px) !important;
            box-shadow: 0 6px 12px rgba(220, 38, 38, 0.6) !important;
        }}
        
        /* 테마 전환 버튼 특별 애니메이션 */
        button[key="theme_toggle"],
        .stButton > button:contains("다크 모드"),
        .stButton > button:contains("라이트 모드"),
        .stButton > button:contains("🌙"),
        .stButton > button:contains("☀️") {{
            transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}
        
        button[key="theme_toggle"]:hover,
        .stButton > button:contains("다크 모드"):hover,
        .stButton > button:contains("라이트 모드"):hover,
        .stButton > button:contains("🌙"):hover,
        .stButton > button:contains("☀️"):hover {{
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
        }}
        
        /* 성공/오류 메시지 가독성 개선 */
        .stSuccess {{
            background-color: rgba(0, 200, 0, 0.1) !important;
        }}
        
        .stSuccess * {{
            color: #00c851 !important;
        }}
        
        .stError {{
            background-color: rgba(255, 0, 0, 0.1) !important;
        }}
        
        .stError * {{
            color: #ff4444 !important;
        }}
        
        .stWarning {{
            background-color: rgba(255, 193, 7, 0.1) !important;
        }}
        
        .stWarning * {{
            color: #ffbb33 !important;
        }}
        
        .stInfo {{
            background-color: rgba(0, 123, 255, 0.1) !important;
        }}
        
        .stInfo * {{
            color: #007bff !important;
        }}
        
        /* 채팅 입력창 - 매우 강력한 선택자 */
        input[type="text"],
        textarea,
        .stChatInputContainer input,
        .stChatInput input,
        [data-testid="stChatInputContainer"] input,
        [data-testid="chatInput"] input,
        .stApp [data-testid="stChatInputContainer"] input,
        .stApp .stChatInputContainer input,
        div[data-testid="stChatInputContainer"] input,
        section[data-testid="main"] input[type="text"],
        .main input[type="text"],
        .stChatInput textarea,
        .stChatInputContainer textarea {{
            background-color: {secondary_bg} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
            border-radius: 4px !important;
        }}
        
        /* 채팅 입력창 placeholder */
        input[type="text"]::placeholder,
        textarea::placeholder,
        .stChatInputContainer input::placeholder,
        .stChatInput input::placeholder,
        [data-testid="stChatInputContainer"] input::placeholder {{
            color: #888888 !important;
            opacity: 0.7 !important;
        }}
        
        /* 채팅 입력창 컨테이너 배경 - 매우 강력하게 */
        .stChatInputContainer,
        [data-testid="stChatInputContainer"],
        .stChatInput,
        div[data-testid="stChatInputContainer"],
        .stApp .stChatInputContainer,
        section[data-testid="main"] div[data-testid="stChatInputContainer"] {{
            background-color: {bg_color} !important;
        }}
        
        /* 테마별 조건부 스타일 추가 */
    </style>
    """ + (f"""
    <style>
        /* 라이트 모드 전용 강제 스타일 - 브라우저 다크모드 무시 */
        * {{
            color-scheme: light !important;
        }}
        html, body {{
            background: #ffffff !important;
            color: #262730 !important;
            color-scheme: light !important;
        }}
        .stApp, body, html {{
            background: #ffffff !important;
            color: #262730 !important;
        }}
        [data-testid="stSidebar"] {{
            background: #f0f2f6 !important;
        }}
        
        /* 채팅 입력창 강력한 라이트모드 적용 */
        input, textarea, 
        .stApp input, .stApp textarea,
        [data-testid="stChatInputContainer"] input,
        [data-testid="stChatInputContainer"] textarea,
        .stChatInputContainer input,
        .stChatInputContainer textarea,
        .stChatInput input,
        .stChatInput textarea {{
            background: #f8f9fa !important;
            color: #212529 !important;
            border: 2px solid #dee2e6 !important;
            border-radius: 8px !important;
        }}
        
        [data-testid="stChatInputContainer"] {{
            background: #ffffff !important;
        }}
        
        .main .block-container {{
            background: #ffffff !important;
            color: #262730 !important;
        }}
        
        /* 모든 input 강제 라이트모드 */
        input:not([type="submit"]):not([type="button"]) {{
            background: #f8f9fa !important;
            color: #212529 !important;
            border: 2px solid #dee2e6 !important;
        }}
    </style>
    <script>
        // JavaScript로 강제 라이트모드 적용
        setTimeout(function() {{
            const inputs = document.querySelectorAll('input[type="text"], textarea');
            inputs.forEach(input => {{
                input.style.setProperty('background', '#f8f9fa', 'important');
                input.style.setProperty('color', '#212529', 'important');
                input.style.setProperty('border', '2px solid #dee2e6', 'important');
            }});
        }}, 100);
        
        // 동적으로 생성되는 요소들도 처리
        const observer = new MutationObserver(function(mutations) {{
            mutations.forEach(function(mutation) {{
                mutation.addedNodes.forEach(function(node) {{
                    if (node.nodeType === 1) {{
                        const inputs = node.querySelectorAll ? node.querySelectorAll('input[type="text"], textarea') : [];
                        inputs.forEach(input => {{
                            input.style.setProperty('background', '#f8f9fa', 'important');
                            input.style.setProperty('color', '#212529', 'important');
                            input.style.setProperty('border', '2px solid #dee2e6', 'important');
                        }});
                    }}
                }});
            }});
        }});
        observer.observe(document.body, {{ childList: true, subtree: true }});
    </script>
    """ if theme == "light" else f"""
    <style>
        /* 다크 모드 전용 강제 스타일 - 브라우저 라이트모드 무시 */
        html, body {{
            background: #0e1117 !important;
            color: #fafafa !important;
            color-scheme: dark !important;
        }}
        .stApp, body, html {{
            background: #0e1117 !important;
            color: #fafafa !important;
        }}
        [data-testid="stSidebar"] {{
            background: #262730 !important;
        }}
        .stApp input[type="text"],
        .stApp textarea {{
            background: #262730 !important;
            color: #fafafa !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }}
        .stApp [data-testid="stChatInputContainer"] {{
            background: #0e1117 !important;
        }}
        .main .block-container {{
            background: #0e1117 !important;
            color: #fafafa !important;
        }}
    </style>
    """)

# 🎯 다양한 도구들 정의
def create_weather_tool():
    """날씨 정보 검색 도구"""
    search = SerpAPIWrapper()
    
    def get_weather(location: str) -> str:
        try:
            results = search.results(f"{location} 날씨 오늘 섭씨 celsius temperature")
            organic = results.get("organic_results", [])
            if organic:
                weather_info = organic[0].get("snippet", "날씨 정보를 찾을 수 없습니다.")
                # 화씨를 섭씨로 변환하는 안내 포함
                return f"🌤️ {location} 날씨: {weather_info}\n\n📌 온도는 섭씨(°C) 기준으로 표시됩니다."
            return "날씨 정보를 찾을 수 없습니다."
        except Exception as e:
            return f"날씨 검색 중 오류 발생: {str(e)}"
    
    return Tool(
        name="weather_search",
        func=get_weather,
        description="특정 지역의 날씨 정보를 검색합니다. 사용법: weather_search('서울')"
    )

def create_news_tool():
    """최신 뉴스 검색 도구"""
    search = SerpAPIWrapper()
    
    def get_news(topic: str) -> str:
        try:
            results = search.results(f"{topic} 최신 뉴스")
            organic = results.get("organic_results", [])
            news_list = []
            
            for i, result in enumerate(organic[:3]):
                title = result.get("title", "제목 없음")
                snippet = result.get("snippet", "내용 없음")
                link = result.get("link", "")
                news_list.append(f"{i+1}. 📰 {title}\n   {snippet}\n   🔗 {link}")
            
            return "\n\n".join(news_list) if news_list else "뉴스를 찾을 수 없습니다."
        except Exception as e:
            return f"뉴스 검색 중 오류 발생: {str(e)}"
    
    return Tool(
        name="news_search",
        func=get_news,
        description="최신 뉴스를 검색합니다. 사용법: news_search('AI 기술')"
    )

def create_recipe_tool():
    """요리 레시피 검색 도구"""
    search = SerpAPIWrapper()
    
    def get_recipe(dish: str) -> str:
        try:
            results = search.results(f"{dish} 레시피 만들기 요리법")
            organic = results.get("organic_results", [])
            recipes = []
            
            for result in organic[:2]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if "레시피" in title or "만들기" in title:
                    recipes.append(f"🍳 {title}\n{snippet}")
            
            return "\n\n".join(recipes) if recipes else f"{dish} 레시피를 찾을 수 없습니다."
        except Exception as e:
            return f"레시피 검색 중 오류 발생: {str(e)}"
    
    return Tool(
        name="recipe_search",
        func=get_recipe,
        description="요리 레시피를 검색합니다. 사용법: recipe_search('김치찌개')"
    )

def create_stock_tool():
    """주식 정보 검색 도구"""
    search = SerpAPIWrapper()
    
    def get_stock_info(company: str) -> str:
        try:
            results = search.results(f"{company} 주식 주가 현재가")
            organic = results.get("organic_results", [])
            
            if organic:
                stock_info = organic[0].get("snippet", "주식 정보를 찾을 수 없습니다.")
                return f"📈 {company} 주식 정보: {stock_info}"
            return f"{company} 주식 정보를 찾을 수 없습니다."
        except Exception as e:
            return f"주식 정보 검색 중 오류 발생: {str(e)}"
    
    return Tool(
        name="stock_search",
        func=get_stock_info,
        description="주식 정보를 검색합니다. 사용법: stock_search('삼성전자')"
    )

def create_translation_tool():
    """번역 도구"""
    search = SerpAPIWrapper()
    
    def translate_text(text_and_lang: str) -> str:
        try:
            results = search.results(f"번역 {text_and_lang}")
            organic = results.get("organic_results", [])
            
            if organic:
                translation = organic[0].get("snippet", "번역을 찾을 수 없습니다.")
                return f"🔤 번역 결과: {translation}"
            return "번역을 찾을 수 없습니다."
        except Exception as e:
            return f"번역 중 오류 발생: {str(e)}"
    
    return Tool(
        name="translation_search",
        func=translate_text,
        description="텍스트를 번역합니다. 사용법: translation_search('안녕하세요 영어로')"
    )

def create_general_search_tool():
    """일반 검색 도구"""
    search = SerpAPIWrapper()
    
    def general_search(query: str) -> str:
        try:
            results = search.results(query)
            organic = results.get("organic_results", [])
            search_results = []
            
            for i, result in enumerate(organic[:3]):
                title = result.get("title", "제목 없음")
                snippet = result.get("snippet", "내용 없음")
                link = result.get("link", "")
                search_results.append(f"{i+1}. 🔍 {title}\n   {snippet}\n   🔗 {link}")
            
            return "\n\n".join(search_results) if search_results else "검색 결과를 찾을 수 없습니다."
        except Exception as e:
            return f"검색 중 오류 발생: {str(e)}"
    
    return Tool(
        name="general_search",
        func=general_search,
        description="일반적인 정보를 검색합니다. 다른 도구로 해결되지 않는 질문에 사용합니다."
    )

# 🤖 AI 에이전트 생성
def create_ai_agent(api_keys):
    """톡톡이 AI 에이전트 생성"""
    
    # 환경변수 설정
    os.environ['OPENAI_API_KEY'] = api_keys['openai']
    os.environ['SERPAPI_API_KEY'] = api_keys['serpapi']
    
    # 도구들 생성
    tools = [
        create_weather_tool(),
        create_news_tool(),
        create_recipe_tool(),
        create_stock_tool(),
        create_translation_tool(),
        create_general_search_tool()
    ]
    
    # LLM 설정
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000
    )
    
    # 프롬프트 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
안녕하세요! 저는 AI 비서 톡톡이입니다! 🤖✨

저는 다양한 기능을 가진 만능 AI 비서예요:

🌤️ **날씨 정보**: 전국 어디든 실시간 날씨를 섭씨(°C) 온도로 알려드려요
📰 **최신 뉴스**: 궁금한 분야의 최신 소식을 전해드려요  
🍳 **요리 레시피**: 맛있는 요리법을 찾아드려요
📈 **주식 정보**: 관심 있는 기업의 주가를 확인해드려요
🔤 **번역 서비스**: 다양한 언어로 번역해드려요
🔍 **통합 검색**: 모든 궁금한 것을 검색해드려요

**사용 팁:**
- 구체적으로 질문해주세요! (예: "서울 날씨", "김치찌개 레시피")
- 최신 정보가 필요하면 "최신", "현재", "오늘" 등을 포함해주세요
- 날씨 정보는 항상 섭씨(°C) 온도로 제공됩니다
- 여러 질문도 한번에 물어보셔도 돼요!

친근하고 도움이 되는 답변을 드릴게요! 😊
어떤 도움이 필요하신가요?
"""),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # 에이전트 생성
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=False,
        max_iterations=3,
        early_stopping_method="generate"
    )
    
    return agent_executor

# 💬 채팅 기록 관리
def get_session_history(session_id: str):
    if "session_histories" not in st.session_state:
        st.session_state.session_histories = {}
    
    if session_id not in st.session_state.session_histories:
        st.session_state.session_histories[session_id] = ChatMessageHistory()
    
    return st.session_state.session_histories[session_id]

# 🎨 메인 앱
def main():
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    
    # 현재 테마에 따른 스타일 적용 (캐시 무효화)
    import time
    cache_buster = int(time.time() * 1000)  # 밀리초 타임스탬프
    theme_css = apply_theme_styles(st.session_state.theme)
    # CSS에 고유 식별자 추가로 캐시 무효화
    theme_css = theme_css.replace('<style>', f'<style id="theme-{cache_buster}">')
    st.markdown(theme_css, unsafe_allow_html=True)
    
    # 추가 강제 테마 적용
    if st.session_state.theme == "light":
        st.markdown(f"""
        <style id="force-light-{cache_buster}">
            /* 라이트 모드 강제 적용 */
            * {{
                --primary-color: #262730 !important;
                --background-color: #ffffff !important;
                --secondary-background-color: #f0f2f6 !important;
                --text-color: #262730 !important;
            }}
            
            .stApp, [data-testid="stAppViewContainer"], body, html {{
                background: #ffffff !important;
                color: #262730 !important;
            }}
            
            [data-testid="stSidebar"] {{
                background: #f0f2f6 !important;
                color: #262730 !important;
            }}
            
            input, textarea {{
                background: #f0f2f6 !important;
                color: #262730 !important;
                border: 1px solid rgba(0,0,0,0.2) !important;
            }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <style id="force-dark-{cache_buster}">
            /* 다크 모드 강제 적용 */
            * {{
                --primary-color: #fafafa !important;
                --background-color: #0e1117 !important;
                --secondary-background-color: #262730 !important;
                --text-color: #fafafa !important;
            }}
            
            .stApp, [data-testid="stAppViewContainer"], body, html {{
                background: #0e1117 !important;
                color: #fafafa !important;
            }}
            
            [data-testid="stSidebar"] {{
                background: #262730 !important;
                color: #fafafa !important;
            }}
            
            input, textarea {{
                background: #262730 !important;
                color: #fafafa !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
            }}
        </style>
        """, unsafe_allow_html=True)
    
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI 비서 톡톡이</h1>
        <p>당신의 똑똑한 AI 친구가 되어드릴게요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 - API 키 입력
    with st.sidebar:
        # 🌙 테마 토글 버튼 (가장 위에 배치)
        current_theme = "🌙 다크 모드" if st.session_state.theme == "light" else "☀️ 라이트 모드"
        if st.button(current_theme, key="theme_toggle"):
            old_theme = st.session_state.theme
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            new_theme_name = "다크 모드" if st.session_state.theme == "dark" else "라이트 모드"
            st.rerun()
        
        st.markdown("### 🔑 API 키 설정")
        openai_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            placeholder="sk-...",
            value="sk-ABp1f2C1BWf8SkXnrEil9hP3OvsxTmnytRq4mM6Z1aT3BlbkFJiR43shY2AF75_rIKJAP4HqGY35yCJ82Ha7r-XYW1sA"
        )
        
        serpapi_key = st.text_input(
            "SerpAPI Key", 
            type="password", 
            placeholder="발급받은 SerpAPI 키",
            value="b0eceab991f4d6987f25402fa86f49f4a5f5af4d6e8b6f1e3fa101112d88c660"
        )
        
        st.markdown("---")
        
        # 현재 테마 상태 표시
        theme_status = "🌙 다크 모드" if st.session_state.theme == "dark" else "☀️ 라이트 모드"
        st.info(f"현재 테마: {theme_status}")
        
        # 도구 정보
        st.markdown("""
        ### 🛠️ 사용 가능한 기능들
        
        🌤️ **날씨 정보**  
        📰 **최신 뉴스**  
        🍳 **요리 레시피**  
        📈 **주식 정보**  
        🔤 **번역 서비스**  
        🔍 **통합 검색**
        """)
        
        st.markdown("---")
        
        # 대화 초기화 버튼
        if st.button("🗑️ 대화 기록 삭제"):
            st.session_state.messages = []
            st.session_state.session_histories = {}
            st.success("대화 기록이 삭제되었습니다!")
            st.rerun()
    
    # API 키 확인
    if not openai_key or not serpapi_key:
        st.warning("🔑 OpenAI API 키와 SerpAPI 키를 입력해주세요!")
        st.info("""
        **API 키 발급 방법:**
        - OpenAI: https://platform.openai.com/api-keys
        - SerpAPI: https://serpapi.com/
        """)
        return
    
    # AI 에이전트 생성
    try:
        api_keys = {"openai": openai_key, "serpapi": serpapi_key}
        agent_executor = create_ai_agent(api_keys)
        
        # 메모리 추가
        agent_with_history = RunnableWithMessageHistory(
            agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
    except Exception as e:
        st.error(f"AI 에이전트 생성 중 오류 발생: {str(e)}")
        return
    
    # 환영 메시지
    if not st.session_state.messages:
        welcome_msg = """
        안녕하세요! 👋 AI 비서 톡톡이입니다!
        
        저는 다음과 같은 도움을 드릴 수 있어요:
        - 🌤️ 날씨 정보 (예: "서울 날씨 알려줘")
        - 📰 최신 뉴스 (예: "AI 관련 최신 뉴스")
        - 🍳 요리 레시피 (예: "김치찌개 만드는 법")
        - 📈 주식 정보 (예: "삼성전자 주가")
        - 🔤 번역 (예: "안녕하세요를 영어로")
        - 🔍 모든 궁금한 것들!
        
        무엇을 도와드릴까요? 😊
        """
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    # 이전 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if user_input := st.chat_input("궁금한 것을 물어보세요! 💬"):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # AI 응답 생성
        with st.spinner("톡톡이가 생각중이에요... 🤔"):
            try:
                response = agent_with_history.invoke(
                    {"input": user_input},
                    config={"configurable": {"session_id": "user_session"}}
                )
                ai_response = response['output']
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                error_msg = f"죄송해요! 오류가 발생했어요: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # 메시지 추가 후 페이지 재실행
        st.rerun()

if __name__ == "__main__":
    main()