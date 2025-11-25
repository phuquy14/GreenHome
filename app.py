import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. CẤU HÌNH API (CHUẨN CHO WEB) ---
try:
    # Lấy key từ "Két sắt" khi chạy trên mạng
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # 👇 DÁN API KEY CỦA BẠN VÀO DÒNG DƯỚI ĐỂ CHẠY TRÊN MÁY TÍNH 👇
    api_key = ""

genai.configure(api_key=api_key)

st.set_page_config(
    page_title="GreenHome AI",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. BỘ NÃO GREENHOME (THEO TÀI LIỆU SYSTEM PROMPT) ---
system_instruction = """
BẠN LÀ: GreenHome 🌱 - Trợ lý năng lượng xanh thân thiện.
MỤC TIÊU: Giúp giảm phát thải CO2 và tiết kiệm chi phí điện năng[cite: 4].

QUY TẮC TRẢ LỜI:
1. LUÔN QUY ĐỔI CO2: Dùng hệ số 0.72kg CO2/kWh. So sánh trực quan (ví dụ: tương đương lái xe X km, hoặc Y cây xanh)[cite: 17, 18].
2. ĐÁNH GIÁ MỨC ĐỘ:
   - < 150 kWh: Thấp (Khen ngợi)[cite: 55].
   - 150-300 kWh: Trung bình[cite: 56].
   - 300-500 kWh: Hơi cao[cite: 57].
   - > 500 kWh: Cao (Cảnh báo)[cite: 58].
3. LỜI KHUYÊN: Đưa ra 3 hành động cụ thể (Điều hòa, Tủ lạnh, Đèn LED...) kèm ước tính tiền tiết kiệm[cite: 60, 63].

CHẾ ĐỘ LÁI CHUYỆN (Smart Steering):
- Nếu người dùng hỏi chuyện ngoài lề (tình cảm, vui chơi...): Hãy đồng cảm ngắn gọn, sau đó dùng sự hài hước để lái về chủ đề tiết kiệm năng lượng.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# --- 3. GIAO DIỆN DARK MODE ---
st.markdown("""
<style>
    .stApp {background-color: #131314; color: #E3E3E3;}
    header, footer, #MainMenu {visibility: hidden;}
    .stChatInputContainer textarea {background-color: #1E1F20; color: white; border-radius: 25px; border: 1px solid #444746;}
    [data-testid="stPopover"] button {border-radius: 50%; width: 40px; height: 40px; border: 1px solid #444746; background-color: #1E1F20; color: #A8C7FA;}
    table {width: 100%; border-collapse: collapse; color: #E3E3E3;}
    th {background-color: #2E7D32; color: white;}
    td {border-bottom: 1px solid #444;}
</style>
""", unsafe_allow_html=True)

# --- 4. KHỞI TẠO LỜI CHÀO (ĐÃ SỬA LỖI) ---
if "messages" not in st.session_state:
    # Nội dung chào chuẩn theo kịch bản [cite: 29-34]
    welcome_msg = """Xin chào! Mình là **GreenHome** 🌱 - trợ lý năng lượng xanh của bạn!
    
Hãy gửi cho mình ảnh hóa đơn tiền điện 📸 hoặc nhập số điện tiêu thụ, mình sẽ giúp bạn:

* 📊 **Tính lượng CO2 phát thải**
* 💰 **Ước tính chi phí & Tiết kiệm**
* 🌍 **Đưa ra lời khuyên cụ thể**

Sẵn sàng chưa nào? 😊"""
    
    st.session_state.messages = [
        {"role": "model", "content": welcome_msg}
    ]

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 5. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #81C995;'>🌱 GreenHome</h3>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. XỬ LÝ NHẬP LIỆU ---
input_container = st.container()
with input_container:
    col1, col2 = st.columns([1, 10])
    with col1:
        with st.popover("➕"):
            uploaded_file = st.file_uploader("Chọn ảnh", type=["jpg", "png"], key=f"uploader_{st.session_state.uploader_key}")
    with col2:
        if uploaded_file: st.caption(f"✅ Đã chọn: {uploaded_file.name}")

if prompt := st.chat_input("Nhắn tin cho GreenHome..."):
    # 1. User gửi tin
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file: st.image(Image.open(uploaded_file), width=200)

    # 2. Bot trả lời
    with st.chat_message("model"):
        msg_box = st.empty()
        full_text = ""
        try:
            history_gemini = []
            for msg in st.session_state.messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=history_gemini)
            
            if uploaded_file:
                # Prompt kích hoạt quy trình phân tích chuẩn [cite: 41-53]
                img_prompt = prompt + "\n\n(Hệ thống: Hãy phân tích hóa đơn này. Trích xuất số kWh, tính CO2, đánh giá mức độ (Thấp/TB/Cao) và đưa ra 3 lời khuyên tiết kiệm cụ thể theo chuẩn GreenHome)"
                response = chat.send_message([img_prompt, Image.open(uploaded_file)], stream=True)
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