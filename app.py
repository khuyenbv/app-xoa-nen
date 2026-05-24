import streamlit as st
import io
import time

# Bọc kiểm tra nạp thư viện để tránh lỗi trắng trang ngầm
try:
    from rembg import remove
    from PIL import Image
    from payos import PayOS, ItemData, PaymentData
except ImportError as e:
    st.error(f"Thiếu thư viện hệ thống, anh kiểm tra lại file requirements.txt nhé. Chi tiết: {e}")
    st.stop()

# =========================================================================
# 1. KHAI BÁO THÔNG TIN KẾT NỐI PAYOS CỦA ANH
# (Anh hãy điền chính xác 3 chuỗi mã bảo mật trong tài khoản PayOS của anh vào đây)
# =========================================================================
PAYOS_CLIENT_ID = "c45cca4a-1851-4c2d-bd02-c8d49ffb5115"
PAYOS_API_KEY = "8738d185-b3c2-4a8b-b90e-2f844fed181e"
PAYOS_CHECKSUM_KEY = "74c0218fe5596d1535cea52b8d8c51abe3a51a2a2cfaafe837fcc50f7cdbc642"

# Khởi tạo cổng kết nối PayOS an toàn
@st.cache_resource
def init_payos():
    return PayOS(client_id=PAYOS_CLIENT_ID, api_key=PAYOS_API_KEY, checksum_key=PAYOS_CHECKSUM_KEY)

try:
    payos = init_payos()
except Exception as init_err:
    st.error(f"Lỗi khởi tạo cấu hình PayOS đầu trang: {init_err}")
    st.stop()

# Cấu hình giao diện ban đầu
st.set_page_config(page_title="AI Xóa Nền - Ủng hộ Trà Đá", layout="centered")
st.title("✂️ Công cụ AI Xóa Nền Ảnh Tự Động")
st.write("Ủng hộ Admin 5.000đ (tương đương 1 cốc trà đá) để mở khóa tải ảnh không nền chất lượng cao.")

# Khởi tạo bộ nhớ phiên làm việc (Session State)
if 'payment_success' not in st.session_state:
    st.session_state.payment_success = False
if 'order_id' not in st.session_state:
    st.session_state.order_id = int(time.time())
if 'checkout_url' not in st.session_state:
    st.session_state.checkout_url = None

# =========================================================================
# 2. KHU VỰC TẢI ẢNH GỐC LÊN HỆ THỐNG
# =========================================================================
uploaded_file = st.file_uploader("Chọn một bức ảnh từ thiết bị của bạn...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Đọc ảnh từ file upload
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption='Ảnh gốc của bạn', use_column_width=True)
    
    # AI xử lý tách nền ngầm
    with st.spinner('AI đang tiến hành phân tích và tách nền...'):
        try:
            output_image = remove(input_image, alpha_matting=False)
            buf = io.BytesIO()
            output_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
        except Exception as ai_error:
            st.error(f"Không thể xử lý ảnh do lỗi bộ lọc AI: {ai_error}")
            st.stop()

    st.markdown("---")

    # =========================================================================
    # 3. TIẾN TRÌNH XỬ LÝ LOGIC ĐỐI SOÁT THANH TOÁN
    # =========================================================================
    if not st.session_state.payment_success:
        st.warning("⚠️ Vui lòng ủng hộ 5.000đ để hiển thị nút tải ảnh không nền.")
        
        # Nút bấm số 1: Khởi tạo đơn hàng lên hệ thống PayOS
        if st.button("🚀 Khởi Tạo Mã QR Chuyển Khoản (5.000đ)"):
            try:
                # Khởi tạo dữ liệu đúng cấu trúc Class của SDK PayOS
                item = ItemData(name="Ủng hộ tách nền ảnh", quantity=1, price=5000)
                payment_data = PaymentData(
                    orderCode=st.session_state.order_id,
                    amount=5000,
                    description=f"Thanh toan {st.session_state.order_id}",
                    items=[item],
                    cancelUrl="https://www.bevietkhuyen.vn",
                    returnUrl="https://www.bevietkhuyen.vn"
                )
                
                # Gọi API chính thức
                payment_link_response = payos.createPaymentLink(payment_data)
                st.session_state.checkout_url = payment_link_response.checkoutUrl
                st.success("Tạo mã QR thành công! Anh bấm vào link dưới đây nhé.")
                
            except Exception as e:
                st.error(f"Lỗi kết nối cổng API PayOS: {e}")

        # Hiển thị đường link nếu đã lấy thành công từ PayOS về
        if st.session_state.checkout_url:
            st.info("👉 Anh vui lòng bấm vào đường link bên dưới để quét mã QR ngân hàng:")
            st.markdown(f'[**Bấm vào đây để mở trang quét mã QR chuyển khoản**]({st.session_state.checkout_url})')
            
        # Nút bấm số 2: Đối soát xem tài khoản ngân hàng của anh đã nhận được tiền chưa
        if st.button("🔄 Tôi Đã Chuyển Khoản Thành Công - Kiểm Tra Ngay"):
            with st.spinner('Đang kết nối ngân hàng đối soát dữ liệu sao kê...'):
                try:
                    payment_info = payos.getPaymentLinkInformation(st.session_state.order_id)
                    
                    # Kiểm tra thuộc tính status từ đối tượng trả về
                    if payment_info.status == "PAID":
                        st.session_state.payment_success = True
                        st.success("🎉 Giao dịch thành công! Xin chân thành cảm ơn sự ủng hộ của anh.")
                        st.rerun()
                    else:
                        st.error(f"❌ Trạng thái đơn hàng hiện tại: {payment_info.status}. Anh vui lòng đợi vài giây sau khi chuyển khoản rồi bấm lại nhé.")
                except Exception as e:
                    st.error(f"Hệ thống chưa tìm thấy giao dịch chuyển khoản khớp nội dung: {e}")

    # =========================================================================
    # 4. MỞ KHÓA NÚT DOWNLOAD FILE KHI ĐÃ NHẬN TIỀN
    # =========================================================================
    if st.session_state.payment_success:
        st.image(output_image, caption='Ảnh kết quả bóc tách nền trong suốt (.PNG)', use_column_width=True)
        
        st.download_button(
            label="📥 Tải Ảnh Đã Xóa Nền (Định dạng PNG HD)",
            data=byte_im,
            file_name="xoanen_bevietkhuyen.png",
            mime="image/png"
        )