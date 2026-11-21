import { Button } from '@mantine/core';
import { useEffect, useState } from 'react';
import { request } from './api';
import { ErrorNotice, Loading, useResource } from './views';

type ModelRow = {
  model_id: string;
  display_name: string;
  reviewed_for_ocr: boolean;
  listed_in_last_snapshot: boolean;
  generation_supported: boolean;
  category: string;
  quota_status: string;
};
type Catalog = {
  configured: boolean;
  ocr_enabled: boolean;
  premium_models_enabled: boolean;
  last_success_at: string | null;
  last_error_code: string;
  new_models_last_scan: number;
  mode: 'economy' | 'balanced' | 'quality' | 'manual';
  manual_model_id: string;
  automatic_candidate: string | null;
  automatic_status: string;
  models: ModelRow[];
  usage: {
    today_local_requests: number;
    today_input_tokens: number;
    today_output_tokens: number;
    provider_remaining_requests: null;
    provider_remaining_tokens: null;
  };
};
type Mode = Catalog['mode'];

export function GeminiModelPanel({ csrf }: { csrf: string }) {
  const registry = useResource<Catalog>('/integrations/gemini/models');
  const [mode, setMode] = useState<Mode>('balanced');
  const [manual, setManual] = useState('');
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(false);
  const data = registry.data;

  useEffect(() => {
    if (data && !pending) {
      setMode(data.mode);
      setManual(data.manual_model_id);
    }
  }, [data?.mode, data?.manual_model_id]);

  async function save() {
    setPending(true);
    setSaved(false);
    setError(false);
    try {
      await request('/integrations/gemini/preferences', {
        method: 'POST', csrf, body: {
          mode,
          manual_model_id: mode === 'manual' ? manual : '',
        },
      });
      setSaved(true);
      registry.retry();
    } catch {
      setError(true);
    } finally {
      setPending(false);
    }
  }

  const approved = (data?.models ?? []).filter(model =>
    model.reviewed_for_ocr &&
    model.listed_in_last_snapshot &&
    model.generation_supported &&
    (data?.premium_models_enabled || model.category !== 'premium'));
  const newModels = (data?.models ?? []).filter(model => !model.reviewed_for_ocr);
  return <div className="panel gemini-settings" aria-label="Cài đặt model Gemini OCR">
    {registry.error ? <ErrorNotice retry={registry.retry}>Không tải được cấu hình model Gemini.</ErrorNotice> :
      !data ? <Loading /> : <>
        <dl className="key-value">
          <div><dt>Trạng thái</dt><dd>{!data.configured ? 'Chưa cấu hình API key trên máy chủ' :
            !data.ocr_enabled ? 'Đã có API key; chưa bật xử lý OCR' : 'Đã bật xử lý OCR'}</dd></div>
          <div><dt>Danh mục model</dt><dd>{data.last_success_at ?
            'Đồng bộ gần nhất ' + new Date(data.last_success_at).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
            : 'Chưa đồng bộ'}</dd></div>
          {data.last_error_code && <div><dt>Đồng bộ</dt><dd>Cần thử lại ({data.last_error_code})</dd></div>}
          <div><dt>Đề xuất hiện tại</dt><dd>{data.automatic_candidate ?? 'Chưa có model sẵn sàng'}</dd></div>
        </dl>

        <div className="gemini-choice">
          <label htmlFor="gemini-mode">Chế độ lựa chọn model</label>
          <select id="gemini-mode" value={mode} disabled={pending} onChange={event => {
            setMode(event.currentTarget.value as Mode); setSaved(false);
          }}>
            <option value="balanced">Tự động — cân bằng (khuyên dùng)</option>
            <option value="economy">Tiết kiệm — ưu tiên Flash-Lite</option>
            <option value="quality">Chất lượng cao — ảnh và bảng phức tạp</option>
            <option value="manual">Thủ công — khóa một model</option>
          </select>
          {mode === 'manual' && <>
            <label htmlFor="gemini-manual-model">Model cố định</label>
            <select id="gemini-manual-model" value={manual} disabled={pending}
              onChange={event => { setManual(event.currentTarget.value); setSaved(false); }}>
              <option value="">Chọn model đã kiểm chứng</option>
              {approved.map(model => <option key={model.model_id} value={model.model_id}>
                {model.display_name} ({model.model_id})
              </option>)}
            </select>
            <p className="section-note">Chế độ thủ công không tự chuyển sang model khác khi gặp giới hạn.</p>
          </>}
          <div className="form-actions">
            <Button loading={pending} onClick={() => void save()}
              disabled={mode === 'manual' && !manual}>Lưu lựa chọn</Button>
            <Button variant="default" onClick={registry.retry}>Cập nhật màn hình</Button>
          </div>
          {saved && <p role="status">Đã lưu chế độ chọn model.</p>}
          {error && <ErrorNotice>Không lưu được lựa chọn hoặc model chưa được duyệt.</ErrorNotice>}
        </div>

        <p className="section-note">Đã ghi nhận tại máy chủ hôm nay: {data.usage.today_local_requests} lượt; {data.usage.today_input_tokens} token đầu vào và {data.usage.today_output_tokens} token đầu ra. Đây là số liệu nội bộ, không phải hạn mức Google còn lại.</p>
        <p className="section-note">Tự động kiểm tra danh mục khoảng 12 giờ/lần khi có API key. Model mới phải qua kiểm thử OCR tiếng Việt và xác nhận chi phí trước khi được sử dụng. Không tự động chuyển lên model giá cao nếu chưa được phép.</p>
        {newModels.length > 0 && <details>
          <summary>{newModels.length} model mới hoặc chưa đánh giá</summary>
          <ul>{newModels.slice(0, 30).map(row => <li key={row.model_id}>
            {row.display_name} — chưa phê duyệt cho OCR
          </li>)}</ul>
        </details>}
        <p className="section-note">
          <a href="https://aistudio.google.com/rate-limit" target="_blank" rel="noreferrer">Xem hạn mức thực trên Google AI Studio</a>
          {' · '}
          <a href="https://ai.google.dev/gemini-api/docs/deprecations" target="_blank" rel="noreferrer">Lịch ngừng model</a>
        </p>
      </>}
  </div>;
}
