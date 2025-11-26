import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os

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
    initial_sidebar_state="collapsed"
)

# --- 2. HỆ THỐNG USER ---
if not os.path.exists("user_data"):
    os.makedirs("user_data")

def get_user_file(username):
    safe_name = "".join(x for x in username if x.isalnum())
    return f"user_data/history_{safe_name}.json"

def load_user_history(username):
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_user_history(username, messages):
    file_path = get_user_file(username)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

# --- 3. BỘ NÃO CHUYÊN GIA ---
system_instruction = """
VAI TRÒ: GreenHome 🌱 - Chuyên gia Kỹ thuật Năng lượng.
QUY TẮC:
1. NHẬN TIỀN/SỐ: Tự quy đổi -> Tính CO2 (0.72) -> Lời khuyên.
2. NHẬN ẢNH: Phân tích hóa đơn -> Trích xuất -> Đánh giá.
3. NGOÀI LỀ: Từ chối lịch sự.
"""
model = genai.GenerativeModel(model_name="gemini-2.0-flash", system_instruction=system_instruction)

# --- 4. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .stApp {background-color: #131314; color: #E3E3E3;}
    header, footer, #MainMenu {visibility: hidden;}
    .stChatInputContainer textarea {background-color: #1E1F20; color: white; border-radius: 25px; border: 1px solid #444746;}
    
    /* VỊ TRÍ NÚT (+) */
    @media (min-width: 600px) { [data-testid="stPopover"] { position: fixed; bottom: 80px; left: 20px; z-index: 9999; } }
    @media (max-width: 600px) { [data-testid="stPopover"] { position: fixed; top: 60px; right: 15px; z-index: 9999; } }
    
    [data-testid="stPopover"] button {
        border-radius: 50%; width: 50px; height: 50px; 
        border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
        font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
    
    /* Nút đăng nhập đẹp */
    .stButton button {width: 100%; border-radius: 10px; background-color: #2E7D32; color: white;}
    
    /* Input đăng nhập */
    .stTextInput input {background-color: #1E1F20; color: white; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# --- 5. QUẢN LÝ SESSION ---
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 6. GIAO DIỆN CHÍNH ---

# LOGIC CHIA MÀN HÌNH: Nếu chưa đăng nhập -> Hiện Form Giữa / Nếu rồi -> Hiện Chat
if st.session_state.current_user is None:
    # --- MÀN HÌNH ĐĂNG NHẬP (CENTER) ---
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Cách dòng cho xuống giữa
    st.markdown("<h1 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Đăng nhập để lưu giữ lịch sử trò chuyện của riêng bạn.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("Tên của bạn:", placeholder="Ví dụ: Tuan123")
        if st.button("🚀 BẮT ĐẦU CHAT"):
            if username_input.strip():
                st.session_state.current_user = username_input.strip()
                # Load lịch sử
                old_history = load_user_history(st.session_state.current_user)
                if old_history:
                    st.session_state.messages = old_history
                    st.toast("Đã tải lại lịch sử cũ!", icon="🎉")
                else:
                    st.session_state.messages = [{"role": "model", "content": f"👋 Chào **{st.session_state.current_user}**. Gửi ảnh hoặc số tiền để mình tư vấn nhé!"}]
                st.rerun()
            else:
                st.warning("Vui lòng nhập tên!")

else:
    # --- MÀN HÌNH CHAT (KHI ĐÃ ĐĂNG NHẬP) ---
    
    # Sidebar chỉ dùng để Đăng xuất & Tải lịch sử
    with st.sidebar:
        st.write(f"👤 **{st.session_state.current_user}**")
        if st.button("Đăng xuất 🚪"):
            st.session_state.current_user = None
            st.rerun()
        
        st.divider()
        chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📥 Tải lịch sử chat", chat_text, "history.txt")

    # Header
    st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

    # Hiển thị chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Hàm xử lý
    def handle_response(user_input, image=None):
        st.session_state.messages.append({"role": "user", "content": user_input})
        if st.session_state.current_user:
            save_user_history(st.session_state.current_user, st.session_state.messages)

        with st.chat_message("user"):
            st.markdown(user_input)
            if image: st.image(image, width=200)

        with st.chat_message("model"):
            msg_box = st.empty()
            full_text = ""
            try:
                chat = model.start_chat(history=[])
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
                st.session_state.messages.append({"role": "model", "content": full_text})
                
                if st.session_state.current_user:
                    save_user_history(st.session_state.current_user, st.session_state.messages)
                
                if image: st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

    # Nút Upload (Nổi)
    with st.popover("➕", use_container_width=False):
        st.markdown("### 📸 Gửi ảnh hóa đơn")
        uploaded_file = st.file_uploader("", type=["jpg", "png"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
        if uploaded_file:
            if st.button("🚀 Phân tích ngay"):
                handle_response("Hãy phân tích hóa đơn này.", Image.open(uploaded_file))

    # Thanh Chat
    if prompt := st.chat_input("Nhập số tiền hoặc số điện..."):
        if uploaded_file:
            handle_response(prompt, Image.open(uploaded_file))
        else:
            handle_response(prompt)
