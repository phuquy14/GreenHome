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
    initial_sidebar_state="expanded" # Mở menu để đăng nhập
)

# --- 2. HỆ THỐNG QUẢN LÝ USER & LỊCH SỬ ---
# Tạo thư mục chứa lịch sử nếu chưa có
if not os.path.exists("user_data"):
    os.makedirs("user_data")

def get_user_file(username):
    # Tạo tên file an toàn (bỏ ký tự đặc biệt)
    safe_name = "".join(x for x in username if x.isalnum())
    return f"user_data/history_{safe_name}.json"

def load_user_history(username):
    """Tải lịch sử của user cụ thể"""
    file_path = get_user_file(username)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None # Chưa có lịch sử

def save_user_history(username, messages):
    """Lưu lịch sử cho user"""
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

    /* Nút (+) đẹp */
    [data-testid="stPopover"] button {
        border-radius: 50%; width: 50px; height: 50px; 
        border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
        font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
    
    /* Giao diện Login ở Sidebar */
    [data-testid="stSidebar"] {background-color: #1E1F20; border-right: 1px solid #333;}
</style>
""", unsafe_allow_html=True)

# --- 5. QUẢN LÝ ĐĂNG NHẬP (SESSION STATE) ---
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 6. THANH SIDEBAR (ĐĂNG NHẬP & LỊCH SỬ) ---
with st.sidebar:
    st.title("👤 Tài khoản")
    
    if st.session_state.current_user is None:
        # Giao diện chưa đăng nhập
        st.info("Nhập tên để lưu giữ cuộc trò chuyện của riêng bạn.")
        username_input = st.text_input("Tên của bạn (hoặc Mã số)", placeholder="Ví dụ: Tuan123")
        
        if st.button("🚀 Vào Chat ngay"):
            if username_input.strip():
                st.session_state.current_user = username_input.strip()
                # Tải lịch sử cũ nếu có
                old_history = load_user_history(st.session_state.current_user)
                if old_history:
                    st.session_state.messages = old_history
                    st.toast(f"Chào mừng trở lại, {st.session_state.current_user}! Đã tải lại lịch sử cũ.", icon="🎉")
                else:
                    # Người dùng mới -> Tạo lời chào
                    welcome_msg = f"""👋 Chào **{st.session_state.current_user}**. Tôi là GreenHome.
Tôi đã tạo một hồ sơ riêng cho bạn. Mọi tin nhắn sẽ được lưu lại tại đây! ✅

Hãy gửi **Ảnh hóa đơn** hoặc **Số tiền điện** để bắt đầu."""
                    st.session_state.messages = [{"role": "model", "content": welcome_msg}]
                st.rerun()
            else:
                st.warning("Vui lòng nhập tên!")
    else:
        # Giao diện ĐÃ đăng nhập
        st.success(f"Đang chat với tên: **{st.session_state.current_user}**")
        st.caption("Dữ liệu của bạn đang được tự động lưu ✅")
        
        if st.button("Đăng xuất / Đổi tên 🚪"):
            st.session_state.current_user = None
            st.session_state.messages = []
            st.rerun()
            
        st.divider()
        # Nút xóa lịch sử riêng của user này
        if st.button("🗑️ Xóa lịch sử của tôi"):
            st.session_state.messages = []
            save_user_history(st.session_state.current_user, []) # Ghi đè file rỗng
            st.rerun()

# --- 7. LOGIC XỬ LÝ AI ---
def handle_response(user_input, image=None):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # LƯU NGAY LẬP TỨC
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
            
            # LƯU NGAY LẬP TỨC
            if st.session_state.current_user:
                save_user_history(st.session_state.current_user, st.session_state.messages)
            
            if image: st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 8. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

# Chỉ hiện chat khi đã đăng nhập
if st.session_state.current_user:
    # Hiển thị lịch sử
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
else:
    # Màn hình chờ đăng nhập
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h2>🔐 Vui lòng đăng nhập</h2>
        <p>Nhập tên của bạn ở thanh bên trái (Sidebar) để bắt đầu trò chuyện và lưu giữ lịch sử.</p>
    </div>
    """, unsafe_allow_html=True)
