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

# 스타일링 - 다크/라이트 모드 호환
st.markdown("""
<style>
    /* 메인 헤더 스타일 */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white !important;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9) !important;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
    }
    
    /* 사이드바 텍스트 색상 고정 */
    .css-1d391kg, .css-1d391kg p, .css-1d391kg div {
        color: #262730 !important;
    }
    
    /* 다크모드 사이드바 텍스트 */
    [data-testid="stSidebar"] * {
        color: #fafafa !important;
    }
    
    [data-testid="stSidebar"] .markdown-text-container {
        color: #fafafa !important;
    }
    
    /* 채팅 메시지 스타일 */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 라이트 모드 텍스트 */
    .stApp {
        color: #262730;
    }
    
    /* 다크 모드 텍스트 */
    .stApp[data-theme="dark"] {
        color: #fafafa;
    }
    
    /* 입력창 스타일 */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: inherit;
        border: 1px solid rgba(0, 0, 0, 0.2);
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background-color: #667eea;
        color: white;
        border: none;
        border-radius: 5px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #764ba2;
        transform: translateY(-2px);
    }
    
    /* 성공/오류 메시지 가독성 개선 */
    .stSuccess {
        background-color: rgba(0, 200, 0, 0.1) !important;
        color: #00c851 !important;
    }
    
    .stError {
        background-color: rgba(255, 0, 0, 0.1) !important;
        color: #ff4444 !important;
    }
    
    .stWarning {
        background-color: rgba(255, 193, 7, 0.1) !important;
        color: #ffbb33 !important;
    }
    
    .stInfo {
        background-color: rgba(0, 123, 255, 0.1) !important;
        color: #007bff !important;
    }
</style>
""", unsafe_allow_html=True)

# 🎯 다양한 도구들 정의
def create_weather_tool():
    """날씨 정보 검색 도구"""
    search = SerpAPIWrapper()
    
    def get_weather(location: str) -> str:
        try:
            results = search.results(f"{location} 날씨 오늘")
            organic = results.get("organic_results", [])
            if organic:
                weather_info = organic[0].get("snippet", "날씨 정보를 찾을 수 없습니다.")
                return f"🌤️ {location} 날씨: {weather_info}"
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

🌤️ **날씨 정보**: 전국 어디든 실시간 날씨를 알려드려요
📰 **최신 뉴스**: 궁금한 분야의 최신 소식을 전해드려요  
🍳 **요리 레시피**: 맛있는 요리법을 찾아드려요
📈 **주식 정보**: 관심 있는 기업의 주가를 확인해드려요
🔤 **번역 서비스**: 다양한 언어로 번역해드려요
🔍 **통합 검색**: 모든 궁금한 것을 검색해드려요

**사용 팁:**
- 구체적으로 질문해주세요! (예: "서울 날씨", "김치찌개 레시피")
- 최신 정보가 필요하면 "최신", "현재", "오늘" 등을 포함해주세요
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
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI 비서 톡톡이</h1>
        <p>당신의 똑똑한 AI 친구가 되어드릴게요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 사이드바 - API 키 입력
    with st.sidebar:
        st.markdown("### 🔑 API 키 설정")
        
        openai_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            placeholder="sk-..."
        )
        
        serpapi_key = st.text_input(
            "SerpAPI Key", 
            type="password", 
            placeholder="발급받은 SerpAPI 키"
        )
        
        st.markdown("---")
        
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
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("톡톡이가 생각중이에요... 🤔"):
                try:
                    response = agent_with_history.invoke(
                        {"input": user_input},
                        config={"configurable": {"session_id": "user_session"}}
                    )
                    ai_response = response['output']
                    
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = f"죄송해요! 오류가 발생했어요: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()