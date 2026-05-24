import streamlit as st
import io
import time
import requests

# Bọc kiểm tra nạp thư viện tiêu chuẩn để tuyệt đối không trắng trang
try:
    from PIL import Image
    from payos import PayOS
except ImportError as e:
    st.error(f"Thiếu thư viện hệ thống: {e}")
    st.stop()

# =========================================================================
# 1. KHAI BÁO THÔNG TIN BẢO MẬT CỦA ANH
# =========================================================================
# (Anh điền 3 mã PayOS của anh vào đây)
PAYOS_CLIENT_ID = "c45cca4a-1851-4c2d-bd02-c8d49ffb5115"
PAYOS_API_KEY = "8738d185-b3c2-4a8b-b90e-2f844fed181e"
PAYOS_CHECKSUM_KEY = "74c0218fe5596d1535cea52b8d8c51abe3a51a2a2cfaafe837fcc50f7cdbc642"

# API Key xóa nền miễn phí của Photoroom
PHOTOROOM_API_KEY = "sk_pr_default_003c16913203ef0e14a2d7466a06d49a4f6511e2" 

# Khởi tạo cổng kết nối PayOS an toàn
@st.cache_resource
def init_payos():
    return PayOS(client_id=PAYOS_CLIENT_ID, api_key=PAYOS_API_KEY, checksum_key=PAYOS_CHECKSUM_KEY)

try:
    payos = init_payos()
except Exception as init_err:
    st.error(f"Lỗi khởi tạo cấu hình PayOS: {init_err}")
    st.stop()

st.set_page_config(page_title="AI Xóa Nền - Ủng hộ Trà Đá", layout="centered")
st.title("✂️ Công cụ AI Xóa Nền Ảnh Tự Động")
st.write("Ủng hộ Admin 5.000đ (tương đương 1 cốc trà đá) để mở khóa tải ảnh không nền chất lượng cao.")

# Khởi tạo bộ nhớ phiên làm việc
if 'payment_success' not in st.session_state:
    st.session_state.payment_success = False
if 'order_id' not in st.session_state:
    st.session_state.order_id = int(time.time())
if 'checkout_url' not in st.session_state:
    st.session_state.checkout_url = None

# =========================================================================
# 2. KHU VỰC TẢI ẢNH GỐC LÊN
# =========================================================================
uploaded_file = st.file_uploader("Chọn một bức ảnh từ thiết bị của bạn...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Ảnh gốc của bạn', use_column_width=True)
    
    with st.spinner('AI đang bóc tách nền bằng công nghệ siêu tốc...'):
        try:
            files = {'image_file': uploaded_file.getvalue()}
            headers = {'x-api-key': PHOTOROOM_API_KEY}
            response = requests.post('https://sdk.photoroom.com/v1/segment', files=files, headers=headers)
            
            if response.status_code == 200:
                byte_im = response.content
                output_image = Image.open(io.BytesIO(byte_im))
            else:
                st.error("Cổng AI đang bận xử lý, anh bấm F5 thử lại nhé!")
                st.stop()
        except Exception as ai_err:
            st.error(f"Lỗi xử lý hình ảnh: {ai_err}")
            st.stop()

    st.markdown("---")

    # =========================================================================
    # 3. TIẾN TRÌNH XỬ LÝ LOGIC ĐỐI SOÁT THANH TOÁN
    # =========================================================================
    if not st.session_state.payment_success:
        st.warning("⚠️ Vui lòng ủng hộ 5.000đ để hiển thị nút tải ảnh không nền.")
        
        if st.button("🚀 Khởi Tạo Mã QR Chuyển Khoản (5.000đ)"):
            try:
                # 1. Định nghĩa danh sách các mặt hàng (items) đúng cấu trúc mảng
                items_list = [
                    {
                        "name": "Ủng hộ tách nền ảnh",
                        "quantity": 1,
                        "price": 5000
                    }
                ]
                
                # 2. Ép kiểu dữ liệu sang cấu trúc PaymentData bắt buộc của thư viện PayOS bản mới
                from payos import PaymentData
                payment_data = PaymentData(
                    orderCode=st.session_state.order_id,
                    amount=5000,
                    description=f"Thanh toan {st.session_state.order_id}",
                    items=items_list,
                    cancelUrl="https://www.bevietkhuyen.vn",
                    returnUrl="https://www.bevietkhuyen.vn"
                )
                
                # 3. Thực thi gọi API tạo link chính thức
                payment_link_response = payos.createPaymentLink(payment_data)
                st.session_state.checkout_url = payment_link_response.checkoutUrl
                st.success("Tạo mã QR thành công!")
            except Exception as e:
                st.error(f"Lỗi kết nối cổng PayOS: {e}")

    # =========================================================================
    # 4. TRẢ FILE KHI THANH TOÁN XONG
    # =========================================================================
    if st.session_state.payment_success:
        st.image(output_image, caption='Ảnh đã xóa nền thành công', use_column_width=True)
        st.download_button(
            label="📥 Tải Ảnh Đã Xóa Nền (Định dạng PNG HD)",
            data=byte_im,
            file_name="xoanen_bevietkhuyen.png",
            mime="image/png"
        )