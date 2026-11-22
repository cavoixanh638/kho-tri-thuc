# P08/J6B — bằng chứng phụ: kiểm seek MP4 thật trên Chromium (22/11/2026)

## Căn cứ
- PR #89 đã kiểm chứng P08 **11/13 PASS**. J3 và J6B là hai ca NOT_RUN cuối, release G2 vẫn đỏ có chủ ý.
- J6B đòi hỏi **cả** nguồn PDF được định vị đúng trang và MP4 tìm đúng thời điểm trên asset private đã xác minh. Không được coi việc render một iframe/video là bằng chứng.
- Backend `storage/viewer_api.py` hiện trả `pageNavigationVerified: false` với PDF và frontend `SourceLocator.tsx` cố ý không cho định vị khi thiếu bằng chứng. Không thay đổi flag này để tạo PASS giả.

## Phần đã thực hiện
1. Script `tools/smoke/p08_native_media.mjs`: tạo một MP4/H.264 12 giây bằng ffmpeg ngay trong QA runner, tính SHA256; serve riêng trên loopback với cookie HTTP-only, no-store, route gắn phiên bản SHA256, chặn anonymous, 416 range sai, 404 URL stale.
2. Chạy **Chromium thật qua CDP**. Kiểm GET Range `bytes=0-31` nhận 206/Content-Range và đúng 32 bytes. Tạo `HTMLVideoElement`, đợi decode, đòi hỏi sự kiện `seeked`, và kiểm thời gian sau seek tại 6 mốc `[0.125, 1.25, 3.5, 6.25, 8.75, 10.5]` với sai số tối đa 0,5 giây.
3. `p08_attach_media.mjs` đối chiếu proof và gắn `j6b_partial_media` vào báo cáo P08 **mà không hề thay đổi J6B từ NOT_RUN sang PASS**.
4. Tích hợp trong **runner CI browser đã có**, không tạo workflow chạy định kỳ, không gọi Drive/Gemini, không truy cập URL ngoài và không dùng media cá nhân.

## Những điều KHÔNG chứng minh
- Đây là **loopback HTTP fixture**, không phải Django production endpoint hoặc Google Drive readback; toàn bộ media phát sinh tự động, không trích từ video người dùng.
- **Chưa chứng minh PDF chính xác trang nào** và **chưa kiểm hành trình J6B trên UI app thật với hai asset private pinned**. Không đổi `pageNavigationVerified` thành true khi chưa có renderer đáng tin cậy và test trang thực.
- Không có `J6B PASS`, không phát hành. Hai ca J3/J6B vẫn NOT_RUN trong release gate đến khi đạt định nghĩa đầy đủ.

## Evidence và rollback
- Chỉ lưu JSON `p08-j6b-native-media.json`, screenshot `p08-j6b-native-media.png` và ledger P08 trong artifact `kt-p08-real-browser-ledger`. Binary MP4 được xóa sau test.
- Unit `node --test tools/smoke/p08_attach_media.test.mjs`; real CI `node tools/smoke/p08_native_media.mjs`.
- Chỉ dùng repo branch QA; rollback đóng PR. Không đổi runtime, schema, Drive token hay app deployment.

## Chốt trạng thái
- Tại commit tạo checkpoint: **CI chưa có kết quả**, không suy đoán PASS trước khi kiểm Actions đúng HEAD.
