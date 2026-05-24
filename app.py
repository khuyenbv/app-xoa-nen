import streamlit as st
from rembg import remove
from PIL import Image
import io
import requests
import time

# Cấu hình thông tin kết nối PayOS của anh (Lấy từ màn hình anh đã tạo thành công)
PAYOS_CLIENT_ID = "c45cca4a-1851-4c2d-bd02-c8d49ffb5115"
PAYOS_API_KEY = "8738d185-b3c2-4a8b-b90e-2f844fed181e"
PAYOS_CHECKSUM_KEY = "74c0218fe5596d1535cea52b8d8c51abe3a51a2a2cfaafe837fcc50f7cdbc642"

st.set_page_config(page_title="AI Xóa Nền - Ủng hộ Trà Đá", layout="centered")
st.title("✂️ Công cụ AI Xóa Nền Ảnh Tự Động")
st.write("Ủng hộ Admin 5.000đ (tương đương 1 cốc trà đá) để tải ảnh chất lượng cao không nền.")

# 1. Ô cho người dùng tải ảnh lên
uploaded_file = st.file_uploader("Chọn một bức ảnh từ máy tính...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption='Ảnh gốc của bạn', use_column_width=True)
    
    # Tạo biến trạng thái trong bộ nhớ Streamlit để kiểm tra thanh toán
    if 'payment_success' not in st.session_state:
        st.session_state.payment_success = False
    if 'order_id' not in st.session_state:
        st.session_state.order_id = str(int(time.time())) # Tạo mã đơn hàng duy nhất bằng timestamp

    # 2. Xử lý xóa nền bằng AI (Chạy ngầm sẵn)
    with st.spinner('AI đang bóc tách nền...'):
        output_image = remove(input_image)
        buf = io.BytesIO()
        output_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

    # 3. Tiến trình kiểm tra thanh toán
    if not st.session_state.payment_success:
        st.warning("⚠️ Vui lòng ủng hộ 5.000đ để mở khóa tính năng tải ảnh.")
        
        # Nút tạo mã QR thanh toán qua PayOS
        if st.button("🚀 Tạo Mã QR Chuyển Khoản (5.000đ)"):
            # Gọi API của PayOS để tạo link thanh toán cố định cho đơn hàng này
            # (Phần này anh dùng thư viện payos của Python hoặc gọi requests trực tiếp)
            payload = {
                "orderCode": int(st.session_state.order_id),
                "amount": 5000,
                "description": f"Ung ho tra da {st.session_state.order_id}",
                "cancelUrl": "https://www.bevietkhuyen.vn",
                "returnUrl": "https://www.bevietkhuyen.vn"
            }
            
            # Giả định gửi lên PayOS và nhận về Link thanh toán chứa mã QR
            # Thực tế anh sẽ dùng: payos.create_payment_link(payload)
            st.info("👉 Bạn hãy quét mã QR hiển thị trên màn hình để thanh toán.")
            # Hiển thị khung nhúng thanh toán của PayOS tại đây
            
        # Nút để người dùng bấm kiểm tra sau khi chuyển khoản xong
        if st.button("🔄 Tôi Đã Chuyển Khoản - Kiểm Tra Ngay"):
            with st.spinner('Đang đối soát ngân hàng tự động...'):
                # Gọi API PayOS kiểm tra trạng thái đơn hàng (get_payment_link_information)
                # Nếu trạng thái trả về là "PAID" (Đã thanh toán) -> kích hoạt:
                # st.session_state.payment_success = True
                
                # Bản DEMO chạy thử nghiệm (Giả định thành công để test luồng):
                st.session_state.payment_success = True
                st.rerun()

    # 4. Khi đã thanh toán thành công -> Mở khóa nút Tải file
    if st.session_state.payment_success:
        st.success("🎉 Cảm ơn anh/chị đã ủng hộ cốc trà đá cho Admin! Ảnh của bạn đã sẵn sàng.")
        st.image(output_image, caption='Ảnh đã xóa nền', use_column_width=True)
        
        st.download_button(
            label="📥 Tải Ảnh Đã Xóa Nền (Định dạng PNG HD)",
            data=byte_im,
            file_name="xoanen_bevietkhuyen.png",
            mime="image/png"
        )