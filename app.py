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
    initial_sidebar_state="expanded"
)

# --- 2. HỆ THỐNG QUẢN LÝ DỮ LIỆU ĐA PHIÊN ---
if not os.path.exists("user_data"):
    os.makedirs("user_data")

def get_user_file(username):
    safe_name = "".join(x for x in username if x.isalnum())
    return f"user_data/{safe_name}_sessions.json"

def load_all_sessions(username):
    """Tải toàn bộ danh sách các cuộc trò chuyện"""
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {} # Trả về dict rỗng nếu chưa có gì

def save_all_sessions(username, sessions_data):
    """Lưu lại toàn bộ"""
    file_path = get_user_file(username)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sessions_data, f, ensure_ascii=False, indent=4)

# --- 3. BỘ NÃO AI ---
system_instruction = """
VAI TRÒ: GreenHome 🌱 - Chuyên gia Năng lượng.
QUY TẮC:
1. NHẬN TIỀN/SỐ: Quy đổi -> Tính CO2 (0.72) -> Lời khuyên.
2. NHẬN ẢNH: Phân tích hóa đơn -> Trích xuất -> Đánh giá.
3. NGOÀI LỀ: Từ chối lịch sự.
"""
model = genai.GenerativeModel(model_name="gemini-2.0-flash", system_instruction=system_instruction)

