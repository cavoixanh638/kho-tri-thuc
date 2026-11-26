from django.db import connection
from django.test import TestCase

from .quantities import quantity_condition, quantity_params


class QuantityEvidenceTests(TestCase):
    def supported(self, query, source):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {quantity_condition('body')} FROM (VALUES (%(body)s::text)) source(body)",
                {**quantity_params(query), "body": source},
            )
            return cursor.fetchone()[0]

    def test_prose_and_document_numbers_do_not_add_a_quantity_filter(self):
        for query in ("Mình nhớ một bến tàu", "bản in mẫu AX-124",
                      "Phụ lục 14/2023-TĐG", "tập mã 45"):
            with self.subTest(query=query):
                self.assertIsNone(quantity_params(query)["quantity_required"])
                self.assertTrue(self.supported(query, ""))

    def test_decibel_weight_is_bound_to_its_reading(self):
        body = "Lần đầu là 41 dB(A), lần sau 63 dB(C)."
        self.assertTrue(self.supported("41 dB(A)", body))
        self.assertTrue(self.supported("63 dBC", body))
        self.assertFalse(self.supported("41 dB(C)", body))
        self.assertFalse(self.supported("1 dB(A)", body))
        self.assertFalse(self.supported("41 dBC", "Mức tham chiếu 41 dBc."))

    def test_values_keep_their_labels_in_either_query_order(self):
        body = "Ngang: 92 mm, chiều cao là 56 mm."
        self.assertTrue(self.supported("rộng 92 mm cao 56 mm", body))
        self.assertTrue(self.supported("cao 56 mm ngang 92 mm", body))
        self.assertFalse(self.supported("ngang 56 mm cao 92 mm", body))
        self.assertTrue(self.supported("đặt chốt sau 92 mm", "Đi được 92 mm mới đặt chốt."))
        for body in ("Bản vẽ 92×56 mm", "BẢN VẼ 92 mm x 56 mm"):
            with self.subTest(body=body):
                self.assertTrue(self.supported("rộng 92 mm cao 56 mm", body))
                self.assertFalse(self.supported("rộng 56 mm cao 92 mm", body))

    def test_a_size_cannot_use_one_axis_from_each_object(self):
        query = "bệ rộng 88 mm cao 51 mm"
        for separator in (". ", ", ", " và "):
            body = "Bệ thứ nhất rộng 88 mm, cao 12 mm" + separator + "bệ kia rộng 34 mm, cao 51 mm."
            with self.subTest(separator=separator):
                self.assertFalse(self.supported(query, body))
                self.assertTrue(self.supported("bệ rộng 34 mm cao 51 mm", body))
        self.assertTrue(self.supported(query, "Bệ rộng 88 mm. Chiều cao 51 mm."))

    def test_the_sign_and_whole_decimal_bind_to_the_unit(self):
        body = "Mốc đầu −3,5 cm, mốc sau +5 cm."
        self.assertTrue(self.supported("-3,5 cm", body))
        self.assertTrue(self.supported("+5 cm", body))
        self.assertFalse(self.supported("+3,5 cm", body))
        self.assertFalse(self.supported("5 cm", "Đã chốt 123,5 cm."))
        self.assertFalse(self.supported("3 kg", "Cân thử 3 g rồi đổi quả cân 4 kg."))
        self.assertTrue(self.supported("chốt 15 mm", "Bu-lông 15-mm ở góc."))
        self.assertIsNone(quantity_params("tốc độ 32 m/s")["quantity_required"])
        self.assertFalse(self.supported("độ dài 32 m", "Số đo 32 m/s."))

    def test_a_date_belongs_to_its_local_activity(self):
        body = "Bàn tiếp nhận gửi gói hàng ngày 2026-05-12; bàn lưu trữ hủy phiếu ngày 2026-05-13."
        self.assertTrue(self.supported("gửi gói hàng 2026-05-12", body))
        self.assertTrue(self.supported("hủy phiếu ngày 2026-05-13", body))
        self.assertFalse(self.supported("gửi gói hàng 2026-05-13", body))
        self.assertFalse(self.supported("hủy phiếu ngày 2026-05-12", body))
        self.assertTrue(self.supported("2026-05-13", body))
        self.assertTrue(self.supported("từ 2026-05-12 đến 2026-05-13", body))

    def test_bit_and_byte_rates_follow_their_local_instrument(self):
        body = "Bộ thu có tốc độ 19 Mb/s, còn ổ rời có tốc độ 19 MB/s."
        self.assertTrue(self.supported("Bộ thu 19 Mbps", body))
        self.assertTrue(self.supported("ổ rời 19 MB/s", body))
        self.assertFalse(self.supported("Bộ thu 19 MB/s", body))
        self.assertFalse(self.supported("ổ rời 19 Mb/s", body))
        self.assertFalse(self.supported("19 MB/s", "Nguồn phát ghi 19 Mb/s."))
        self.assertTrue(self.supported("19 MB/s", body))
        paired = "Đầu phát 31 MB/s và đĩa quay 31 Mb/s."
        self.assertTrue(self.supported("đầu phát 31 MB / s", paired))
        self.assertFalse(self.supported("đĩa quay 31 MB/s", paired))

    def test_an_unrecorded_rate_does_not_borrow_a_rate_from_another_instrument(self):
        body = "Tốc độ máy in chưa ghi. Tốc độ máy quét là 76 MB/s."
        self.assertFalse(self.supported("tốc độ máy in 76 MB/s", body))
        self.assertTrue(self.supported("tốc độ máy quét 76 MB/s", body))
        self.assertTrue(self.supported("tốc độ phòng tối 76 MB/s", "Phòng tối. Tốc độ đo được 76 MB/s."))
