import { Button } from '@mantine/core';
import { useState } from 'react';
import { request, type DriveStatus } from './api';
import { ErrorNotice, Loading, PageTitle, useResource } from './views';

const driveStates: Record<string, string> = {
  connected: 'Đã kết nối',
  not_configured: 'Chưa cấu hình Google Drive trên máy chủ',
  not_connected: 'Chưa kết nối',
  reauthorize: 'Cần kết nối lại',
};

export function SettingsScreen({ csrf, driveResult, username }: { csrf: string; driveResult?: string; username: string | null }) {
  const drive = useResource<DriveStatus>('/integrations/drive/status');
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState(false);

  async function connect() {
    setConnecting(true);
    setError(false);
    try {
      const result = await request<{ authorization_url: string }>('/integrations/drive/connect', { method: 'POST', csrf });
      const url = new URL(result.authorization_url);
      if (url.origin !== 'https://accounts.google.com' || url.username || url.password) throw new Error('Invalid authorization URL');
      window.location.assign(url.href);
    } catch {
      setError(true);
      setConnecting(false);
    }
  }

  return <>
    <PageTitle title="Cài đặt" />
    <section className="settings-row" aria-labelledby="drive-title">
      <div>
        <h2 id="drive-title">Google Drive</h2>
        <p className="section-note">Kết nối tài khoản dùng để lưu các tệp gốc.</p>
      </div>
      <div className="panel">
        {driveResult && driveResult !== 'connected' && <ErrorNotice>Chưa kết nối được Google Drive. Bạn có thể thử lại.</ErrorNotice>}
        {drive.error ? <ErrorNotice retry={drive.retry}>Chưa kiểm tra được kết nối Google Drive.</ErrorNotice>
          : !drive.data ? <Loading />
            : <>
              <dl className="key-value">
                <div><dt>Kết nối</dt><dd>{(Object.hasOwn(driveStates, drive.data.state) && driveStates[drive.data.state]) || 'Cần kiểm tra lại'}</dd></div>
                {drive.data.display_name && <div><dt>Tài khoản Drive</dt><dd>{drive.data.display_name}</dd></div>}
              </dl>
              {drive.data.state !== 'not_configured' && <div className="form-actions">
                <Button variant={drive.data.state === 'connected' ? 'default' : 'filled'} loading={connecting} onClick={() => void connect()}>
                  {drive.data.state === 'not_connected' ? 'Kết nối Google Drive' : 'Kết nối lại'}
                </Button>
              </div>}
            </>}
        {error && <ErrorNotice>Chưa mở được trang kết nối Google Drive. Hãy thử lại.</ErrorNotice>}
      </div>
    </section>
    <section className="settings-row" aria-labelledby="account-title">
      <h2 id="account-title">Tài khoản</h2>
      <div className="panel">
        <dl className="key-value"><div><dt>Tên đăng nhập</dt><dd>{username || '—'}</dd></div></dl>
      </div>
    </section>
  </>;
}