# --- 4. CSS GIAO DIỆN (CHỈNH SIDEBAR GIỐNG CHATGPT) ---
st.markdown("""
<style>
    .stApp {background-color: #131314; color: #E3E3E3;}
    header, footer, #MainMenu {visibility: hidden;}
    .stChatInputContainer textarea {background-color: #1E1F20; color: white; border-radius: 25px; border: 1px solid #444746;}
    
    /* Sidebar màu tối */
    [data-testid="stSidebar"] {background-color: #171719; border-right: 1px solid #333;}
    
    /* Nút chọn lịch sử chat */
    .stButton button {
        width: 100%;
        text-align: left;
        border: 1px solid #333;
        background-color: #1E1F20;
        color: #E3E3E3;
        margin-bottom: 5px;
        border-radius: 8px;
    }
    .stButton button:hover {
        background-color: #2E2E2E;
        border-color: #4CAF50;
    }
    
    /* Nút New Chat nổi bật */
    div[data-testid="stSidebarUserContent"] .stButton:first-child button {
        background-color: #2E7D32; 
        color: white; 
        border: none;
        text-align: center;
        font-weight: bold;
    }

    /* Nút (+) Nổi cho PC */
    @media (min-width: 600px) { [data-testid="stPopover"] { position: fixed; bottom: 80px; left: 20px; z-index: 9999; } }
    @media (max-width: 600px) { [data-testid="stPopover"] { position: fixed; top: 60px; right: 15px; z-index: 9999; } }
    
    [data-testid="stPopover"] button {
        border-radius: 50%; width: 50px; height: 50px; 
        border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
        font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- 5. QUẢN LÝ SESSION STATE ---
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "user_sessions" not in st.session_state:
    st.session_state.user_sessions = {}
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 6. HÀM TẠO MỚI & XỬ LÝ CHAT ---
def create_new_session():
    """Tạo một phiên chat mới tinh"""
    new_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Tạo cấu trúc session mới
    st.session_state.user_sessions[new_id] = {
        "title": "Đoạn chat mới...", # Tiêu đề tạm
        "created_at": timestamp,
        "messages": [{"role": "model", "content": "👋 Chào bạn! Gửi hóa đơn hoặc số tiền để mình tính toán nhé!"}]
    }
    st.session_state.active_session_id = new_id
    # Lưu lại ngay
    save_all_sessions(st.session_state.current_user, st.session_state.user_sessions)

def handle_response(user_input, image=None):
    session_id = st.session_state.active_session_id
    current_chat = st.session_state.user_sessions[session_id]
    
    # 1. Cập nhật tiêu đề nếu đây là tin nhắn đầu tiên của User
    # (Để giống ChatGPT: Lấy câu đầu làm tiêu đề)
    if len(current_chat["messages"]) <= 1:
        # Lấy 30 ký tự đầu làm tiêu đề
        new_title = user_input[:30] + "..." if len(user_input) > 30 else user_input
        current_chat["title"] = new_title

    # 2. Thêm tin nhắn User
    current_chat["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        if image: st.image(image, width=200)

    # 3. Bot trả lời
    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            # Tạo lịch sử cho AI đọc (chỉ lấy nội dung chat, bỏ meta data)
            history_gemini = []
            for msg in current_chat["messages"][:-1]: # Trừ câu vừa gửi
                role = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=history_gemini)
            
            if image:
                prompt = user_input + "\n\n[YÊU CẦU]: Phân tích ảnh chuẩn GreenHome. Trích xuất -> Tính CO2 -> Khuyên."
                response = chat.send_message([prompt, image], stream=True)
                st.session_state.uploader_key += 1
            else:
                response = chat.send_message(user_input, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    msg_box.markdown(full_text + "▌")
            
            msg_box.markdown(full_text)
            
            # 4. Lưu tin nhắn Bot
            current_chat["messages"].append({"role": "model", "content": full_text})
            
            # 5. Ghi xuống file ngay lập tức
            save_all_sessions(st.session_state.current_user, st.session_state.user_sessions)
            
            if image: st.rerun()
            
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 7. GIAO DIỆN CHÍNH ---

if st.session_state.current_user is None:
    # --- MÀN HÌNH ĐĂNG NHẬP ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #81C995;'>🌱 GreenHome Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("Nhập tên định danh:", placeholder="Ví dụ: TuanDev")
        if st.button("🚀 Truy cập"):
            if username_input.strip():
                user = username_input.strip()
                st.session_state.current_user = user
                
                # Tải toàn bộ lịch sử các phiên chat
                sessions = load_all_sessions(user)
                st.session_state.user_sessions = sessions
                
                # Nếu chưa có phiên nào, tạo mới
                if not sessions:
                    create_new_session()
                else:
                    # Mặc định mở phiên gần nhất (key cuối cùng)
                    st.session_state.active_session_id = list(sessions.keys())[-1]
                
                st.rerun()

else:
    # --- GIAO DIỆN CHAT (ĐÃ ĐĂNG NHẬP) ---
    
    # A. SIDEBAR: DANH SÁCH LỊCH SỬ
    with st.sidebar:
        st.write(f"👤 **{st.session_state.current_user}**")
        
        # 1. Nút Tạo mới
        if st.button("➕ Cuộc trò chuyện mới"):
            create_new_session()
            st.rerun()
        
        st.markdown("---")
        st.caption("Gần đây")
        
        # 2. Danh sách các đoạn chat cũ (Đảo ngược để cái mới nhất lên đầu)
        # Sắp xếp theo thời gian (nếu cần), ở đây dict thường giữ thứ tự insert
        session_ids = list(st.session_state.user_sessions.keys())[::-1]
        
        for sess_id in session_ids:
            sess_data = st.session_state.user_sessions[sess_id]
            title = sess_data.get("title", "Không tiêu đề")
            
            # Highlight nút đang chọn
            if sess_id == st.session_state.active_session_id:
                # Dùng markdown để bôi đậm nút đang chọn (vì st.button ko chỉnh màu đc)
                st.markdown(f"👉 **{title}**")
            else:
                if st.button(title, key=sess_id):
                    st.session_state.active_session_id = sess_id
                    st.rerun()
        
        st.divider()
        if st.button("Đăng xuất"):
            st.session_state.current_user = None
            st.rerun()

    # B. KHUNG CHAT CHÍNH
    st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)
    
    # Lấy tin nhắn của phiên hiện tại
    if st.session_state.active_session_id in st.session_state.user_sessions:
        current_messages = st.session_state.user_sessions[st.session_state.active_session_id]["messages"]
        
        for message in current_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    else:
        st.error("Không tìm thấy đoạn chat này.")

    # C. CÔNG CỤ NHẬP LIỆU
    # Nút Upload Ảnh (Floating)
    with st.popover("➕", use_container_width=False):
        uploaded_file = st.file_uploader("", type=["jpg", "png"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        if uploaded_file:
            if st.button("🚀 Phân tích ngay"):
                handle_response("Hãy phân tích ảnh này.", Image.open(uploaded_file))

    # Thanh Chat
    if prompt := st.chat_input("Nhập tin nhắn..."):
        if uploaded_file:
            handle_response(prompt, Image.open(uploaded_file))
        else:
            handle_response(prompt)
