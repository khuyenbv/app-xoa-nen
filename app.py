import streamlit as st
from rembg import remove
from PIL import Image
import io
import time
from payos import PayOS, ItemData, PaymentData

# 1. KHAI BÁO THÔNG TIN KẾT NỐI PAYOS CỦA ANH
# (Lưu ý: Thay thế chính xác các chuỗi ký tự trong tài khoản của anh vào đây)
PAYOS_CLIENT_ID = "c45cca4a-1851-4c2d-bd02-c8d49ffb5115"
PAYOS_API_KEY = "8738d185-b3c2-4a8b-b90e-2f844fed181e"
PAYOS_CHECKSUM_KEY = "74c0218fe5596d1535cea52b8d8c51abe3a51a2a2cfaafe837fcc50f7cdbc642"

# Khởi tạo đối tượng cổng kết nối PayOS toàn cục
payos = PayOS(client_id=PAYOS_CLIENT_ID, api_key=PAYOS_API_KEY, checksum_key=PAYOS_CHECKSUM_KEY)

st.set_page_config(page_title="AI Xóa Nền - Ủng hộ Trà Đá", layout="centered")
st.title("✂️ Công cụ AI Xóa Nền Ảnh Tự Động")
st.write("Ủng hộ Admin 5.000đ (tương đương 1 cốc trà đá) để tải ảnh bóc tách nền chất lượng cao.")

# Khởi tạo các biến trạng thái lưu trữ tạm thời trong phiên làm việc (Session State)
if 'payment_success' not in st.session_state:
    st.session_state.payment_success = False
if 'order_id' not in st.session_state:
    # Hệ thống PayOS yêu cầu mã đơn hàng kiểu số nguyên Integer (tối đa 64-bit)
    st.session_state.order_id = int(time.time())
if 'checkout_url' not in st.session_state:
    st.session_state.checkout_url = None

# 2. KHU VỰC TẢI ẢNH GỐC UP LÊN MÁY CHỦ
uploaded_file = st.file_uploader("Chọn một bức ảnh từ thiết bị của bạn...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption='Ảnh gốc của bạn', use_column_width=True)
    
    # AI thực hiện xử lý tách nền và giữ file trong RAM bộ nhớ đệm
    with st.spinner('AI đang tiến hành phân tích và xóa nền...'):
        output_image = remove(input_image)
        buf = io.BytesIO()
        output_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

    st.markdown("---")

    # 3. TIẾN TRÌNH XỬ LÝ LOGIC THANH TOÁN ĐỐI SOÁT
    if not st.session_state.payment_success:
        st.warning("⚠️ Vui lòng ủng hộ 5.000đ để hiển thị nút tải ảnh không nền.")
        
        # Nhấp chuột điều hướng khởi tạo giao dịch trực tiếp lên tổng đài PayOS
        if st.button("🚀 Khởi Tạo Mã QR Chuyển Khoản (5.000đ)"):
            try:
                # Cấu trúc gói dữ liệu hóa đơn chuẩn API PayOS
                item = ItemData(name="Ủng hộ tách nền ảnh 1 lần", quantity=1, price=5000)
                payment_data = PaymentData(
                    orderCode=st.session_state.order_id,
                    amount=5000,
                    description=f"UnghoTrada {st.session_state.order_id}",
                    items=[item],
                    cancelUrl="https://www.bevietkhuyen.vn",
                    returnUrl="https://www.bevietkhuyen.vn"
                )
                
                # Thực thi gọi lệnh tạo link trực tuyến từ PayOS
                payment_link_response = payos.createPaymentLink(payment_data)
                
                # Lưu lại đường dẫn trang hóa đơn nhận diện QR
                st.session_state.checkout_url = payment_link_response.checkoutUrl
                
            except Exception as e:
                st.error(f"Lỗi hệ thống khởi tạo cổng thanh toán: {e}")

        # Nếu link thanh toán đã được tạo thành công, xuất giao diện liên kết
        if st.session_state.checkout_url:
            st.info("👉 Vui lòng nhấn vào liên kết bên dưới để quét mã QR chuyển khoản ngân hàng:")
            st.markdown(f'[**Nhấn vào đây để chuyển tới trang quét mã QR nhận diện tự động**]({st.session_state.checkout_url})')
            
        # Nút đối soát thủ công để kích hoạt trạng thái trả kết quả file ảnh cho khách
        if st.button("🔄 Tôi Đã Chuyển Khoản Thành Công - Kiểm Tra Ngay"):
            with st.spinner('Đang kết nối ngân hàng đối soát dữ liệu...'):
                try:
                    # Truy vấn thông tin thực tế của mã đơn hàng hiện tại từ PayOS
                    payment_info = payos.getPaymentLinkInformation(st.session_state.order_id)
                    
                    # Nếu trạng thái ghi nhận trên sao kê là "PAID" (Đã thanh toán)
                    if payment_info.status == "PAID":
                        st.session_state.payment_success = True
                        st.success("🎉 Giao dịch thành công! Xin chân thành cảm ơn cốc trà đá của anh/chị.")
                        st.rerun()
                    else:
                        st.error("❌ Hệ thống chưa tìm thấy giao dịch khớp thông tin. Vui lòng kiểm tra lại trạng thái app ngân hàng.")
                except Exception as e:
                    st.error("Chưa ghi nhận dòng tiền thành công hoặc đơn hàng chưa được quét thanh toán.")

    # 4. TRẢ VỀ FILE ẢNH ĐÃ TÁCH NỀN KHI NHẬN TIỀN THÀNH CÔNG
    if st.session_state.payment_success:
        st.image(output_image, caption='Ảnh kết quả sau khi xử lý xóa nền thành công', use_column_width=True)
        
        # Nút tải file mở khóa vĩnh viễn cho phiên làm việc
        st.download_button(
            label="📥 Tải Ảnh Đã Xóa Nền (Định dạng PNG HD)",
            data=byte_im,
            file_name="xoanen_bevietkhuyen.png",
            mime="image/png"
        )