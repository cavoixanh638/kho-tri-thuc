# 120 tình huống tìm kiếm tiếng Việt

Ngày 26/11/2026, 120 truy vấn mới được chạy trên cùng một kho thử gồm 122 ghi chú tự soạn trong PostgreSQL 18.4. Ba nhóm soạn đáp án trước khi chạy. Bộ đề gồm 81 câu tìm một ghi chú, 13 câu cần tìm đủ hai hoặc ba ghi chú và 26 câu yêu cầu trả rỗng. Mỗi ca có câu tìm, đáp án, lý do và kết quả ở cả hai chế độ. [Bản đã khóa đáp án](https://github.com/cavoixanh638/kho-tri-thuc/tree/ae4a6aa8a3dc5ce1ab8f15c0c036182f2798cdad/evals/vietnamese-journeys/scenario-matrix) · [Kết quả gốc trên Windows](results-windows.json)

| Nhóm | Số ca | Đạt ở lượt đầu | Đạt khi dùng thêm **Tìm gần đúng** |
| --- | ---: | ---: | ---: |
| [Nhớ ý và phân biệt nghĩa](#language) | 40 | 9 | 28 |
| [Mã, số, đơn vị và định dạng](#values) | 40 | 24 | 25 |
| [Chủ kho, bộ lọc và trạng thái ghi chú](#scope) | 40 | 38 | 39 |
| **Tổng** | **120** | **71** | **92** |

Với câu một đáp án, ghi chú cần đứng đầu. Với câu nhiều đáp án, mọi ghi chú yêu cầu phải nằm trong năm kết quả đầu. Với câu không có đáp án, danh sách phải rỗng. Nếu bất kỳ kết quả nào nằm ngoài phạm vi đã chọn thì ca đó trượt. Ở cột cuối, công cụ chọn **Tìm gần đúng** mỗi khi dịch vụ cho phép, tổng cộng 45/120 câu. Những câu còn lại giữ kết quả lượt đầu.

| Kỳ vọng | Lượt đầu | Khi dùng thêm **Tìm gần đúng** |
| --- | ---: | ---: |
| Một ghi chú đúng đứng đầu | 46/81 | 70/81 |
| Đủ các ghi chú được hỏi trong năm kết quả đầu | 5/13 | 10/13 |
| Trả rỗng cho câu không có đáp án | 20/26 | 12/26 |

**Ba lỗi ảnh hưởng trực tiếp đến người tìm.**

- **Gắn số với sai thuộc tính.** V37 hỏi ngày đo mưa 5/6 nhưng tìm thấy tờ đo ngày 4/6 và ký ngày 5/6. V36 hỏi thiệp ngang 148 mm, cao 105 mm lại được bản có hai chiều ngược nhau. V34 ghép số 52 với dB(C) dù ghi chú chỉ có 52 dB(A) và 67 dB(C).
- **Bỏ sót cách viết tương đương.** V04 gõ `0.48 s` không tìm được bản ghi `0,48 s`. V23 dán mã toàn chiều rộng `ＣＭ－７３Ｂ` không tìm được `CM-73B`. Cả hai câu đều không có nút mở rộng.
- **Gợi ý một ghi chú nói điều ngược lại.** L34 hỏi về việc đi giày gõ thẳng lên sàn, kết quả đầu tiên khi mở rộng là nội quy chỉ cho phép đi loại giày này trên ván riêng. Cả 8 câu không có đáp án của nhóm ngữ nghĩa đều nhận gợi ý sai sau khi mở rộng.

Trong các danh sách đã đọc, không xuất hiện ghi chú của sai chủ kho, trong thùng rác, bị loại trừ hoặc ngoài bộ lọc. S38 trượt vì một ghi chú *đúng phạm vi* nói về tấm chắn ở bàn cân lại được gợi ý cho câu hỏi về rèm treo trần.

## Đọc và chạy lại

Các bảng bên dưới ghi tối đa năm mã theo thứ tự thực tế. `∅` là danh sách rỗng. Dấu ⇥ trong V06 biểu diễn ký tự tab thật. Cả văn bản nguồn và bộ lọc của từng ca nằm trong ba tệp đề. [Ghi chú ngữ nghĩa](language.json) · [Ghi chú có mã và số](values.json) · [Ghi chú có bộ lọc](scope.json)

Để kiểm đề và kiểm công cụ chấm mà không mở cơ sở dữ liệu, chạy từ gốc repo.

```powershell
python -B evals/vietnamese-journeys/confusable-cases/run.py --matrix --validate-only
python -B -m unittest discover -s evals/vietnamese-journeys/scenario-matrix -p test_scoring.py
```

Để đo lại, dùng Python của backend và PostgreSQL QA cục bộ. Trỏ cấu hình Django tới DB trống `kt_eval_edge_pairs`, đã tạo và migrate theo hướng dẫn. Truy vấn chạy qua `SearchService`, với chủ kho và bộ lọc của từng câu. Công cụ hoàn tác dữ liệu thử, kiểm lại số người dùng và ghi chú, rồi mới ghi kết quả ra tệp mới. Thêm `--require-all` khi muốn lệnh trả mã lỗi nếu bất kỳ ca nào trượt ở một trong hai chế độ. [Hướng dẫn PostgreSQL QA](../README.md#chạy-từ-gốc-repo) · [Công cụ đo](../confusable-cases/run.py)

```powershell
$env:POSTGRES_HOST = '127.0.0.1'
$env:POSTGRES_DB = 'kt_eval_edge_pairs'
$env:KT_EVAL_ALLOW_DISPOSABLE = '1'
python evals/vietnamese-journeys/confusable-cases/run.py --matrix --expected-source 059f6d4 --report matrix-local.json
```

Phép đo dùng backend của `059f6d4`. Công cụ kiểm 120 câu sau khi chuẩn hóa Unicode, kiểu chữ, khoảng trắng, dấu và ký tự phân cách, đồng thời đối chiếu với các bộ 21, 39, 51 và 86 câu từng có. Đây là đánh giá dịch vụ trên văn bản tự soạn. Lượt này chưa đo thao tác trình duyệt hay mức độ hài lòng của người dùng thật.

<a id="language"></a>

## Tìm lại ý và phân biệt ngữ nghĩa trong ghi chú tiếng Việt

| Ca | Truy vấn và phạm vi | Đáp án và căn cứ | Lượt đầu | Khi dùng gợi ý |
| --- | --- | --- | --- | --- |
| L01 | «Nồi chè bắp chia sẵn hôm đó, phần bớt đường chừa cho ai?» | LN01<br>Ghi chú dùng từ ngô nếp cho bắp và để một phần ít ngọt cho bác trông nhà. | **Sai** · ∅ | Đạt · LN01, SN27, LN04 |
| L02 | «Cái mùng thay tạm cho ca ngủ đêm cất ở đâu? Nhớ cái có dây cam.» | LN02<br>Mùng là màn chống muỗi. Chiếc dự phòng có dây màu cam nằm ở ngăn trên của tủ chăn. | **Sai** · ∅ | Đạt · LN02 |
| L03 | «Nhà cô Mận có việc buồn, mình đã lưu lời ghi trên vòng hoa của tổ ở đâu?» | LN03<br>Ghi chú nói gia đình cô Mận có tang và chép nguyên dòng chữ trên vòng hoa. | **Sai** · ∅ | Đạt · LN03, VN42, VN01, LN23 |
| L04 | «Lúc cắt vải ở nách áo đồng ca, phần nằm ngoài đường khâu chừa cỡ nào?» | LN04<br>Mẫu áo quy định phần vải ngoài đường ráp rộng một đốt tay và nói rõ bản rập chưa tính phần đó. | **Sai** · ∅ | Đạt · LN04, SN24, LN24, LN08 |
| L05 | «Tụi nhỏ đứng cánh gà bên nào trong tiết mục đầu tiên?» | LN05<br>Chỗ khuất sau rèm ở bên phải sân khấu là nơi nhóm diễn viên nhí chờ trong màn mở đầu. | **Sai** · ∅ | **Sai** · VN19, VN50, LN05 |
| L06 | «Nướng cánh gà thì nhìn dấu hiệu nào để biết lật được, khỏi giật rách da?» | LN06<br>Mặt dưới tự róc khỏi vỉ là dấu hiệu để lật. Ghi chú sân khấu chỉ nói chỗ đợi của diễn viên. | **Sai** · ∅ | Đạt · LN06 |
| L07 | «Tìm lần nhà hát được nhóm hát biếu đồ để điểm màu lúc chào khán giả.» | LN07<br>Nhóm hợp xướng là bên trao cuộn băng vải tím, phụ trách đạo cụ của nhà hát là bên nhận. | **Sai** · ∅ | Đạt · LN07 |
| L08 | «Cái túi hình mèo bên khung dệt chứa loại ống quấn sợi làm từ gì?» | LN08<br>Túi hình mèo chứa suốt nhựa. Suốt tre nằm trong túi hình cá. | **Sai** · ∅ | Đạt · LN08 |
| L09 | «Tại sao tấm vải dựng cảnh bến đò lại nhăn, mình có ghi nguyên do đâu đó.» | LN09<br>Việc cuộn phông khi còn ẩm được ghi là nguyên nhân tạo nếp hằn. Việc hong vải diễn ra sau khi phát hiện. | **Sai** · ∅ | Đạt · LN09, VN01 |
| L10 | «Đang hát đoạn lặp mà hụt phách thì nghe tiếng gì để bắt đầu lại?» | LN10<br>Khi lỡ nhịp ở điệp khúc, người hát nghe trống thêm một ô nhịp rồi vào lại. | **Sai** · ∅ | **Sai** · LN22, LN13 |
| L11 | «Có trường hợp nào đi giày đế cứng tập nhảy được, miễn đứng trên mặt kê riêng?» | LN11<br>Ngoại lệ dành cho người tập nhảy gõ khi đứng trên tấm ván chuyên dụng. Sàn chính vẫn cấm giày đế cứng. | **Sai** · ∅ | Đạt · LN11, SN26, SN17, VN13 |
| L12 | «Món bánh gạo còn nguyên mà khách vẫn phải chờ, thiếu dụng cụ nào thì quầy ngừng phục vụ vậy?» | LN12<br>Quầy tạm ngừng bán khi hết kẹp tre để gắp bánh, kể cả lúc trong khay còn bánh và còn khách. | **Sai** · ∅ | Đạt · LN12, LN33, LN27, LN34, LN24 |
| L13 | «Bữa nào thầy bảo ghép giọng ở khúc chót thôi, khoan hát nguyên bài?» | LN13<br>Chiều nay chỉ ráp bè cao và bè trầm ở đoạn kết. Cả lớp chưa hát liền mạch vì phần mở chưa tập xong. | **Sai** · ∅ | **Sai** · LN10, LN21 |
| L14 | «Đi ngang khu trưng bày, chụp bảng chỉ chỗ các gian để dễ đi có cần hỏi trước không?» | LN14<br>Sơ đồ gian hàng được phép chụp. Việc hỏi trước chỉ áp dụng khi chụp rõ mặt một người. | **Sai** · ∅ | Đạt · LN14, SN22, SN30, SN29, LN30 |
| L15 | «Sợi mắc trong thoi dệt, cho mình xem tờ dặn lấy ống ra rồi mới tháo chỗ thắt.» | LN15<br>Khi sợi quấn chặt, người dệt rút suốt ra trước rồi mới tháo nút ở đầu sợi. | **Sai** · ∅ | Đạt · LN15, LN08, LN17, LN02 |
| L16 | «Cúp điện chỗ học hát, cuối cùng học bên nào mà vẫn tập đúng buổi?» | LN16<br>Cả lớp chuyển sang hội trường nhỏ và giữ nguyên buổi luyện thanh chiều nay. | **Sai** · ∅ | **Sai** · LN13, VN19, LN21, LN16, VN13 |
| L17 | «Tấm nền chụp ảnh bằng vải chưa tẩy là ý kiến mới nêu hay trưởng ban đã quyết rồi?» | LN17<br>Vải mộc chưa tẩy mới được đề nghị trong nhóm chat. Trưởng ban còn đợi xem hai mẫu trước khi quyết định chất liệu. | **Sai** · ∅ | Đạt · LN17, VN35, VN37, LN22 |
| L18 | «Tối trước hôm giao hàng sớm, vật gì phải để ngoài tới sáng để họ tìm được chuông cửa bên hông?» | LN18<br>Biển nhận hàng được đặt ở cửa phụ tối thứ bảy và để qua đêm cho người giao sớm chủ nhật. | **Sai** · ∅ | Đạt · LN18, LN21, LN14, SN18 |
| L19 | «Tính riêng đám kéo màn nhận mấy chiếc găng, đừng cộng hai chiếc xám nằm lại.» | LN19<br>Sáu đôi, mỗi đôi một chiếc trái và một chiếc phải, là mười hai chiếc cho đội kéo màn. Hai chiếc xám không được phát. | **Sai** · ∅ | Đạt · LN19, VN17 |
| L20 | «Vụ họp về ồn ào ấy, mỗi nhóm được đưa bao nhiêu người tới thay mặt cả nhóm?» | LN20<br>Mỗi nhóm cử đúng một đại diện. Người khác gửi ý kiến qua đại diện. | **Sai** · ∅ | Đạt · LN20, LN03, LN05, LN21 |
| L21 | «Bài cô dặn đừng để nước đến chân mới nhảy khi ghép đàn nằm đâu?» | LN21<br>Cô yêu cầu ráp đàn từ đầu tuần vì lần trước chờ đến hôm chót mới phát hiện hai đàn lên giọng khác nhau. | **Sai** · ∅ | Đạt · LN21 |
| L22 | «Kéo rèm giữa câu thoại nhỏ mà không át tiếng người diễn, hồi đó sửa cái gì?» | LN22<br>Đổi vòng sắt sang vòng gỗ lót vải khiến người xem hàng đầu vẫn nghe được lời thoại thì thầm khi rèm di chuyển. | **Sai** · ∅ | Đạt · LN22, VN18, LN05, VN19, LN39 |
| L23 | «Hòa thấy hai hình ngôi sao trên tờ nhạc. Chỗ nào mới là lượt em tự đọc?» | LN23<br>Dấu sao thứ hai đánh chỗ Hòa tự đọc. Dấu thứ nhất là chỗ cô đọc mẫu, còn mũi tên dùng để chuyển bài. | **Sai** · ∅ | Đạt · LN23, LN35, VN09, LN17, VN47 |
| L24 | «Ai nhờ chị Duyên nhắn lại là cứ để hộp phấn ở bàn thợ cả?» | LN24<br>Bác Tịnh là người dặn. Chị Duyên chỉ chuyển lời tới người lấy dụng cụ. | Đạt · LN24 | Đạt · LN24 |
| L25 | «Có lần nào diễn trọn vở trong bộ đồ biểu diễn dù không mở hệ thống tiếng?» | LN25<br>Đoàn diễn hết các cảnh với đủ phục trang và tắt loa suốt lượt. Diễn viên vẫn nói bằng giọng thật. | **Sai** · ∅ | Đạt · LN25, VN13, LN39, SN14, LN05 |
| L26 | «Thứ gì luồn qua đoạn khăn gồ mà bớt móc xù sợi hơn loại mũi bén?» | LN26<br>Kim đầu tròn ít mắc hơn kim đầu nhọn và được dùng cho đoạn khăn có sọc nổi. | **Sai** · ∅ | Đạt · LN26 |
| L27 | «Muốn hồ sơ xin bày hàng vải qua khâu tiếp nhận, ảnh sản phẩm phải gửi kèm giấy thể hiện gì?» | LN27<br>Hồ sơ cần đồng thời có ảnh mẫu hàng và sơ đồ kích thước quầy. Thiếu một thì hồ sơ chờ bổ sung. | **Sai** · ∅ | Đạt · LN27, LN14, VN17, VN02, LN34 |
| L28 | «Quên đem vé giấy đi nghe nhạc, mở email xác nhận ở điện thoại là vào được chứ?» | LN28<br>Soát cửa chấp nhận một trong hai minh chứng, gồm vé giấy hoặc thư xác nhận hiển thị trên điện thoại. | Đạt · LN28 | Đạt · LN28 |
| L29 | «Ở buổi đổi sách sân B, tìm đủ ghi chú về cách tự nhìn biển để đi và cách nhờ một người dẫn nếu chưa rành tiếng Việt.» | LN29, LN30<br>LN29 mô tả bảng mũi tên và hình. LN30 mô tả tình nguyện viên dẫn khách. Mỗi ghi chú chỉ nêu một hình thức. | **Sai** · ∅ | Đạt · LN30, LN29, VN19, LN05, SN26 |
| L30 | «Cho mình cả hai mẫu xem đũi với gai ăn màu khác nhau ra sao ngay khi vừa nhúng chàm lượt đầu.» | LN31, LN32<br>LN31 ghi đũi lên xanh xám sau lần nhúng đầu. LN32 ghi gai lên xanh đậm sau cùng lượt nhúng trong cùng mẻ chàm. | **Sai** · ∅ | Đạt · LN31, LN32, LN21, VN22, VN14 |
| L31 | «Ngày hội Gió Nồm có gì dành cho người tránh sữa? Lấy giúp cả ghi chép về nước uống lẫn phần đồ ăn.» | LN33, LN34<br>LN33 nêu quầy pha trà và nước quả dùng dụng cụ riêng. LN34 nêu lô bánh riêng và cách giữ gói cho tới khi phát. | **Sai** · ∅ | Đạt · LN33, LN34, VN24, SN15, VN51 |
| L32 | «Tìm giúp bảng khoản gia đình phải trả cho khóa hòa tấu hè và tờ về phần quỹ có thể đỡ tiền.» | LN35, LN36<br>LN35 liệt kê học phí cùng khoản thuê đàn. LN36 giới hạn hỗ trợ quỹ ở phần học phí, nên cần cả hai nguồn. | **Sai** · ∅ | Đạt · LN36, LN35, VN28 |
| L33 | «Tìm tờ bếp ghi phải nấu bù mẻ đậu vì nồi men cũ làm cháy mẻ đầu.» | ∅<br>LN37 ghi bếp nấu thêm vì có thêm khách. Nồi cũ chỉ đem sửa quai và mẻ đầu vẫn được dọn. | Đạt · ∅ | **Sai** · LN37, VN26 |
| L34 | «Hướng dẫn mang giày gõ đi thẳng lên sàn chính khỏi cần tấm kê ở đâu?» | ∅<br>LN11 chỉ cho dùng giày gõ trên ván chuyên dụng và cấm giày đế cứng trên sàn chính. | Đạt · ∅ | **Sai** · LN11, VN19, LN30 |
| L35 | «Có phải hôm tặng dải băng tím, phụ trách đạo cụ đem màu tím sang biếu nhóm hợp xướng?» | ∅<br>LN07 ghi nhóm hợp xướng tặng vật này cho nhà hát, phụ trách đạo cụ là bên nhận. | Đạt · ∅ | **Sai** · LN07, LN19, SN21 |
| L36 | «Tờ hẹn sáng chủ nhật đem khăn dệt mẫu đến phòng sinh hoạt vẫn kịp gửi sang xưởng giặt.» | ∅<br>LN38 đóng nhận mẫu vào trưa thứ bảy rồi chuyển toàn bộ mẫu đi giặt trong chiều thứ bảy. | Đạt · ∅ | **Sai** · LN38, LN20, LN01, SN05, VN10 |
| L37 | «Đâu là giấy quỹ mái hiên trả luôn cả phí thuê đàn cho gia đình?» | ∅<br>LN36 chỉ hỗ trợ học phí và ghi gia đình tự trả khoản thuê đàn. LN35 chỉ bỏ khoản thuê khi học viên tự mang đàn. | Đạt · ∅ | **Sai** · LN36, LN35 |
| L38 | «Có ghi chú nào bảo nghe hai tiếng gõ thì diễn viên ra diễn cảnh tiếp theo?» | ∅<br>LN39 dùng hai tiếng gõ để nhắc vào đúng vạch thử đèn. Tín hiệu ra diễn là lúc trợ lý gọi tên qua bộ đàm. | Đạt · ∅ | **Sai** · LN39, LN22, LN25, LN28, VN05 |
| L39 | «Tờ nhuộm vải gai ra xanh xám ngay nước đầu, dán mẫu vào cuối trang.» | ∅<br>LN32 đúng là mẫu gai ở cuối trang nhưng mẫu lên xanh đậm. Xanh xám là màu của đũi ở LN31. | **Sai** · LN32 | **Sai** · LN32, LN31, LN23, LN17, VN19 |
| L40 | «Hồ sơ gian vải được xác nhận chỉ bằng ảnh hàng, sơ đồ quầy thiếu cũng không sao.» | ∅<br>LN27 yêu cầu cả hai và chuyển hồ sơ thiếu sơ đồ sang chờ bổ sung. Quy tắc chỉ cần một giấy tờ của LN28 áp dụng cho khách nghe nhạc. | Đạt · ∅ | **Sai** · LN27, LN28, LN14, SN22, LN33 |

<a id="values"></a>

## Tìm ghi chú theo thông số, mã và cách trình bày

| Ca | Truy vấn và phạm vi | Đáp án và căn cứ | Lượt đầu | Khi dùng gợi ý |
| --- | --- | --- | --- | --- |
| V01 | «tác phẩm Mùa đò vắng của NXB Bến Hổ Phách có bản đồ gấp» | VN01<br>Câu mô tả tác phẩm, nhà xuất bản và bản đồ cùng chỉ VN01. VN02 cùng tác giả, cùng nhà xuất bản nhưng ghi Mùa đò trắng và ba ảnh rời. VN49 là bản chép tay ở câu lạc bộ, nằm ngoài đợt xuất bản. | Đạt · VN01, VN02, VN49 | Đạt · VN01, VN02, VN49, SN07 |
| V02 | «lời bạt về người lái đò ở cuối Mùa đò trắng» | VN02<br>VN02 có lời bạt cuối sách về người lái đò. VN01 có lời tựa về bến cũ, một phần khác của sách. | Đạt · VN02 | Đạt · VN02, VN01, VN49, LN21, VN48 |
| V03 | «thiệp Mực Tía 105 x 148 mm» | VN03<br>VN03 ghi khổ ngang × cao là 105 × 148 mm. Chữ x trong câu là cách gõ dấu nhân cho kích thước, giữ nguyên hai giá trị và thứ tự. Phiếu dàn thử VN42 ghi chiều ngang 100 mm. | Đạt · VN03 | Đạt · VN03 |
| V04 | «Nhịp Lá độ vang 0.48 s» | VN04<br>VN04 ghi số trung bình 0,48 s với dấu phẩy thập phân. Số viết bằng dấu chấm trong câu biểu diễn cùng giá trị và đơn vị. VN43 đo sau khi treo rèm và ghi 0,43 s. | **Sai** · ∅ | **Sai** · ∅ |
| V05 | «hành lang Chồi Non 52 dB(A)» | VN05<br>VN05 gắn 52 với trọng số A. Trong cùng ghi chú, 67 dB(C) là một phép ghi khác, giữ nguyên cả chữ trong ngoặc và giá trị. VN44 là lượt đo trước tiết một với mức trọng số A 55 dB(A). | Đạt · VN05 | Đạt · VN05 |
| V06 | «GS57 ⇥ ghi đá ⇥ đã duyệt» | VN06<br>VN06 chứa đúng tổ hợp mã, màu và tình trạng. Các tab là ranh giới giữa ô khi dán từ bảng tính. Dòng GS75 dùng màu ghi ngọc. | Đạt · VN06 | Đạt · VN06 |
| V07 | «bản vẽ thu nhỏ Lồng Đèn tỉ lệ 1:25» | VN07<br>VN07 ghi 1:25 cho bản vẽ, còn 1:20 thuộc mô hình thử. Dấu hai chấm nối hai vế tỉ lệ. VN45 có bản vẽ cùng tên nhưng dùng 1:24. | Đạt · VN07 | Đạt · VN07 |
| V08 | «ẩm kế Tầm Vông 30-80% RH theo tem» | VN08<br>VN08 ghi 30–80% RH trên tem và 40–70% RH ở sổ tham khảo. Dấu gạch ngắn gõ tay thay dấu gạch chỉ khoảng. | **Sai** · ∅ | **Sai** · ∅ |
| V09 | «thanh trượt Bản Nhạc Sân Trường sửa ở bản 2.4.10» | VN09<br>VN09 ghi đúng phiên bản 2.4.10 cho chỉnh thanh trượt. Phiên bản 2.4.1 trong bài chỉ gắn với lỗi phát lặp. | **Sai** · ∅ | **Sai** · ∅ |
| V10 | «lượng mưa Dốc Nguyệt ngày 04/06/2025» | VN10<br>Ngày đo 2025-06-04 ở VN10 là ngày 4 tháng 6. Ngày 2025-06-05 chỉ là ngày ký tờ tổng hợp. VN46 đo ngày 6 tháng 4, đảo vị trí của tháng và ngày. | **Sai** · ∅ | **Sai** · ∅ |
| V11 | «mục lục Diều Sóng phiếu 14/2023-TĐG» | VN11<br>VN11 có đúng mã trọn vẹn cho mục lục Diều Sóng. Mã 14/2022-TĐG dành cho danh mục đạo cụ. | Đạt · VN11 | Đạt · VN11 |
| V12 | «mã phông SL-O8 lấy ở kệ dưới» | VN12<br>VN12 ghi SL-O8 là cuộn xám ở kệ dưới. SL-08 dùng số 0 và chỉ cuộn trắng. | Đạt · VN12 | Đạt · VN12 |
| V13 | «mặt trống CV-41 biểu diễn» | VN13<br>VN13 gắn CV-41, ký tự cuối là số 1, với trống biểu diễn. CV-4I là mặt trống tập. | Đạt · VN13 | Đạt · VN13 |
| V14 | «ô tra màu xám mờ BB-0042» | VN14<br>VN14 ghi BB-0042 đầy đủ cho màu xám mờ. Bỏ hai số 0 sẽ thành mã mẫu nhũ bạc BB-42. | Đạt · VN14 | Đạt · VN14 |
| V15 | «Cỏ Tuyết nhiệt độ thấp nhất -2,6 °C» | VN15<br>VN15 lưu −2,6 °C với dấu trừ Unicode. Dấu gạch ngắn trước số trong câu có nghĩa âm. 2,6 °C trong sổ bên cạnh là số dao động. | Đạt · VN15 | Đạt · VN15 |
| V16 | «ho dan giay do dieu Canh Bac de nguoi» | VN16<br>VN16 ghi hồ dán giấy dó cho Cánh Bấc, để nguội trước khi quét. Hồ và khô đều có trong bài, nhưng chỉ hồ dán là thứ để nguội. | Đạt · VN16 | Đạt · VN16 |
| V17 | «Bướm Đậu Bờ Tre nút rút dây» | VN17<br>VN17 có tên Bướm Đậu Bờ Tre và nút rút dây. Các dấu tổ hợp trong chuỗi dán giữ nguyên cách đọc tiếng Việt của tên tập. | Đạt · VN17 | Đạt · VN17 |
| V18 | «"Đêm chứa hạt - sớm mọc mây"» | VN18<br>VN18 chứa đúng câu thơ, với ngoặc cong và gạch dài. Câu dưới tranh kể trời chứa hạt và dùng hình ảnh buổi chiều. | **Sai** · ∅ | **Sai** · ∅ |
| V19 | «đường hồi phụ R-17 cho bè alto» | VN19<br>Thông tin quyết định nằm ở câu bàn giao cuối của VN19. Tiêu đề và hai đoạn đầu đều kể việc kê bục và tập sân khấu. VN50 ghi đường R-71 cho cùng bè alto. | Đạt · VN19 | Đạt · VN19 |
| V20 | «dấu hỏi ngăn C3 trong khay thiếc» | VN20<br>VN20 gắn C3 và dấu hỏi với khay thiếc trong cùng câu. Khay gỗ nằm ở câu kế và giữ chữ số tại D3. | Đạt · VN20 | Đạt · VN20 |
| V21 | «phụ lục IV thế đặt tay Gió Gánh Màu» | VN21<br>VN21 có phụ lục IV về cách đặt tay sau trang 92. Phụ lục III chỉ là danh sách bản nhạc. VN51 xếp các thế đặt tay ở phụ lục V của tuyển tập. | Đạt · VN21, VN51 | Đạt · VN21, VN51 |
| V22 | «tốc độ chép tệp ở Thạch Sương 24 MB/s» | VN22<br>VN22 gắn MB/s với ổ đọc và thao tác chép tệp. Mb/s có cùng số nhưng là đơn vị cho phép thử đường truyền. VN47 ghi 23 MB/s cho ổ đọc dự phòng. | Đạt · VN22 | Đạt · VN22 |
| V23 | «mã dấu ＣＭ－７３Ｂ Chổi Mây» | VN23<br>Dãy ký tự toàn chiều rộng vẫn ghi CM-73B, mã dấu trên bao đựng của VN23, khác mã thùng bị đảo chữ số CM-37B. | **Sai** · ∅ | **Sai** · ∅ |
| V24 | «Mã kệ: HV-B6» | VN24<br>VN24 có dòng Mã kệ: HV-B6 với dấu hai chấm là phần văn bản của phiếu. PX-86 là mã phiếu xuất, khác vai trò. | Đạt · VN24 | Đạt · VN24 |
| V25 | «DeThangBay-BanCo.wav có giọng đọc» | VN25<br>VN25 có hai tên cùng phần gốc. Đuôi .wav cùng bằng chứng giọng đọc xác định tệp âm thanh, loại bản chữ .txt. VN48 lưu tệp .wav có giọng đọc của Dế Tháng Sáu, một tác phẩm khác. | Đạt · VN25 | Đạt · VN25 |
| V26 | «Hõm Sỏi số in chìm dưới dấu dập tay gập phải» | VN26<br>VN26 có số 172 dưới dấu dập ở tay gập phải. Số 127 ghi ở dải gáy nên không đáp ứng vị trí người dùng nhớ. | Đạt · VN26 | Đạt · VN26 |
| V27 | «giá tranh Vệt Nắng nghiêng 18°» | VN27<br>VN27 gắn 18° với góc nghiêng về sau. Số 18 cm trùng phần số nhưng ghi độ sâu chân giá. | Đạt · VN27 | Đạt · VN27 |
| V28 | «tập Đốm Vàng 1250 tờ giấy lót» | VN28<br>VN28 xác nhận 1.250 tờ, dùng dấu chấm nhóm hàng nghìn. 1,250 mm có dấu phẩy thập phân và là độ dày tấm ép. | **Sai** · ∅ | **Sai** · ∅ |
| V29 | «cả bản giấy dó lẫn giấy ngà in thử Bóng Rặng Me của Đom Đóm Nâu» | VN29, VN30<br>Hai ghi chú khớp riêng từng vật liệu của đợt in thử. VN31 ghi phát hành chính thức nên nằm ngoài yêu cầu. | **Sai** · ∅ | Đạt · VN30, VN29, VN31, SN06, SN05 |
| V30 | «bảng trực cửa phía đông và phía tây Nhà Kính San Hô 09:00-11:30» | VN32, VN33<br>VN32 và VN33 lần lượt ghi cửa đông và cửa tây, cùng 09:00–11:30. VN34 là cửa bắc với giờ khác. | **Sai** · ∅ | **Sai** · ∅ |
| V31 | «tất cả chú thích ảnh Chiếc Vành Lá mang mã tủ KL.3» | VN35, VN36<br>Cần cả ảnh mặt trước và ảnh nghiêng mang đúng KL.3. Ảnh bằng máy lấy ngay trong VN37 mang mã KL.33 dài hơn. | **Sai** · ∅ | **Sai** · ∅ |
| V32 | «mọi phiếu đọc bến Rong Mơ lúc 06:15 có chênh +7 cm» | VN38, VN39, VN40<br>Ba cọc trên, giữa, dưới cùng khớp giờ và dấu cộng. VN41 đọc cùng giờ nhưng chênh −7 cm nên bị loại. | **Sai** · ∅ | **Sai** · ∅ |
| V33 | «Mùa đò vắng Nhà xuất bản Bến Hổ Ngọc» | ∅<br>VN01 khớp tên tác phẩm nhưng nhà xuất bản là Bến Hổ Phách. Không có ghi chú nào ghi ấn bản Bến Hổ Ngọc. | **Sai** · VN49, VN01, VN02 | **Sai** · VN49, VN01, VN02, VN31, VN30 |
| V34 | «Chồi Non mức âm nền 52 dB(C)» | ∅<br>VN05 có cả 52 và dB(C), nhưng tách ở hai mức 52 dB(A) và 67 dB(C). Không có phép đo 52 dB(C) ở hành lang. | **Sai** · VN05 | **Sai** · VN05 |
| V35 | «phiếu mục lục Diều Sóng số 41/2023-TĐG» | ∅<br>VN11 khớp năm và tên mục nhưng mã bắt đầu bằng 14, không thấy mã có hai chữ số đảo thứ tự thành 41. | Đạt · ∅ | Đạt · ∅ |
| V36 | «thiệp Mực Tía in ngang 148 mm cao 105 mm» | ∅<br>VN03 ghi ngang 105 mm, cao 148 mm. Hai kích thước đều có mặt nhưng nằm ở vị trí ngược với khổ yêu cầu. | **Sai** · VN03 | **Sai** · VN03 |
| V37 | «Dốc Nguyệt đo mưa ngày 2025-06-05» | ∅<br>VN10 chỉ dùng ngày 2025-06-05 cho chữ ký. Tờ nhật ký có phép đo ngày 2025-06-04. | **Sai** · VN10 | **Sai** · VN10 |
| V38 | «tốc độ đường truyền Thạch Sương 24 MB/s» | ∅<br>VN22 ghi đường truyền 24 Mb/s và tốc độ chép ở ổ đọc 24 MB/s. Đơn vị mang chữ B hoa thuộc phép đo chép tệp. | **Sai** · VN22 | **Sai** · VN22 |
| V39 | «tem ẩm kế Tầm Vông loại không tính mức 30% và 80% RH» | ∅<br>VN08 nói rõ tem tính cả hai mức biên. Khoảng 40–70% RH là tham khảo trong sổ, không phải tem ghi loại trừ 30% và 80%. | Đạt · ∅ | Đạt · ∅ |
| V40 | «bản thu Dế Tháng Bảy DeThangBay-BanCo.mp3» | ∅<br>VN25 chỉ nêu bản âm thanh .wav và bản chữ .txt. Cùng tên gốc chưa đủ để xác nhận có tệp .mp3. | Đạt · ∅ | Đạt · ∅ |

<a id="scope"></a>

## Tìm ghi chú tiếng Việt theo phạm vi kho, tình trạng và bộ lọc

| Ca | Truy vấn và phạm vi | Đáp án và căn cứ | Lượt đầu | Khi dùng gợi ý |
| --- | --- | --- | --- | --- |
| S01 | «phiếu nghiệm thu lối thoát»<br>Chủ đề *An toàn công trình* · Dự án *Rạp ven sông* · Thẻ *Nghiệm thu* | SN01<br>SN01 có đúng cụm từ trong ghi chú và đủ ba quan hệ. SN02 khác chủ đề, SN03 khác dự án, SN04 khác thẻ dù cả ba cùng có cụm tìm. | Đạt · SN01 | Đạt · SN01 |
| S02 | «lối thoát»<br>Dự án *Rạp ven sông* · Thẻ *Nghiệm thu* | SN01, SN02<br>Cả bản đo bề rộng và bản kiểm biển chỉ đường nói về lối thoát, cùng thuộc dự án và đã gắn thẻ Nghiệm thu. | Đạt · SN01, SN02 | Đạt · SN01, SN02 |
| S03 | «vạch phản quang chân tường»<br>Dự án *Rạp ven sông* · Thẻ *Đề xuất* | SN04<br>Bản nháp SN04 là ghi chú duy nhất đề xuất dán vạch phản quang dọc chân tường tại rạp. | Đạt · SN04 | Đạt · SN04 |
| S04 | «nghiệm thu lối thoát cửa phía tây»<br>Dự án *Hội trường trên đồi* | SN03<br>SN03 ghi bục phát biểu chắn cửa phía tây của hội trường. Các bản rạp ven sông nói về một địa điểm khác. | Đạt · SN03 | Đạt · SN03 |
| S05 | «in thu chu giai bang chu noi»<br>Chủ đề *Tiếp cận công cộng* · Dự án *Sơ đồ khu phố* · Thẻ *Đồ dùng lớp học* | SN05<br>SN05 khớp ghi chú in thử chú giải bằng chữ nổi qua quan hệ thứ hai ở cả ba chiều. SN07 có chung bộ lọc nhưng dùng vòng tròn đồng tâm cho bến phà. | Đạt · SN05 | Đạt · SN05 |
| S06 | «gờ chấm từ bậc thềm»<br>Chủ đề *Giáo dục* · Dự án *Tủ học liệu* · Thẻ *In thử* | SN05<br>Gờ chấm của SN05 dẫn tay từ bậc thềm đến bàn giáo viên. SN06 cùng lô in thử nhưng là bài ghép la bàn. | Đạt · SN05 | Đạt · SN05 |
| S07 | «ba vòng tròn đồng tâm»<br>Chủ đề *Tiếp cận công cộng* · Dự án *Sơ đồ khu phố* · Thẻ *Đồ dùng lớp học* | SN07<br>SN07 dùng ba vòng tròn đồng tâm để đánh dấu bến phà. Cùng tập đồ dùng, SN05 dùng gờ chấm cho hành trình khác. | Đạt · SN07 | Đạt · SN07 |
| S08 | «phiếu lắp khung mica»<br>Chủ đề *Trưng bày* · Dự án *Tuần thủ công* · Thẻ *Đã duyệt* | SN08<br>Hai phiếu đều có đúng nội dung tìm và ba nhãn cùng tên. Phiếu có miếng đệm nỉ thuộc kho main, phiếu chốt lò xo thuộc guest. | Đạt · SN08 | Đạt · SN08 |
| S09 | «khung mica»<br>Chủ kho *guest* · Thẻ *Đã duyệt* | SN09<br>Kho guest giữ SN09 về mẫu dệt, có thẻ Đã duyệt của guest. SN08 là phiếu tranh in của main với cùng cụm tìm. | Đạt · SN09 | Đạt · SN09 |
| S10 | «đồng hồ nước»<br>Dự án *Vườn mưa* | SN13, SN14<br>Hai ca ở vườn mưa đều ghi số đồng hồ nước. Bảng đồng hồ nước của xưởng nhuộm thuộc dự án khác. | Đạt · SN14, SN13 | Đạt · SN14, SN13 |
| S11 | «tủ chìa khóa nhà thuyền»<br>Chủ đề *Trực vận hành* · Dự án *Nhà thuyền* · Thẻ *Hướng dẫn* | SN10<br>SN10 là sổ hiện hành. SN11 cùng nội dung tìm và metadata nhưng đã chuyển vào thùng rác. | Đạt · SN10 | Đạt · SN10 |
| S12 | «phòng trực móc số 6»<br>Dự án *Nhà thuyền* | SN10<br>Sổ hiện hành SN10 xác định phòng trực và móc số 6. Sổ cũ dùng móc số 2 và nằm trong thùng rác. | Đạt · SN10 | Đạt · SN10 |
| S13 | «bảo dưỡng đồng hồ nước»<br>Bỏ mục *SN13* · Dự án *Vườn mưa* · Thẻ *Nhật ký ca* | SN14<br>SN13 đang mở và bị loại. Nhật ký ca tối SN14 cùng thiết bị, dự án và thẻ đủ điều kiện. | Đạt · SN14 | Đạt · SN14 |
| S14 | «đồng hồ nước lưu lượng súc máng»<br>Bỏ mục *SN14* · Chủ đề *Bảo dưỡng* | SN15<br>SN14 đang mở có nhắc mục lưu lượng súc máng nhưng phải loại bằng ID. SN15 cùng chủ đề và có bảng theo dõi lưu lượng của xưởng nhuộm. | Đạt · SN15 | Đạt · SN15 |
| S15 | «ghi số đồng hồ nước»<br>Bỏ mục *SN14* · Chủ đề *Bảo dưỡng* | SN13, SN15<br>SN13 và SN15 đều cùng chủ đề và ghi số đồng hồ nước. SN14 cũng có đúng cụm tìm nhưng bị loại bằng ID. | Đạt · SN15, SN13 | Đạt · SN15, SN13 |
| S16 | «ong nhom gap»<br>Chủ đề *Dụng cụ cầm tay* · Thẻ *Bảo quản* | SN16<br>Tên dụng cụ chỉ xuất hiện trong tiêu đề SN16. Nội dung đi với tiêu đề chỉ gọi chung là thiết bị. | Đạt · SN16 | Đạt · SN16 |
| S17 | «kẹp nam châm chân đế»<br>Dự án *Trạm quan sát* · Thẻ *Kiểm kê* | SN17<br>Mô tả SN17 có đầy đủ tên dụng cụ. Tiêu đề và ghi chú chỉ nói tới vị trí kiểm kê và việc cất sau đó. | Đạt · SN17 | Đạt · SN17 |
| S18 | «tấm nhựa chống trượt hong dựng đứng»<br>Dự án *Trạm quan sát* · Thẻ *Bảo quản* | SN18<br>Nội dung SN18 ghi vật liệu và cách hong dựng đứng. Tiêu đề và mô tả dùng tên chung, SN16 dặn bảo quản vật dụng khác. | Đạt · SN18 | Đạt · SN18 |
| S19 | «Cái chắn gió để kim bàn cân hết lắc và vẫn luồn khay ngang qua ở đâu?»<br>Dự án *Quầy rau cuối tuần* · Chủ đề *Cân đo* | SN19<br>SN19 kê tấm chắn gió để kim cân đứng yên và chừa khe ngang đưa khay. SN20 nói về rèm ở bàn cân bột thuộc dự án bếp bánh. | **Sai** · ∅ | Đạt · SN19 |
| S20 | «Mẫu sơn son gập túi vải để coi vệt đỏ có dính qua bên kia chưa?»<br>Dự án *Gian quà vải* · Thẻ *Thử màu* | SN21<br>SN21 thử gập vải xem màu sơn có in sang mặt đối diện. SN22 trùng vật liệu và màu sơn nhưng là mẫu trưng hàng được đặt mở. | **Sai** · ∅ | Đạt · SN21 |
| S21 | «bóng râm mái tre xe lăn 120 cm»<br>Chủ đề *Vi khí hậu* · Dự án *Sân sinh hoạt* · Thẻ *Có kích thước* | SN23<br>SN23 vừa đo bóng mái tre vừa chừa lối xe lăn 120 cm. SN24 đo bóng nhưng không ghi lối xe lăn, SN25 mô tả lối 150 cm ở vị trí khác. | Đạt · SN23 | Đạt · SN23 |
| S22 | «xe lăn 150 cm»<br>Chủ đề *Tiếp cận công cộng* · Thẻ *Có kích thước* | SN25<br>SN25 ghi 150 cm cho lối cạnh khán đài. SN23 lọt cùng bộ lọc nhưng ghi 120 cm cho lối vòng qua chum nước. | Đạt · SN25 | Đạt · SN25 |
| S23 | «đo bóng râm»<br>Chủ đề *Vi khí hậu* · Thẻ *Đo tại chỗ* | SN23, SN24<br>SN23 đo bóng cho lối và hàng ghế nghỉ, SN24 đo bóng cho chỗ xếp hàng. Cả hai đều ghi quan sát tại sân vào buổi trưa. | Đạt · SN23, SN24 | Đạt · SN23, SN24 |
| S24 | «cháo kê nồi lớn 18 bát men»<br>Thẻ *Khẩu phần* | SN27<br>SN27 ghi nồi lớn chia 18 bát men và gắn thẻ Khẩu phần. SN26 nói về món ăn kèm và danh sách mua. | Đạt · SN27 | Đạt · SN27 |
| S25 | «ruốc nấm ăn với cháo kê»<br>Chủ đề *Bếp tập thể* · Dự án *Bếp đầu ngõ* | SN26<br>Chỉ SN26 ghi món ruốc nấm ăn cùng cháo kê. Cùng dự án và chủ đề, SN27 chỉ nói về chia cháo. | Đạt · SN26 | Đạt · SN26 |
| S26 | «thời hạn đổi cân đóng dấu tròn»<br>Dự án *Bếp đầu ngõ* · Thẻ *Nhà cung cấp* | SN28<br>SN28 có quan hệ với cả dự án quầy rau và bếp đầu ngõ. Nội dung ghi thời hạn đổi cân và dấu tròn của đơn vị gần chợ. | Đạt · SN28 | Đạt · SN28 |
| S27 | «khay đồng mẫu chữ có chân»<br>Dự án *Phố chữ* · Thẻ *Kiểm kê* | SN29<br>SN29 ghi khay đồng chứa mẫu có chân. Bản SN30 cùng bộ chữ địa danh và cùng thẻ nhưng dùng khay gỗ, chứa chữ không chân. | Đạt · SN29 | Đạt · SN29 |
| S28 | «bộ đếm cơ cổng xếp» | SN32<br>SN32 là phiếu giao ca duy nhất dặn cộng bộ đếm cơ sau khi khách qua cổng xếp. | Đạt · SN32 | Đạt · SN32 |
| S29 | «bộ chữ rời nhãn kệ bếp»<br>Dự án *Bếp đầu ngõ* | SN31<br>SN31 dùng chữ rời cao su để in nhãn kệ bếp. Hai khay chữ tại dự án Phố chữ dùng để ghép địa danh. | Đạt · SN31 | Đạt · SN31 |
| S30 | «bộ chữ rời ghép tên phố»<br>Chủ đề *In thủ công* · Dự án *Phố chữ* | SN29, SN30<br>Hai khay chữ đồng và gỗ đều được ghi là bộ dùng ghép tên phố. SN31 dùng cho nhãn kệ bếp, thuộc dự án khác. | Đạt · SN29, SN30 | Đạt · SN29, SN30 |
| S31 | «biên nhận XN702 xuồng nan»<br>Dự án *Nhà thuyền* · Thẻ *Kế toán* | ∅<br>Mã XN702 chỉ có trong SN12 đã xóa mềm. Kho hiện hành không có bản biên nhận nào khác mang mã này. | Đạt · ∅ | Đạt · ∅ |
| S32 | «chìa dự phòng móc số 2»<br>Dự án *Nhà thuyền* · Thẻ *Hướng dẫn* | ∅<br>Vị trí móc số 2 thuộc sổ SN11 đã xóa mềm. Bản đang dùng SN10 quy định móc số 6. | Đạt · ∅ | Đạt · ∅ |
| S33 | «chốt lò xo bằng đồng»<br>Chủ kho *main* · Dự án *Tuần thủ công* · Thẻ *Đã duyệt* | ∅<br>Chốt lò xo bằng đồng thuộc SN09 ở kho guest. Kiểu khung của main dùng đệm nỉ dù hai kho có cùng tên dự án và thẻ. | Đạt · ∅ | Đạt · ∅ |
| S34 | «Tìm cách chừa khe để luồn thẻ tên bức tranh vào khung mica»<br>Chủ kho *guest* · Chủ đề *Trưng bày* · Thẻ *Đã duyệt* | ∅<br>Khe cho thẻ tên tranh chỉ có trong SN08 của main. Phiếu SN09 của guest nói về cách giữ mẫu dệt. | Đạt · ∅ | Đạt · ∅ |
| S35 | «đường gờ chấm bàn giáo viên»<br>Bỏ mục *SN05* · Dự án *Sơ đồ khu phố* · Chủ đề *Tiếp cận công cộng* | ∅<br>SN05 là bản duy nhất mô tả gờ chấm dẫn đến bàn giáo viên, và chính mục này đang bị loại. | Đạt · ∅ | Đạt · ∅ |
| S36 | «cháo kê ruốc nấm»<br>Dự án *Bếp đầu ngõ* · Thẻ *Nhà cung cấp* | ∅<br>Thẻ này có thật trong dự án qua SN28 về cân điện tử. Ghi chú món cháo SN26 chỉ gắn thẻ Thực đơn. | Đạt · ∅ | Đạt · ∅ |
| S37 | «in thử một bộ la bàn»<br>Chủ đề *Giáo dục* · Dự án *Sơ đồ khu phố* · Thẻ *Thực hành* | ∅<br>SN06 có bài la bàn, chủ đề Giáo dục và thẻ Thực hành nhưng ở dự án Tủ học liệu. Trong Sơ đồ khu phố, SN05 cũng có chủ đề Giáo dục nhưng không có thẻ Thực hành. | Đạt · ∅ | Đạt · ∅ |
| S38 | «Rèm chắn gió treo lên trần để giữ kim cân bột khỏi nhảy gần cửa lò»<br>Dự án *Quầy rau cuối tuần* · Thẻ *Thử thiết bị* | ∅<br>Đúng cơ cấu rèm treo và bối cảnh cửa lò thuộc SN20 của Bếp bánh sáng. SN19 đúng bộ lọc nhưng là tấm kê quanh bàn để đưa khay ngang, không có rèm treo. | Đạt · ∅ | **Sai** · SN19 |
| S39 | «kẹp nam châm giữ góc tờ phiếu»<br>Chủ đề *Dụng cụ cầm tay* · Dự án *Trạm quan sát* · Thẻ *Bảo quản* | ∅<br>Mô tả phù hợp nằm trong SN17 có thẻ Kiểm kê. Hai mục Bảo quản cùng dự án nói về ống nhòm và tấm chống trượt. | Đạt · ∅ | Đạt · ∅ |
| S40 | «bóng râm mái tre nhiệt độ 29 độ»<br>Chủ đề *Vi khí hậu* · Dự án *Sân sinh hoạt* | ∅<br>SN23 khảo sát bóng râm mái tre và SN24 khảo sát bóng chỗ xếp hàng, nhưng không ghi nhiệt độ 29 độ hay bất kỳ số đo nhiệt độ nào. | Đạt · ∅ | Đạt · ∅ |
