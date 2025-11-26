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
    initial_sidebar_state="collapsed"
)

# --- 2. BỘ NÃO CHUYÊN GIA (ĐÃ SỬA LỖI HIỂU SỐ TIỀN) ---
system_instruction = """
VAI TRÒ: Bạn là GreenHome 🌱 - Chuyên gia Kỹ thuật về Năng lượng & Net Zero.
NHIỆM VỤ: Chỉ tập trung phân tích điện năng, CO2 và đưa ra giải pháp tiết kiệm.

QUY TẮC XỬ LÝ QUAN TRỌNG (STRICT MODE):

1. ✅ KHI NGƯỜI DÙNG NHẬP SỐ HOẶC TIỀN (VD: "500k", "1 triệu", "300", "200 số"):
   - [TỰ ĐỘNG HIỂU]: Đây là dữ liệu điện năng.
   - [XỬ LÝ]: 
     + Nếu là Tiền (VNĐ): Hãy chia cho 2.500đ để ước tính ra số kWh.
     + Nếu là Số (kWh): Dùng trực tiếp.
   - [PHÂN TÍCH]: Tính CO2 (0.72 kg/kWh) -> So sánh mức tiêu thụ -> Đưa ra giải pháp.
   
2. ✅ KHI NHẬN ẢNH HÓA ĐƠN:
   - Trích xuất số liệu chính xác -> Tính CO2 -> Đánh giá & Khuyên.

3. 🚫 KHI GẶP CÂU HỎI KHÔNG LIÊN QUAN (Tình cảm, Thơ ca, Code, Chính trị...):
   - TỪ CHỐI LỊCH SỰ: "Xin lỗi, tôi chỉ hỗ trợ tính toán điện năng và giải pháp tiết kiệm điện. Vui lòng nhập số liệu để tôi phân tích."

KHÔNG ĐƯỢC: Kể chuyện cười, tán gẫu, làm thơ. Hãy tập trung vào số liệu.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# --- 3. CSS GIAO DIỆN (NÚT BAY) ---
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

    /* VỊ TRÍ NÚT (+) */
    /* Máy tính: Góc dưới trái */
    @media (min-width: 600px) {
        [data-testid="stPopover"] { position: fixed; bottom: 80px; left: 20px; z-index: 9999; }
    }
    /* Điện thoại: Góc trên phải */
    @media (max-width: 600px) {
        [data-testid="stPopover"] { position: fixed; top: 60px; right: 15px; z-index: 9999; }
    }

    /* Giao diện nút */
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
    welcome_msg = """👋 Chào bạn. Tôi là **GreenHome** - Chuyên gia Năng lượng.

Tôi chỉ tập trung giải quyết:
1. 📊 **Phân tích hóa đơn điện** (Tính CO2, đánh giá mức tiêu thụ).
2. 💡 **Tư vấn giải pháp kỹ thuật** giảm lãng phí điện.

Vui lòng **Gửi ảnh hóa đơn** (Nút +) hoặc **Nhập số tiền (VD: 500k)** để bắt đầu."""
    
    st.session_state.messages = [{"role": "model", "content": welcome_msg}]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. NÚT UPLOAD ---
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
if prompt := st.chat_input("Nhập số tiền (vd: 500k) hoặc số điện..."):
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
            chat = model.start_chat(history=[])
            
            if uploaded_file:
                # Prompt cho ảnh
                sys_msg = prompt + "\n\n[YÊU CẦU]: Phân tích kỹ thuật ảnh này: Trích xuất số liệu -> Tính CO2 (0.72) -> So sánh chuẩn -> Giải pháp."
                response = chat.send_message([sys_msg, Image.open(uploaded_file)], stream=True)
                st.session_state.uploader_key += 1
            else:
                # Prompt cho văn bản (Bot tự hiểu số tiền nhờ System Instruction ở trên)
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
