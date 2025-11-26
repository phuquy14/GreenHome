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
    page_title="GreenHome",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. BỘ NÃO THÔNG MINH (ĐÃ CẬP NHẬT THEO YÊU CẦU MỚI) ---
system_instruction = """
VAI TRÒ: Bạn là GreenHome 🌱 - Chuyên gia Kỹ thuật về Năng lượng & Net Zero.

QUY TẮC XỬ LÝ (QUAN TRỌNG):

1. ✅ KHI NHẬN SỐ TIỀN/SỐ ĐIỆN (VD: "500k", "300 số"):
   - Tự quy đổi ra kWh (Giá TB ~2.500đ/kWh).
   - Tính CO2 (0.72 kg CO2/kWh).
   - Đưa ra 3 lời khuyên ngắn gọn ban đầu.

2. ✅ KHI NHẬN CÂU HỎI "TƯ VẤN CỤ THỂ/CHI TIẾT HƠN":
   - Đây là lúc người dùng cần hành động thực tế.
   - Bạn phải liệt kê các bước thực hiện chi tiết (Step-by-step).
   - BẮT BUỘC phải ước tính con số cụ thể: "Nếu làm việc này, bạn giảm được khoảng X tiền và Y kg CO2 mỗi tháng".

3. ✅ KHI NHẬN ẢNH HÓA ĐƠN:
   - Trích xuất số liệu -> Tính CO2 -> Đánh giá.

4. 🚫 CÂU HỎI NGOÀI LỀ:
   - Từ chối lịch sự, lái về chủ đề điện năng.

PHONG CÁCH: Thân thiện, luôn sẵn sàng giải thích sâu hơn nếu người dùng hỏi lại.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# --- 3. CSS GIAO DIỆN ---
st.markdown("""
<style>
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
    @media (min-width: 600px) { [data-testid="stPopover"] { position: fixed; bottom: 80px; left: 20px; z-index: 9999; } }
    @media (max-width: 600px) { [data-testid="stPopover"] { position: fixed; top: 60px; right: 15px; z-index: 9999; } }

    /* Nút (+) đẹp */
    [data-testid="stPopover"] button {
        border-radius: 50%; width: 50px; height: 50px; 
        border: 1px solid #4CAF50; background-color: #1E1F20; color: #4CAF50;
        font-size: 24px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
    
    /* Nút Gửi ngay trong menu */
    div[data-testid="stPopoverBody"] button {
        width: 100%; border-radius: 10px; background-color: #2E7D32; color: white; border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ AI (CÓ LỊCH SỬ ĐỂ HỎI TIẾP) ---
def handle_response(user_input, image=None):
    # Thêm tin nhắn user vào lịch sử
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
        if image: st.image(image, width=200)

    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            # Gửi TOÀN BỘ lịch sử chat cũ để AI hiểu ngữ cảnh (để trả lời câu hỏi follow-up)
            history_gemini = []
            for msg in st.session_state.messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=history_gemini)
            
            if image:
                # Nếu có ảnh, gửi ảnh kèm prompt phân tích
                prompt = user_input + "\n\n[YÊU CẦU]: Phân tích ảnh này. Trích xuất số liệu -> Tính CO2 -> Khuyên."
                response = chat.send_message([prompt, image], stream=True)
                st.session_state.uploader_key += 1
            else:
                # Nếu chỉ có text (hỏi tiếp hoặc nhập số tiền)
                response = chat.send_message(user_input, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    msg_box.markdown(full_text + "▌")
            
            msg_box.markdown(full_text)
            st.session_state.messages.append({"role": "model", "content": full_text})
            
            if image: st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 5. KHỞI TẠO & LỜI CHÀO HƯỚNG DẪN ---
if "messages" not in st.session_state:
    # Cập nhật lời chào hướng dẫn chi tiết cho người mới 
    welcome_msg = """👋 Xin chào! Mình là **GreenHome** 🌱.

💡 **Hướng dẫn người mới:**
1. Để gửi hóa đơn: Hãy bấm vào **dấu cộng (+)** ở góc màn hình và chọn ảnh.
2. Để tính nhanh: Nhập số tiền (VD: *500k*), số điện (VD: *200kWh*) vào ô chat bên dưới.

"""
    st.session_state.messages = [{"role": "model", "content": welcome_msg}]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. NÚT UPLOAD (CÓ NÚT GỬI NGAY) ---
with st.popover("➕", use_container_width=False):
    st.markdown("### 📸 Gửi ảnh hóa đơn")
    st.caption("Bấm vào bên dưới để tải ảnh lên 👇")
    uploaded_file = st.file_uploader(
        "", type=["jpg", "png"], 
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    
    # Nút bấm gửi luôn không cần gõ phím
    if uploaded_file:
        if st.button("🚀 Phân tích ngay"):
            handle_response("Hãy phân tích hóa đơn này giúp tôi.", Image.open(uploaded_file))

# --- 8. THANH CHAT (HỖ TRỢ HỎI TIẾP) ---
if prompt := st.chat_input("Nhập số tiền (vd: 500k) hoặc câu hỏi..."):
    # Nếu đang treo ảnh trong nút (+) mà lại gõ phím -> Gửi cả ảnh và chữ
    if uploaded_file:
        handle_response(prompt, Image.open(uploaded_file))
    else:
        # Chat bình thường (Hỏi tiếp, nhập số tiền...)
        handle_response(prompt)
