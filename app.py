import streamlit as st
from rembg import remove
from PIL import Image
import io
import time
from payos import PayOS, ItemData, PaymentData

# =========================================================================
# 1. KHAI BÁO THÔNG TIN KẾT NỐI PAYOS CỦA ANH
# (Anh hãy điền chính xác 3 chuỗi mã bảo mật trong tài khoản PayOS của anh vào đây)
# =========================================================================
PAYOS_CLIENT_ID = "c45cca4a-1851-4c2d-bd02-c8d49ffb5115"
PAYOS_API_KEY = "8738d185-b3c2-4a8b-b90e-2f844fed181e"
PAYOS_CHECKSUM_KEY = "74c0218fe5596d1535cea52b8d8c51abe3a51a2a2cfaafe837fcc50f7cdbc642"

# Khởi tạo đối tượng cổng kết nối toàn cục
try:
    payos = PayOS(client_id=PAYOS_CLIENT_ID, api_key=PAYOS_API_KEY, checksum_key=PAYOS_CHECKSUM_KEY)
except Exception as init_err:
    st.error(f"Cấu hình thông tin mã PayOS đầu trang chưa chính xác: {init_err}")

# Cấu hình giao diện Streamlit ban đầu
st.set_page_config(page_title="AI Xóa Nền - Ủng hộ Trà Đá", layout="centered")
st.title("✂️ Công cụ AI Xóa Nền Ảnh Tự Động")
st.write("Ủng hộ Admin 5.000đ (tương đương 1 cốc trà đá) để mở khóa tải ảnh không nền chất lượng cao.")

# Khởi tạo bộ nhớ tạm thời cho phiên làm việc (Session State) để tránh mất dữ liệu khi load lại trang
if 'payment_success' not in st.session_state:
    st.session_state.payment_success = False
if 'order_id' not in st.session_state:
    st.session_state.order_id = int(time.time()) # Mã đơn hàng kiểu số nguyên bắt buộc của PayOS
if 'checkout_url' not in st.session_state:
    st.session_state.checkout_url = None

# =========================================================================
# 2. KHU VỰC TẢI ẢNH GỐC LÊN HỆ THỐNG
# =========================================================================
uploaded_file = st.file_uploader("Chọn một bức ảnh từ thiết bị của bạn...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption='Ảnh gốc của bạn', use_column_width=True)
    
    # AI xử lý tách nền ngầm và bắt lỗi treo RAM nếu máy chủ nghẽn tải gói u2net
    with st.spinner('AI đang tiến hành phân tích và tách nền...'):
        try:
            # Tắt tính năng alpha_matting để tối ưu hóa thời gian tính toán của RAM
            output_image = remove(input_image, alpha_matting=False)
            buf = io.BytesIO()
            output_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
        except Exception as ai_error:
            st.error(f"Máy chủ AI đang tải gói dữ liệu mẫu từ xa bị chậm. Anh vui lòng nhấn F5 (Reload) thử lại sau vài giây nhé! Chi tiết: {ai_error}")
            st.stop()

    st.markdown("---")

    # =========================================================================
    # 3. TIẾN TRÌNH XỬ LÝ LOGIC ĐỐI SOÁT THANH TOÁN
    # =========================================================================
    if not st.session_state.payment_success:
        st.warning("⚠️ Vui lòng ủng hộ 5.000đ để hiển thị nút tải ảnh không nền.")
        
        # Nút bấm số 1: Gọi lệnh sang PayOS sinh mã đơn hàng và link QR định danh
        if st.button("🚀 Khởi Tạo Mã QR Chuyển Khoản (5.000đ)"):
            try:
                item = ItemData(name="Ủng hộ tách nền ảnh 1 lần", quantity=1, price=5000)
                payment_data = PaymentData(
                    orderCode=st.session_state.order_id,
                    amount=5000,
                    description=f"UnghoTrada {st.session_state.order_id}",
                    items=[item],
                    cancelUrl="https://www.bevietkhuyen.vn",
                    returnUrl="https://www.bevietkhuyen.vn"
                )
                
                # Thực thi gọi API tạo Link
                payment_link_response = payos.createPaymentLink(payment_data)
                st.session_state.checkout_url = payment_link_response.checkoutUrl
                
            except Exception as e:
                st.error(f"Lỗi khởi tạo cổng kết nối API PayOS: {e}")

        # Hiển thị đường dẫn trang thanh toán chứa mã QR nếu đã khởi tạo xong
        if st.session_state.checkout_url:
            st.info("👉 Anh vui lòng bấm vào đường link bên dưới để mở giao diện quét mã QR ngân hàng:")
            st.markdown(f'[**Bấm vào đây để quét mã QR chuyển khoản tự động**]({st.session_state.checkout_url})')
            
        # Nút bấm số 2: Kiểm tra trạng thái tài khoản ngân hàng xem tiền đã về chưa
        if st.button("🔄 Tôi Đã Chuyển Khoản Thành Công - Kiểm Tra Ngay"):
            with st.spinner('Đang kết nối ngân hàng đối soát dữ liệu sao kê...'):
                try:
                    payment_info = payos.getPaymentLinkInformation(st.session_state.order_id)
                    
                    # Nếu tổng đài PayOS xác nhận trạng thái là PAID (Đã nộp tiền thành công)
                    if payment_info.status == "PAID":
                        st.session_state.payment_success = True
                        st.success("🎉 Giao dịch thành công! Xin chân thành cảm ơn cốc trà đá ủng hộ của anh/chị.")
                        st.rerun()
                    else:
                        st.error("❌ Hệ thống chưa kiểm tra thấy dòng tiền 5.000đ khớp nội dung. Anh vui lòng đợi 3 giây rồi bấm lại nhé.")
                except Exception as e:
                    st.error("Chưa ghi nhận dòng tiền thành công hoặc phiên quét mã QR đã hết hạn.")

    # =========================================================================
    # 4. MỞ KHÓA NÚT DOWNLOAD FILE KHI ĐÃ NHẬN TIỀN
    # =========================================================================
    if st.session_state.payment_success:
        st.image(output_image, caption='Ảnh kết quả bóc tách nền trong suốt (.PNG)', use_column_width=True)
        
        # Khởi tạo nút bấm tải tệp tin HD
        st.download_button(
            label="📥 Tải Ảnh Đã Xóa Nền (Định dạng PNG HD)",
            data=byte_im,
            file_name="xoanen_bevietkhuyen.png",
            mime="image/png"
        )