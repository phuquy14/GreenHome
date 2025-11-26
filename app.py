import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import uuid
from datetime import datetime

# --- 1. CẤU HÌNH API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # 👇 DÁN API KEY CỦA BẠN VÀO DÒNG DƯỚI 👇
    api_key = ""

genai.configure(api_key=api_key)

st.set_page_config(
    page_title="GreenHome Expert",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="expanded" # LỆNH ÉP MỞ SIDEBAR
)

# --- 2. HỆ THỐNG DỮ LIỆU ---
if not os.path.exists("user_data"):
    os.makedirs("user_data")

def get_user_file(username):
    safe_name = "".join(x for x in username if x.isalnum())
    return f"user_data/{safe_name}_sessions.json"

def load_all_sessions(username):
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_all_sessions(username, sessions_data):
    file_path = get_user_file(username)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sessions_data, f, ensure_ascii=False, indent=4)

# --- 3. HÀM TẠO "TRÍ NHỚ DÀI HẠN" ---
def get_long_term_memory(username, sessions):
    memory_text = ""
    recent_session_ids = list(sessions.keys())[-3:] 
    if recent_session_ids:
        memory_text += f"\n[KÝ ỨC VỀ USER {username}]:\n"
        for sess_id in recent_session_ids:
            sess = sessions[sess_id]
            date = sess['created_at']
            msgs = [m for m in sess['messages'] if m['role'] in ['user', 'model']]
            if msgs:
                summary = " | ".join([f"{m['role']}: {m['content'][:100]}..." for m in msgs[-4:]])
                memory_text += f"- {date}: {summary}\n"
    return memory_text

# --- 4. CẤU HÌNH AI ---
def get_model(memory_context=""):
    base_instruction = """
    VAI TRÒ: GreenHome 🌱 - Chuyên gia Năng lượng.
    QUY TẮC:
    1. TIỀN/SỐ: Quy đổi -> Tính CO2 (0.72) -> Lời khuyên.
    2. ẢNH: Phân tích hóa đơn -> Trích xuất -> Đánh giá.
    3. NGOÀI LỀ: Từ chối lịch sự.
    4. KÝ ỨC: Dùng thông tin trong [KÝ ỨC] để trả lời nếu cần.
    """
    return genai.GenerativeModel(model_name="gemini-2.0-flash", system_instruction=base_instruction + memory_context)

