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

# --- 2. BỘ NÃO CHUYÊN GIA (AN TOÀN & RIÊNG TƯ) ---
system_instruction = """
VAI TRÒ: GreenHome 🌱 - Chuyên gia Kỹ thuật Năng lượng.
NHIỆM VỤ: Phân tích điện năng, CO2, Giải pháp tiết kiệm.

QUY TẮC:
1. NHẬN TIỀN/SỐ: Tự quy đổi -> Tính CO2 (0.72) -> Lời khuyên.
2. NHẬN ẢNH: Phân tích hóa đơn -> Trích xuất -> Đánh giá.
3. NGOÀI LỀ: Từ chối lịch sự.
"""
model = genai.GenerativeModel(model_name="gemini-2.0-flash", system_instruction=system_instruction)

# --- 3. CSS GIAO DIỆN (NÚT BAY) ---
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
    [data-testid="stPopover"] button:hover {background-color: #2E7D32; color: white; border-color: #2E7D32;}
    
    /* Nút download ở sidebar */
    .stDownloadButton button {width: 100%; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# --- 4. KHỞI TẠO DỮ LIỆU (SESSION STATE - RIÊNG TƯ) ---
if "messages" not in st.session_state:
    # Dữ liệu này chỉ tồn tại trong trình duyệt của người đang xem
    welcome_msg = """👋 Chào bạn. Tôi là **GreenHome**.

Tôi giúp bạn:
1. 📸 **Phân tích ảnh hóa đơn** (Bấm dấu +).
2. 💰 **Quy đổi tiền điện** ra CO2 và tư vấn tiết kiệm.

*Lưu ý: Cuộc trò chuyện này là riêng tư và sẽ mất khi bạn tắt trình duyệt.*"""
    st.session_state.messages = [{"role": "model", "content": welcome_msg}]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 5. HÀM XỬ LÝ AI ---
def handle_response(user_input, image=None):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        if image: st.image(image, width=200)

    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            chat = model.start_chat(history=[])
            if image:
                prompt = user_input + "\n\n[YÊU CẦU]: Phân tích ảnh này chuẩn GreenHome. Trích xuất -> Tính CO2 -> Khuyên."
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
            
            if image: st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 6. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome Expert</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. MENU TẢI XUỐNG (AN TOÀN) ---
with st.sidebar:
    st.title("⚙️ Cài đặt")
    st.caption("Dữ liệu chỉ lưu tạm thời trên máy bạn.")
    
    # Tạo nội dung file text ngay lập tức từ bộ nhớ hiện tại
    chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    
    st.download_button(
        label="📥 Tải cuộc trò chuyện về máy",
        data=chat_text,
        file_name="greenhome_history.txt",
        mime="text/plain"
    )
    
    if st.button("🗑️ Xóa hội thoại"):
        st.session_state.messages = []
        st.rerun()

# --- 8. NÚT UPLOAD ẢNH (NỔI) ---
with st.popover("➕", use_container_width=False):
    st.markdown("### 📸 Gửi ảnh hóa đơn")
    uploaded_file = st.file_uploader("", type=["jpg", "png"], key=f"uploader_{st.session_state.uploader_key}", label_visibility="collapsed")
    if uploaded_file:
        if st.button("🚀 Phân tích ngay"):
            handle_response("Hãy phân tích hóa đơn này.", Image.open(uploaded_file))

# --- 9. THANH CHAT ---
if prompt := st.chat_input("Nhập số tiền (vd: 500k) hoặc số điện..."):
    if uploaded_file:
        handle_response(prompt, Image.open(uploaded_file))
    else:
        handle_response(prompt)
