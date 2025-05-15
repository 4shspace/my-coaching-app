import streamlit as st
import google.generativeai as genai

# --- Main Application Function ---
def main():
    # --- App Title ---
    st.title("🎓 학생 성장 코칭 피드백 생성기")
    st.markdown("학생의 상황, 학습 내용, 그리고 필요시 관련 자료 파일을 업로드하여 Gemini API로부터 직접 맞춤형 코칭 질문과 피드백을 받아보세요.")
    st.markdown("---")

    # --- Session State Initialization ---
    if 'feedback_generated' not in st.session_state:
        st.session_state.feedback_generated = False
        st.session_state.api_response = ""
        st.session_state.error_message = ""

    # --- Sidebar ---
    # 배포된 앱에서는 API 키 입력 안내나 로컬 테스트 안내가 필요 없으므로 관련 문구 제거
    # st.sidebar.header("🔑 Gemini API 설정 (보안)") # 이 줄과 아래 문단들을 주석 처리하거나 삭제합니다.
    # st.sidebar.markdown("""
    # 이 앱은 Gemini API를 사용합니다. 
    # 앱이 배포된 환경에서는 Streamlit Secrets 또는 해당 플랫폼의 비밀 관리 기능을 통해 API 키가 안전하게 설정되어야 합니다.

    # **로컬 테스트 시:**
    # 만약 로컬에서 이 앱을 테스트하고 싶다면, 프로젝트 루트 디렉토리에 `.streamlit/secrets.toml` 파일을 만들고 다음과 같이 API 키를 추가하세요:
    # ```toml
    # GEMINI_API_KEY = "여기에_실제_API_키를_입력하세요"
    # ```
    # **주의:** `secrets.toml` 파일은 절대로 GitHub와 같은 공개 저장소에 올리면 안 됩니다! `.gitignore` 파일에 `.streamlit/secrets.toml`을 추가하세요.
    # """)
    # st.sidebar.markdown("`pip install google-generativeai` 라이브러리가 설치되어 있어야 합니다.")
    # st.sidebar.markdown("---")
    # st.sidebar.header("ℹ️ 사용 방법") # 이 줄과 아래 문단들을 주석 처리하거나 삭제합니다.
    # st.sidebar.markdown("""
    # 1.  **API 키 설정:**
    #     * **배포 시:** Streamlit Community Cloud 또는 사용 중인 플랫폼의 Secrets 설정에서 `GEMINI_API_KEY`라는 이름으로 API 키를 등록합니다.
    #     * **로컬 테스트 시:** 프로젝트 폴더 내에 `.streamlit/secrets.toml` 파일을 만들고 `GEMINI_API_KEY = "YOUR_API_KEY"` 형식으로 키를 저장합니다. (사이드바 상세 안내 참고)
    # 2.  메인 화면의 입력 필드([1]~[4])에 학생 관련 정보를 모두 입력합니다.
    # 3.  필요시, TXT 또는 MD 형식의 관련 자료 파일을 업로드합니다.
    # 4.  `코칭 질문 및 피드백 생성 (API 호출)` 버튼을 클릭합니다.
    # 5.  잠시 기다리면 Gemini API가 생성한 코칭 질문과 피드백이 화면 하단에 나타납니다.
    # """)
    # st.sidebar.markdown("---")
    st.sidebar.info("이 앱은 Streamlit과 Gemini API를 사용하여 제작되었습니다.") # 이 한 줄 정도는 남겨두거나, 이것도 원치 않으시면 삭제 가능합니다.


    # --- Attempt to load API key from Streamlit Secrets ---
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("⚠️ Gemini API 키가 설정되지 않았습니다. 앱 관리자에게 문의해주세요. Streamlit Community Cloud의 Secrets 설정을 확인해야 합니다.")
        st.stop()
    except FileNotFoundError: # 로컬에서 .streamlit 폴더나 secrets.toml 파일이 없을 경우 (배포 환경에서는 이 오류가 나면 안 됨)
        st.error("⚠️ 로컬 테스트 환경에서 secrets.toml 파일을 찾을 수 없습니다. 배포 환경에서는 Streamlit Cloud의 Secrets 설정을 확인해야 합니다.")
        st.stop()


    # --- Main Input Sections ---
    st.header("코칭 정보 입력")
    st.markdown("아래 각 항목에 학생의 상황과 필요한 정보를 자세히 입력해주세요.")

    col1, col2 = st.columns(2)

    with col1:
        student_situation_input = st.text_area(
            "**[1] 교수학습 상황 또는 학생의 특정 행동/결과물]**",
            height=200,
            placeholder="예시: 한 학생이 분수 덧셈 문제를 풀 때, 분모는 더하고 분자는 그대로 두는 실수를 반복적으로 합니다.",
            help="학생의 구체적인 행동, 어려움, 또는 결과물을 상세히 작성해주세요."
        )
        student_info_input = st.text_input(
            "**[2] 대상 학생 정보]**",
            placeholder="예시: 대한민국 초등학교 5학년",
            help="피드백 대상 학생의 학년, 연령 등 관련 정보를 입력합니다."
        )

    with col2:
        learning_context_input = st.text_area(
            "**[3] 현재 학습 내용 및 어려움]**",
            height=200,
            placeholder="예시: 분수의 덧셈과 뺄셈 단원을 학습 중이며, 특히 통분 개념을 어려워합니다.",
            help="학생이 현재 배우고 있는 내용과 특별히 어려워하는 부분을 설명해주세요."
        )
        feedback_goal_input = st.text_input(
            "**[4] 피드백 목표]**",
            placeholder="예시: 통분 과정을 정확히 이해하고 적용하도록 돕는 것",
            help="이번 코칭과 피드백을 통해 학생이 무엇을 성취하길 바라는지 명확히 기술합니다."
        )

    st.markdown("---")

    # --- File Upload Section ---
    st.subheader("📎 지도안 또는 관련 자료 파일 업로드 (선택 사항)")
    uploaded_file = st.file_uploader(
        "**TXT 또는 MD 형식의 파일을 업로드해주세요.**",
        type=['txt', 'md'],
        help="지도안, 학생 활동지, 수업 자료 등 텍스트 기반 파일을 업로드할 수 있습니다. 파일 내용은 코칭 생성 시 함께 고려됩니다."
    )
    st.caption("참고: DOCX, PDF, HWP 등의 파일은 현재 앱에서 직접 내용을 읽을 수 없는 형식입니다. 필요한 경우, 해당 파일의 주요 내용을 복사하여 위 텍스트 입력란에 추가해주세요.")
    st.markdown("---")

    # --- Generate Coaching Button & Logic ---
    if st.button("🚀 코칭 질문 및 피드백 생성 (API 호출)", type="primary", use_container_width=True):
        st.session_state.feedback_generated = False
        st.session_state.api_response = ""
        st.session_state.error_message = ""

        if not api_key:
            st.error("⚠️ Gemini API 키를 사용할 수 없습니다. 앱 설정을 확인해주세요.")
        elif not student_situation_input or not student_info_input or not learning_context_input or not feedback_goal_input:
            st.error("⚠️ 모든 필수 입력 필드([1]~[4])를 채워주세요!")
        else:
            with st.spinner("Gemini API로부터 코칭 질문과 피드백을 생성 중입니다... 잠시만 기다려주세요."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

                    file_content_for_prompt = ""
                    if uploaded_file is not None:
                        try:
                            if uploaded_file.type == "text/plain" or uploaded_file.name.endswith(".md"):
                                file_content_for_prompt = uploaded_file.read().decode("utf-8")
                                st.info(f"'{uploaded_file.name}' 파일 내용이 프롬프트에 포함됩니다.")
                            else:
                                file_content_for_prompt = f"업로드된 파일명: {uploaded_file.name} (내용 직접 분석 미지원 형식으로 파일명만 참조)"
                        except Exception as e:
                            st.warning(f"파일 '{uploaded_file.name}'을(를) 읽는 중 오류 발생: {e}")
                            file_content_for_prompt = f"파일 '{uploaded_file.name}' 읽기 오류 발생."

                    prompt_to_gemini = f"""
                    당신은 학생들의 학습 잠재력을 최대한 이끌어내는 데 초점을 맞추는 숙련된 교수 설계자이자 학생 성장 코치 역할을 해주세요. 학생들의 강점을 격려하고 개선 영역을 건설적으로 안내하는 데 능숙합니다.

                    다음 정보를 바탕으로 학생에게 제공할 수 있는 구체적이고 실행 가능한 **코칭 질문**과 **피드백**을 각각 구분하여 생성해주세요.
                    피드백은 학생의 현재 수준을 진단하고, 다음 학습 단계로 나아갈 수 있도록 동기를 부여하며, 구체적인 개선 전략을 포함해야 합니다.
                    생성되는 코칭 질문과 피드백은 긍정적 강화, 교정적 지도, 심층적 사고 유도 등 다양한 유형을 포함해야 합니다.

                    **형식:**
                    - **'코칭 질문'** 섹션과 **'피드백'** 섹션으로 명확히 나누어 제시해주세요.
                    - 각 섹션 내에서는 불렛 리스트(글머리 기호)를 사용하고, 각 항목은 2-3문장 이내의 간결한 형태로 작성해주세요.
                    - '피드백' 섹션 내에서는 필요시, 긍정적 피드백, 개선을 위한 피드백 등으로 소제목을 달아 분류해주세요. '코칭 질문' 섹션은 학생의 사고를 자극하고 이해를 돕는 질문 중심으로 구성해주세요.

                    **어조:**
                    - 학생을 존중하고 지지하는 따뜻하고 친근한 어조를 사용해주세요.
                    - 학생이 자신의 성장을 주도적으로 인식하고 노력할 수 있도록 격려하는 말투를 사용해주세요.
                    - 비판적이거나 단정적인 표현은 지양해주세요.

                    **학생 관련 정보:**
                    - **대상 학생:** {student_info_input}
                    - **교수학습 상황 또는 학생의 특정 행동/결과물:** {student_situation_input}
                    - **현재 학습 내용 및 어려움:** {learning_context_input}
                    - **업로드된 지도안/자료 내용:** {file_content_for_prompt if file_content_for_prompt else '제공되지 않음'}
                    - **피드백 목표:** {feedback_goal_input}
                    - **요구사항:** 학생에게 즉각적으로 적용 가능하고 이해하기 쉬운 수준으로 설명해주세요.

                    이제 위 정보를 바탕으로 명확히 구분된 코칭 질문과 피드백을 생성해주세요.
                    """

                    response = model.generate_content(prompt_to_gemini)
                    st.session_state.api_response = response.text
                    st.session_state.feedback_generated = True

                except Exception as e:
                    st.session_state.error_message = f"API 호출 중 오류 발생: {str(e)}"
                    st.error(st.session_state.error_message)
                    if "API key not valid" in str(e) or "API_KEY_INVALID" in str(e):
                         st.warning("API 키가 유효하지 않은 것 같습니다. 앱 설정을 다시 확인해주세요.")
                    elif "quota" in str(e).lower():
                        st.warning("API 할당량(quota)을 초과했을 수 있습니다. API 사용량을 확인해주세요.")
                    elif "API_KEY_UNSPECIFIED" in str(e) or "provide an API key" in str(e).lower():
                        st.warning("Gemini API 키가 genai.configure에 전달되지 않았습니다. Secrets 설정을 확인해주세요.")


    # --- Display API Response or Error ---
    if st.session_state.feedback_generated and st.session_state.api_response:
        st.markdown("---")
        st.header("💡 Gemini API 생성 코칭 질문 및 피드백")
        st.markdown(st.session_state.api_response)
    elif st.session_state.error_message and not st.session_state.api_response :
        st.markdown("---")
        st.header("🚫 오류 발생")
        st.error(st.session_state.error_message)

# --- Script Entry Point ---
if __name__ == "__main__":
    st.set_page_config(page_title="학생 성장 코칭 피드백 생성기", layout="wide")
    main()
