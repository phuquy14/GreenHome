import streamlit as st
import google.generativeai as genai
from PIL import Image

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
    initial_sidebar_state="collapsed" # Thu gọn menu cho thoáng
)

# --- 2. BỘ NÃO "CHUYÊN GIA TẬP TRUNG" (STRICT MODE) ---
[cite_start]# [cite: 32-54]
system_instruction = """
VAI TRÒ: Bạn là GreenHome 🌱 - Chuyên gia Kỹ thuật về Năng lượng & Net Zero.
GIỚI HẠN: CHỈ trả lời về: Điện năng, Hóa đơn, Thiết bị điện, CO2, Môi trường.

QUY TẮC XỬ LÝ:
1. ✅ DỮ LIỆU ĐIỆN (Ảnh/Số liệu):
   - Phân tích hóa đơn, trích xuất số kWh/Tiền.
   - Tính CO2 (0.72 kg/kWh).
   - So sánh mức tiêu thụ và đưa ra giải pháp kỹ thuật.

2. 🚫 CÂU HỎI NGOÀI LỀ (Tình cảm, Toán, Văn...):
   - TỪ CHỐI LỊCH SỰ: "Xin lỗi, tôi là trợ lý năng lượng. Vui lòng nhập số liệu điện năng để tôi hỗ trợ."

KHÔNG ĐƯỢC: Kể chuyện cười, làm thơ, tư vấn tâm lý.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# --- 3. CSS "BIẾN HÌNH" (NÚT (+) THÔNG MINH) ---
st.markdown("""
<style>
    /* Nền tối */
    .stApp {background-color: #131314; color: #E3E3E3;}
    header, footer, #MainMenu {visibility: hidden;}
    
    /* Thanh chat */
    .stChatInputContainer {
        padding-bottom: 20px; padding-top: 10px;
        background-color: #131314; z-index: 1000;
    }
    .stChatInputContainer textarea {
        background-color: #1E1F20; color: white; 
        border-radius: 25px; border: 1px solid #444746;
    }

    /* --- CẤU HÌNH VỊ TRÍ NÚT (+) --- */
    
    /* 💻 MÁY TÍNH (> 600px): Nằm góc dưới bên trái */
    @media (min-width: 600px) {
        [data-testid="stPopover"] {
            position: fixed;
            bottom: 80px; 
            left: 20px; 
            z-index: 9999;
        }
    }

    /* 📱 ĐIỆN THOẠI (< 600px): Bay lên góc trên bên phải */
    /* Để tránh bị bàn phím ảo che mất khi gõ */
    @media (max-width: 600px) {
        [data-testid="stPopover"] {
            position: fixed;
            top: 60px;      
            right: 15px;    
            z-index: 9999;
        }
    }

    /* Giao diện nút đẹp */
    [data-testid="stPopover"] button {
        border-radius: 50%; width: 50px; height: 50px; 
        border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
        font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
    [data-testid="stPopover"] button:hover {
        background-color: #2E7D32; color: white; border-color: #2E7D32;
    }

    /* Bảng số liệu */
    table {width: 100%; border-collapse: collapse; color: #E3E3E3;}
    th {background-color: #2E7D32; color: white;}
    td {border-bottom: 1px solid #444;}
</style>
""", unsafe_allow_html=True)

# --- 4. KHỞI TẠO LỜI CHÀO ---
if "messages" not in st.session_state:
    [cite_start]# [cite: 58-65]
    welcome_msg = """👋 Chào bạn. Tôi là **GreenHome** - Chuyên gia Năng lượng.

Tôi chỉ tập trung giải quyết:
1. 📊 **Phân tích hóa đơn điện** (Tính CO2, đánh giá mức tiêu thụ).
2. 💡 **Tư vấn giải pháp kỹ thuật** giảm lãng phí điện.

Vui lòng **Gửi ảnh hóa đơn** (Nút +) hoặc **Nhập số liệu** để bắt đầu."""
    
    st.session_state.messages = [{"role": "model", "content": welcome_msg}]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. NÚT UPLOAD (NỔI) ---
with st.popover("➕", use_container_width=False):
    st.markdown("### 📸 Gửi ảnh hóa đơn")
    uploaded_file = st.file_uploader(
        "", type=["jpg", "png"], 
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    if uploaded_file:
        st.success(f"Đã chọn: {uploaded_file.name}")
        st.info("👇 Nhập câu hỏi hoặc bấm gửi bên dưới")

# --- 7. THANH CHAT ---
if prompt := st.chat_input("Nhập số liệu điện năng..."):
    # User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file: st.image(Image.open(uploaded_file), width=200)

    # Bot
    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            chat = model.start_chat(history=[]) # Không dùng lịch sử dài để tránh lan man
            
            if uploaded_file:
                # Prompt ÉP BUỘC phân tích chuyên sâu
                sys_msg = prompt + "\n\n[YÊU CẦU]: Phân tích kỹ thuật ảnh này: Trích xuất số liệu -> Tính CO2 (0.72) -> So sánh chuẩn -> Giải pháp. Không nói chuyện phiếm."
                response = chat.send_message([sys_msg, Image.open(uploaded_file)], stream=True)
                st.session_state.uploader_key += 1
            else:
                response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    msg_box.markdown(full_text + "▌")
            
            msg_box.markdown(full_text)
            st.session_state.messages.append({"role": "model", "content": full_text})
            
            if uploaded_file: st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")
