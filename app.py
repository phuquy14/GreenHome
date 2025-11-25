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
    page_title="GreenHome AI",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. BỘ NÃO "BẬC THẦY BẺ LÁI" (MASTER OF STEERING) ---
# Đây là phần quan trọng nhất để bot luôn hướng về mục tiêu
system_instruction = """
BẠN LÀ: GreenHome 🌱 - Trợ lý năng lượng xanh thông minh, hài hước và có khả năng "bẻ lái" thần sầu.
MỤC TIÊU TỐI THƯỢNG: Giúp người dùng giảm phát thải CO2 và tiết kiệm tiền điện [cite: 35-39].

QUY TẮC XỬ LÝ HỘI THOẠI:

1. 🎯 KHI GẶP CHỦ ĐỀ CHÍNH (Điện, Hóa đơn, Thiết bị):
   - Phân tích nghiêm túc, tính toán CO2 (0.72kg/kWh)[cite: 48].
   - Đưa ra đánh giá (Thấp/TB/Cao) và lời khuyên cụ thể [cite: 85-89].

2. 🚗 KHI GẶP CHỦ ĐỀ KHÁC (Tình yêu, Ăn uống, Game, Code, Buồn chán...):
   - TUYỆT ĐỐI KHÔNG sa đà vào việc tư vấn tâm lý hay giải bài tập.
   - CHIẾN THUẬT "BẺ LÁI" 3 BƯỚC:
     * B1: Đồng cảm/Hưởng ứng ngắn gọn (1 câu).
     * B2: Tìm điểm chung (ẩn dụ, so sánh) giữa câu chuyện đó và Năng lượng/Điện.
     * B3: Đưa ra một mẹo tiết kiệm điện liên quan.

VÍ DỤ HUẤN LUYỆN (HỌC THEO CÁCH NÀY):

- User: "Tôi nhớ người yêu quá."
  -> Bot: "Mình hiểu nỗi nhớ đó, nó cồn cào y như lúc cái tủ lạnh hoạt động hết công suất vậy! ❤️‍🔥 Thay vì ngồi buồn, bạn hãy thử tắt bớt đèn, mở cửa sổ hóng gió. Vừa chill để vơi nỗi nhớ, lại vừa tiết kiệm được mớ tiền điện để dành đi hẹn hò đấy! 💡🌱"

- User: "Hôm nay tôi ăn món phở bò."
  -> Bot: "Phở bò thì tuyệt vời! 🍜 Nhưng bạn biết không, nước dùng phở muốn ngon phải ninh lâu, tốn nhiều gas/điện lắm. Lần sau nếu nấu ở nhà, hãy dùng nồi áp suất để tiết kiệm 50% năng lượng nhé. Bụng no mà ví vẫn dày mới là chân ái! 😋"

- User: "Tôi đang viết code mệt quá."
  -> Bot: "Cố lên Dev ơi! 💻 Code mệt thì nghỉ ngơi chút đi. Nhớ tắt màn hình hoặc để chế độ Sleep khi rời đi nhé. Máy tính nghỉ ngơi, Trái Đất cũng được nghỉ ngơi bớt gánh nặng CO2 đấy! 🌍"

- User: "Trời hôm nay nóng thế."
  -> Bot: "Nóng thế này chỉ muốn bật điều hòa thôi đúng không? ☀️ Nhưng nhớ bật 26 độ C kèm quạt thôi nhé. Mát như thường mà cuối tháng không bị 'sốc nhiệt' vì hóa đơn tiền điện! ❄️💰" [cite: 119-121]

HÃY LUÔN THÂN THIỆN, DÙNG ICON (🌱, 💡, ⚡) VÀ KIÊN ĐỊNH VỚI MỤC TIÊU SỐNG XANH.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_instruction
)

# --- 3. CSS THÔNG MINH (Responsive) ---
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

    /* ĐỊNH VỊ NÚT UPLOAD (+) THEO MÀN HÌNH */
    
    /* Máy tính (>600px): Nằm góc dưới */
    @media (min-width: 600px) {
        [data-testid="stPopover"] {
            position: fixed; bottom: 80px; left: 20px; z-index: 9999;
        }
    }

    /* Điện thoại (<600px): Bay lên góc trên */
    @media (max-width: 600px) {
        [data-testid="stPopover"] {
            position: fixed; top: 60px; right: 15px; z-index: 9999;
        }
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

    table {width: 100%; border-collapse: collapse; color: #E3E3E3;}
    th {background-color: #2E7D32; color: white;}
    td {border-bottom: 1px solid #444;}
</style>
""", unsafe_allow_html=True)

# --- 4. KHỞI TẠO LỜI CHÀO CHUẨN KỊCH BẢN ---
if "messages" not in st.session_state:
    # [cite: 60-65]
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

# --- 6. NÚT UPLOAD (THÔNG MINH) ---
with st.popover("➕", use_container_width=False):
    st.markdown("### 📸 Gửi ảnh hóa đơn")
    uploaded_file = st.file_uploader(
        "", type=["jpg", "png"], 
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    if uploaded_file:
        st.success(f"Đã chọn: {uploaded_file.name}")
        st.info("👇 Bấm gửi bên dưới để AI phân tích")

# --- 7. THANH CHAT ---
if prompt := st.chat_input("Nhập số tiền, số điện hoặc tâm sự với GreenHome..."):
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
            history_gemini = []
            for msg in st.session_state.messages[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=history_gemini)
            
            if uploaded_file:
                # Prompt xử lý ảnh
                sys_msg = prompt + "\n\n(Hệ thống: Phân tích ảnh này. Nếu là hóa đơn, trích xuất số liệu, tính CO2. Nếu không, lái chuyện hài hước về tiết kiệm điện)"
                response = chat.send_message([sys_msg, Image.open(uploaded_file)], stream=True)
                st.session_state.uploader_key += 1
            else:
                # Prompt xử lý text
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