import streamlit as st
import google.generativeai as genai
from PIL import Image
import random

# --- 1. CẤU HÌNH API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # XÓA KEY THẬT ĐI, ĐỂ TRỐNG NHƯ THẾ NÀY
    api_key = ""

genai.configure(api_key=api_key)

st.set_page_config(
    page_title="GreenHome AI",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. BỘ NÃO "SIÊU LÁI CHUYỆN" ---
system_instruction = """
BẠN LÀ: GreenHome 🌱 - Trợ lý ảo "cuồng" Tiết kiệm điện & Sống xanh.
MỤC TIÊU DUY NHẤT: Giúp người dùng giảm hóa đơn điện và giảm CO2.

QUY TẮC ỨNG XỬ:
1. NẾU HỎI VỀ ĐIỆN/HÓA ĐƠN:
   - [cite_start]Trả lời chuyên nghiệp, tính CO2 (0.72kg/kWh), đưa lời khuyên cụ thể[cite: 33, 34, 48].

2. NẾU HỎI CHUYỆN NGOÀI LỀ (Tình yêu, Ăn uống...):
   - Bước 1: Đồng cảm ngắn gọn.
   - Bước 2: LÁI NGAY LẬP TỨC về chủ đề tiết kiệm điện một cách hài hước.

VÍ DỤ:
- User: "Tôi nhớ người yêu."
  -> Bot: "Hiểu mà! Nhưng nhớ nhung cũng tốn năng lượng như bóng đèn sợi đốt vậy. ❤️‍🔥 Thay vì ngồi buồn, hãy tắt đèn, mở cửa sổ hóng gió trời. Vừa chill, lại vừa tiết kiệm tiền điện để dành đi hẹn hò! 💡🌱"
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

# --- 4. KHỞI TẠO (CHÀO NGẪU NHIÊN) ---
if "messages" not in st.session_state:
    greetings = [
        "Chào bạn! GreenHome đây 🌱. [cite_start]Gửi hóa đơn điện để mình tính CO2 giúp nhé! [cite: 58, 60]",
        "Hello! ⚡ Tiết kiệm điện hôm nay, xanh Trái Đất ngày mai. Bạn cần mình tư vấn gì?",
        "GreenHome xin chào! 🌍 Đừng để hóa đơn làm bạn 'đau ví'. Chụp ảnh gửi đây nào!",
        "Xin chào đồng chí 'Sống Xanh'! 👋 Hôm nay chúng ta giảm bao nhiêu số điện đây?"
    ]
    st.session_state.messages = [{"role": "model", "content": random.choice(greetings)}]

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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file: st.image(Image.open(uploaded_file), width=200)

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
                # [cite_start]Prompt ngầm xử lý ảnh theo kịch bản [cite: 66, 71]
                img_prompt = prompt + "\n\n(Hệ thống: Hãy phân tích ảnh này. Nếu là hóa đơn, trích xuất số liệu và tính CO2. Nếu khác, hãy lái câu chuyện về tiết kiệm điện)"
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