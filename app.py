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

# --- 2. BỘ NÃO CHUYÊN GIA (ĐÃ CẬP NHẬT TÍNH NĂNG TỰ TÍNH TIỀN) ---
system_instruction = """
VAI TRÒ: Bạn là GreenHome 🌱 - Chuyên gia Kỹ thuật về Năng lượng & Net Zero.
NHIỆM VỤ: Phân tích điện năng, CO2 và đưa ra giải pháp tiết kiệm.

QUY TẮC XỬ LÝ (QUAN TRỌNG):

1. ✅ KHI NHẬN SỐ TIỀN (VD: "500k", "1 triệu", "200.000"):
   - [BƯỚC 1] Tự quy đổi ra kWh (Giả sử giá trung bình 2.500đ/kWh).
   - [BƯỚC 2] Tính CO2 (Hệ số: 0.72 kg CO2/kWh).
   - [BƯỚC 3] Đánh giá mức tiêu thụ (Thấp/TB/Cao).
   - [BƯỚC 4] Đưa ra 3 lời khuyên tiết kiệm cụ thể ngay lập tức.

2. ✅ KHI NHẬN ẢNH HÓA ĐƠN:
   - Trích xuất số liệu -> Tính CO2 -> Đánh giá & Khuyên.

3. 🚫 CÂU HỎI NGOÀI LỀ:
   - Từ chối lịch sự: "Xin lỗi, tôi chỉ hỗ trợ tính toán năng lượng. Vui lòng nhập số tiền hoặc gửi hóa đơn."

MẪU TRẢ LỜI KHI NHẬN TIỀN:
"💰 Với số tiền [Số tiền] (tương đương khoảng [Số kWh] kWh):
🌍 Lượng CO2 phát thải: [Số kg] kg
💡 Đánh giá: [Mức độ]
👉 Lời khuyên cho bạn:
1. ...
2. ...
3. ..."
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
    @media (min-width: 600px) {
        [data-testid="stPopover"] { position: fixed; bottom: 80px; left: 20px; z-index: 9999; }
    }
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
    
    /* Nút "Gửi ngay" trong popover */
    div[data-testid="stPopoverBody"] button {
        width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; border: none;
    }

    /* Bảng số liệu */
    table {width: 100%; border-collapse: collapse; color: #E3E3E3;}
    th {background-color: #2E7D32; color: white;}
    td {border-bottom: 1px solid #444;}
</style>
""", unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ AI (DÙNG CHUNG) ---
def handle_response(user_input, image=None):
    # Hiển thị tin nhắn user
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        if image: st.image(image, width=200)

    # Bot trả lời
    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            chat = model.start_chat(history=[])
            
            if image:
                prompt = user_input + "\n\n[YÊU CẦU]: Phân tích ảnh này theo chuẩn GreenHome. Trích xuất số liệu -> Tính CO2 -> Khuyên."
                response = chat.send_message([prompt, image], stream=True)
                st.session_state.uploader_key += 1 # Reset ảnh sau khi xử lý
            else:
                response = chat.send_message(user_input, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    msg_box.markdown(full_text + "▌")
            
            msg_box.markdown(full_text)
            st.session_state.messages.append({"role": "model", "content": full_text})
            
            # Nếu vừa xử lý ảnh xong thì reload để xóa ảnh khỏi giao diện
            if image: 
                st.rerun()
                
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 5. KHỞI TẠO ---
if "messages" not in st.session_state:
    welcome_msg = """👋 Chào bạn. Tôi là **GreenHome**.

Tôi giúp bạn:
1. 📸 **Phân tích ảnh hóa đơn** (Bấm dấu +).
2. 💰 **Quy đổi tiền điện** ra CO2 và tư vấn tiết kiệm.

Vui lòng **Gửi ảnh** hoặc **Nhập số tiền (VD: 500k)** để bắt đầu."""
    st.session_state.messages = [{"role": "model", "content": welcome_msg}]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. NÚT UPLOAD (CÓ NÚT GỬI NGAY) ---
with st.popover("➕", use_container_width=False):
    st.markdown("### 📸 Gửi ảnh hóa đơn")
    uploaded_file = st.file_uploader(
        "", type=["jpg", "png"], 
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    
    # NÚT GỬI NGAY LẬP TỨC
    if uploaded_file:
        if st.button("🚀 Phân tích ngay"):
            handle_response("Hãy phân tích hóa đơn này giúp tôi.", Image.open(uploaded_file))

# --- 8. THANH CHAT ---
if prompt := st.chat_input("Nhập số tiền (vd: 500k) hoặc số điện..."):
    # Nếu có ảnh trong popover nhưng người dùng lại gõ phím Enter
    # Thì ưu tiên xử lý ảnh kèm text
    if uploaded_file:
        handle_response(prompt, Image.open(uploaded_file))
    else:
        handle_response(prompt)