# --- 5. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .stApp {background-color: #131314; color: #E3E3E3;}
    header, footer, #MainMenu {visibility: hidden;}
    .stChatInputContainer textarea {background-color: #1E1F20; color: white; border-radius: 25px; border: 1px solid #444746;}
    
    /* Sidebar luôn hiện rõ */
    [data-testid="stSidebar"] {background-color: #171719; border-right: 1px solid #333;}
    
    /* Nút chọn lịch sử */
    .stButton button {
        width: 100%; text-align: left; border: 1px solid #333;
        background-color: #1E1F20; color: #E3E3E3; margin-bottom: 5px; border-radius: 8px;
    }
    .stButton button:hover {background-color: #2E2E2E; border-color: #4CAF50;}
    
    /* Nút New Chat xanh lá */
    div[data-testid="stSidebarUserContent"] .stButton:first-child button {
        background-color: #2E7D32; color: white; border: none; text-align: center; font-weight: bold;
    }

    /* Nút (+) Nổi */
    @media (min-width: 600px) { [data-testid="stPopover"] { position: fixed; bottom: 80px; left: 20px; z-index: 9999; } }
    @media (max-width: 600px) { [data-testid="stPopover"] { position: fixed; top: 60px; right: 15px; z-index: 9999; } }
    
    [data-testid="stPopover"] button {
        border-radius: 50%; width: 50px; height: 50px; 
        border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
        font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- 6. SESSION STATE ---
if "current_user" not in st.session_state: st.session_state.current_user = None
if "active_session_id" not in st.session_state: st.session_state.active_session_id = None
if "user_sessions" not in st.session_state: st.session_state.user_sessions = {}
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "gemini_model" not in st.session_state: st.session_state.gemini_model = None 

# --- 7. HÀM TẠO MỚI (ĐÃ SỬA LỜI CHÀO CHUẨN) ---
def create_new_session():
    new_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # [cite_start]LỜI CHÀO CHUẨN ĐẸP [cite: 58-65]
    welcome_content = """👋 Chào bạn! Mình là **GreenHome** 🌱.

Hãy gửi **Ảnh hóa đơn** 📸 hoặc **Số tiền điện**, mình sẽ giúp bạn:
* 📊 **Tính lượng CO2**
* 💰 **Ước tính chi phí**
* 🌍 **Đưa ra lời khuyên**"""
    
    st.session_state.user_sessions[new_id] = {
        "title": "Cuộc trò chuyện mới...", 
        "created_at": timestamp,
        "messages": [{"role": "model", "content": welcome_content}]
    }
    st.session_state.active_session_id = new_id
    save_all_sessions(st.session_state.current_user, st.session_state.user_sessions)
    
    # Nạp ký ức
    memory_context = get_long_term_memory(st.session_state.current_user, st.session_state.user_sessions)
    st.session_state.gemini_model = get_model(memory_context)

def handle_response(user_input, image=None):
    session_id = st.session_state.active_session_id
    current_chat = st.session_state.user_sessions[session_id]
    
    # Tự đặt tiêu đề
    if len(current_chat["messages"]) <= 1:
        current_chat["title"] = (user_input[:25] + "...") if len(user_input) > 25 else user_input

    current_chat["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        if image: st.image(image, width=200)

    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            model_instance = st.session_state.gemini_model
            history_gemini = []
            for msg in current_chat["messages"][:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role, "parts": [msg["content"]]})
            
            chat = model_instance.start_chat(history=history_gemini)
            if image:
                prompt = user_input + "\n\n[YÊU CẦU]: Phân tích ảnh chuẩn GreenHome. Trích xuất -> Tính CO2 -> Khuyên."
                response = chat.send_message([prompt, image], stream=True)
                st.session_state.uploader_key += 1
            else:
                response = chat.send_message(user_input, stream=True)
            
            for chunk in response:
                if chunk.text: full_text += chunk.text; msg_box.markdown(full_text + "▌")
            
            msg_box.markdown(full_text)
            current_chat["messages"].append({"role": "model", "content": full_text})
            save_all_sessions(st.session_state.current_user, st.session_state.user_sessions)
            if image: st.rerun()
        except Exception as e: st.error(f"Lỗi: {e}")

# --- 8. GIAO DIỆN CHÍNH ---
if st.session_state.current_user is None:
    # LOGIN
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #81C995;'>🌱 GreenHome Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("Nhập tên của bạn:", placeholder="Ví dụ: TuanDev")
        if st.button("🚀 Truy cập"):
            if username_input.strip():
                user = username_input.strip()
                st.session_state.current_user = user
                st.session_state.user_sessions = load_all_sessions(user)
                create_new_session()
                st.rerun()
else:
    # MAIN APP
    
    # --- THANH BÊN (SIDEBAR) CHỨA LỊCH SỬ ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.current_user}**")
        
        # Nút tạo mới (Xanh lá)
        if st.button("➕ Cuộc trò chuyện mới"):
            create_new_session()
            st.rerun()
        
        st.caption("Gần đây")
        session_ids = list(st.session_state.user_sessions.keys())[::-1]
        
        # Danh sách lịch sử
        for sess_id in session_ids:
            sess_data = st.session_state.user_sessions[sess_id]
            title = sess_data.get("title", "No title")
            label = f"👉 {title}" if sess_id == st.session_state.active_session_id else title
            
            if st.button(label, key=sess_id):
                st.session_state.active_session_id = sess_id
                st.rerun()
        
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state.current_user = None
            st.rerun()

    # HEADER
    st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)
    
    # CHAT AREA
    if st.session_state.active_session_id:
        current_messages = st.session_state.user_sessions[st.session_state.active_session_id]["messages"]
        for message in current_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # INPUT
    with st.popover("➕", use_container_width=False):
        uploaded_file = st.file_uploader("", type=["jpg", "png"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        if uploaded_file:
            if st.button("🚀 Phân tích ngay"):
                handle_response("Hãy phân tích ảnh này.", Image.open(uploaded_file))

    if prompt := st.chat_input("Nhập tin nhắn..."):
        if uploaded_file: handle_response(prompt, Image.open(uploaded_file))
        else: handle_response(prompt)
