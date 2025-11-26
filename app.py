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
    initial_sidebar_state="auto"
)

# --- 2. BỘ NÃO "CHUYÊN GIA GIỚI HẠN" (STRICT FOCUS PROMPT) ---
# Đây là phần quan trọng nhất để giới hạn khả năng của bot
system_instruction = """
VAI TRÒ: Bạn là GreenHome 🌱 - Một AI Chuyên gia Kỹ thuật về Năng lượng & Net Zero.
GIỚI HẠN KHẢ NĂNG: Bạn CHỈ ĐƯỢC PHÉP xử lý thông tin liên quan đến: Điện năng, Hóa đơn, Thiết bị điện, Khí thải CO2, và Môi trường.

QUY TẮC XỬ LÝ NGHIÊM NGẶT:

1. ✅ KHI NHẬN DỮ LIỆU ĐIỆN (Ảnh/Số liệu):
   - Phải thực hiện phân tích chuyên sâu:
     + Bước 1: Xác định tổng tiêu thụ (kWh) và Tiền (VNĐ).
     + Bước 2: Tính toán khí thải CO2 (Hệ số bắt buộc: 0.72 kg CO2/kWh).
     + Bước 3: So sánh với mức chuẩn (VD: Hộ gia đình 4 người TB dùng 250kWh).
     + Bước 4: Đưa ra giải pháp kỹ thuật cụ thể (VD: Thay Ron tủ lạnh, lắp cảm biến...).

2. 🚫 KHI GẶP CÂU HỎI NGOÀI LỀ (Off-topic):
   - Nếu người dùng hỏi về: Tình cảm, Chính trị, Code, Toán học, Lịch sử, Ăn uống...
   - HÀNH ĐỘNG: Từ chối trả lời ngay lập tức.
   - MẪU CÂU TỪ CHỐI: "Xin lỗi, tôi là trợ lý chuyên biệt về Năng lượng. Tôi không có dữ liệu để trả lời câu hỏi này. Vui lòng nhập số liệu điện năng để tôi hỗ trợ."

KHÔNG ĐƯỢC:
- Không kể chuyện cười, không làm thơ, không đóng vai bác sĩ tâm lý.
- Luôn giữ thái độ Khách quan, Khoa học và Chính xác.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# --- 3. GIAO DIỆN (MOBILE SAFE) ---
st.markdown("""
<style>
    .stApp {background-color: #131314; color: #E3E3E3;}
    header, footer, #MainMenu {visibility: hidden;}
    
    /* Ô chat */
    .stChatInputContainer textarea {
        background-color: #1E1F20; color: white; 
        border-radius: 25px; border: 1px solid #444746;
    }

    /* Ẩn nút ghim trên điện thoại để tránh lỗi, chỉ hiện trên PC */
    @media (max-width: 768px) {
        [data-testid="stPopover"] { display: none; }
    }
    @media (min-width: 769px) {
        [data-testid="stPopover"] {
            position: fixed; bottom: 80px; left: 20px; z-index: 9999;
        }
        [data-testid="stPopover"] button {
            border-radius: 50%; width: 50px; height: 50px; 
            border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
            font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        }
    }
    
    /* Bảng số liệu */
    table {width: 100%; border-collapse: collapse; color: #E3E3E3;}
    th {background-color: #2E7D32; color: white;}
    td {border-bottom: 1px solid #444;}
</style>
""", unsafe_allow_html=True)

# --- 4. KHỞI TẠO ---
if "messages" not in st.session_state:
    # Lời chào chuyên nghiệp, định hướng người dùng ngay lập tức
    welcome_msg = """👋 Chào bạn. Tôi là **GreenHome** - AI Phân tích Năng lượng.

Tôi chỉ tập trung giải quyết các vấn đề sau:
1. 📊 **Phân tích hóa đơn điện** (Tính CO2, đánh giá mức tiêu thụ).
2. 💡 **Tư vấn giải pháp kỹ thuật** để giảm lãng phí điện.

Vui lòng **Gửi ảnh hóa đơn** hoặc **Nhập số liệu (kWh/VNĐ)** để bắt đầu."""
    st.session_state.messages = [{"role": "model", "content": welcome_msg}]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 5. LOGIC INPUT (Hybrid: Sidebar cho Mobile / Nút Ghim cho PC) ---
# Cách này đảm bảo không bao giờ bị lỗi giao diện
uploaded_file = None

# A. Mobile: Dùng Sidebar (Menu trái)
with st.sidebar:
    st.markdown("### 📱 Tải ảnh (Mobile)")
    file_mobile = st.file_uploader("Chọn ảnh", type=["jpg","png"], key=f"mob_{st.session_state.uploader_key}")
    if file_mobile: uploaded_file = file_mobile
    
    st.divider()
    if st.button("Xóa lịch sử chat 🗑️"):
        st.session_state.messages = []
        st.rerun()

# B. PC: Dùng Nút Ghim (Floating Button)
# CSS đã ẩn nút này trên điện thoại nên không lo bị che
with st.popover("➕", use_container_width=False):
    st.markdown("### 💻 Tải ảnh (PC)")
    file_pc = st.file_uploader("Chọn ảnh", type=["jpg","png"], key=f"pc_{st.session_state.uploader_key}")
    if file_pc: uploaded_file = file_pc

if uploaded_file:
    st.toast(f"Đã nhận dữ liệu: {uploaded_file.name}", icon="✅")

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. XỬ LÝ CHAT ---
if prompt := st.chat_input("Nhập số liệu điện năng tại đây..."):
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
            chat = model.start_chat(history=[]) # Không dùng lịch sử dài để tránh lan man, tập trung vào hiện tại
            
            if uploaded_file:
                # Prompt ÉP BUỘC phân tích chuyên sâu
                sys_msg = prompt + "\n\n[YÊU CẦU HỆ THỐNG]: Đây là dữ liệu đầu vào. Hãy phân tích kỹ thuật: Trích xuất số liệu -> Tính CO2 (0.72) -> So sánh chuẩn -> Giải pháp. Tuyệt đối không nói chuyện phiếm."
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
