import { Button, Menu, PasswordInput, TextInput } from '@mantine/core';
import { useEffect, useState, type SubmitEvent } from 'react';
import { ApiError, request, SESSION_EXPIRED_EVENT, type Session } from './api';
import { CaptureScreen } from './CaptureScreen';
import { HistoryScreen } from './HistoryScreen';
import { ItemScreen } from './ItemScreen';
import { LibraryScreen } from './LibraryScreen';
import { SearchScreen } from './SearchScreen';
import { SettingsScreen } from './SettingsScreen';
import { KnowledgeCommandPalette } from './KnowledgeCommandPalette';
import { ErrorNotice, Loading, PageTitle } from './views';

const links = [
  { path: '#/gui', label: 'Gửi vào kho' },
  { path: '#/lich-su', label: 'Lịch sử' },
  { path: '#/thu-vien', label: 'Thư viện' },
  { path: '#/tim-kiem', label: 'Tìm kiếm' },
  { path: '#/cai-dat', label: 'Cài đặt' },
];

function Brand() {
  return <a className="brand" href="#/gui"><span className="brand-mark" aria-hidden="true" />Kho Tri Thức</a>;
}

function Header({ path, username, onLogout, signingOut }: {
  path: string;
  username?: string | null;
  onLogout?: () => void;
  signingOut: boolean;
}) {
  const active = path.startsWith('#/muc/') ? '#/thu-vien' : path.split('?', 1)[0];
  return <header className="site-header">
    <div className="shell header-inner">
      <Brand />
      {onLogout && <>
        <nav className="desktop-nav" aria-label="Điều hướng chính">
          {links.map((link) => <a key={link.path} href={link.path} aria-current={link.path === active ? 'page' : undefined}>{link.label}</a>)}
        </nav>
        <div className="account">
          <span>{username}</span>
          <Button variant="subtle" size="compact-sm" loading={signingOut} onClick={onLogout}>Đăng xuất</Button>
        </div>
        <div className="mobile-nav">
          <Menu position="bottom-end" width={205}>
            <Menu.Target><Button variant="default" size="compact-sm">Điều hướng</Button></Menu.Target>
            <Menu.Dropdown>
              {links.map((link) => <Menu.Item component="a" href={link.path} key={link.path} aria-current={link.path === active ? 'page' : undefined}>{link.label}</Menu.Item>)}
              <Menu.Divider />
              <Menu.Item disabled={signingOut} onClick={onLogout}>Đăng xuất</Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </div>
      </>}
    </div>
  </header>;
}

function Login({ csrf, onLogin }: { csrf: string; onLogin: (session: Session) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(undefined);
    try {
      const session = await request<Session>('/session', { method: 'POST', csrf, body: { username, password } });
      onLogin(session);
    } catch (error) {
      setError(error instanceof ApiError && error.status === 401
        ? 'Tên đăng nhập hoặc mật khẩu chưa đúng.'
        : 'Chưa đăng nhập được. Hãy thử lại.');
    } finally {
      setBusy(false);
    }
  }

  return <div className="login-panel">
    <PageTitle title="Đăng nhập" description="Mở thư viện cá nhân của bạn." />
    <section className="panel">
      <form className="form-stack" onSubmit={submit}>
        <TextInput label="Tên đăng nhập" autoComplete="username" value={username} required disabled={busy}
          onChange={(event) => setUsername(event.currentTarget.value)} />
        <PasswordInput label="Mật khẩu" autoComplete="current-password" value={password} required disabled={busy}
          onChange={(event) => setPassword(event.currentTarget.value)} />
        {error && <ErrorNotice>{error}</ErrorNotice>}
        <div className="form-actions"><Button type="submit" loading={busy}>Đăng nhập</Button></div>
      </form>
    </section>
  </div>;
}

function activePath() {
  return window.location.hash || '#/gui';
}

export function App() {
  const [path, setPath] = useState(activePath);
  const [driveResult, setDriveResult] = useState<string>();
  const [session, setSession] = useState<Session>();
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  const [signingOut, setSigningOut] = useState(false);
  const [logoutError, setLogoutError] = useState(false);

  useEffect(() => {
    const url = new URL(window.location.href);
    const drive = url.searchParams.get('drive');
    if (drive) {
      url.searchParams.delete('drive');
      url.hash = '#/cai-dat';
      window.history.replaceState(null, '', url.href);
      setDriveResult(drive);
      setPath(url.hash);
    }

    function handleLocation() {
      setPath(activePath());
      window.scrollTo(0, 0);
    }

    function checkSession() {
      setSession(undefined);
      setRevision((value) => value + 1);
    }

    window.addEventListener('hashchange', handleLocation);
    window.addEventListener(SESSION_EXPIRED_EVENT, checkSession);
    return () => {
      window.removeEventListener('hashchange', handleLocation);
      window.removeEventListener(SESSION_EXPIRED_EVENT, checkSession);
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void request<Session>('/session', { signal: controller.signal }).then(
      (data) => { if (!controller.signal.aborted) setSession(data); },
      () => { if (!controller.signal.aborted) setFailed(true); },
    );
    return () => controller.abort();
  }, [revision]);

  async function logout() {
    if (!session || signingOut) return;
    setSigningOut(true);
    setLogoutError(false);
    try {
      const result = await request<Session>('/session', { method: 'DELETE', csrf: session.csrf_token });
      setSession(result);
      setDriveResult(undefined);
      window.location.hash = '#/gui';
    } catch {
      setLogoutError(true);
    } finally {
      setSigningOut(false);
    }
  }

  const itemId = /^#\/muc\/([a-f\d-]{36})$/i.exec(path)?.[1];
  const authenticated = session?.authenticated === true;

  return <>
    <Header path={path} username={session?.username} onLogout={authenticated ? () => void logout() : undefined} signingOut={signingOut} />
    <main className="shell canvas">
      {authenticated && <KnowledgeCommandPalette currentItemId={itemId} onAction={(action) => {
        if (action === 'day') window.location.hash = '#/thu-vien?view=timeline';
        else if (action === 'create') {
          if (path.startsWith('#/thu-vien')) window.dispatchEvent(new CustomEvent('knowledge-command', { detail: { action } }));
          else window.location.hash = '#/gui';
        } else if (itemId) window.dispatchEvent(new CustomEvent('knowledge-command', { detail: { action, itemId } }));
        else window.location.hash = '#/thu-vien';
      }} />}
      {logoutError && <ErrorNotice retry={() => void logout()}>Chưa đăng xuất được.</ErrorNotice>}
      {!session && <>
        <PageTitle title="Kho Tri Thức" />
        <section className="panel">
          {failed ? <ErrorNotice retry={() => {
            setFailed(false);
            setRevision((value) => value + 1);
          }}>Chưa kết nối được với máy chủ.</ErrorNotice> : <Loading label="Đang kiểm tra phiên đăng nhập" />}
        </section>
      </>}
      {session && !authenticated && <Login csrf={session.csrf_token} onLogin={setSession} />}
      {session && authenticated && (itemId ? <ItemScreen id={itemId} csrf={session.csrf_token} key={itemId} />
        : path === '#/lich-su' ? <HistoryScreen />
          : path.split('?', 1)[0] === '#/thu-vien' ? <LibraryScreen csrf={session.csrf_token} />
            : path.split('?', 1)[0] === '#/tim-kiem' ? <SearchScreen path={path} key={path} />
              : path === '#/cai-dat' ? <SettingsScreen csrf={session.csrf_token} driveResult={driveResult} username={session.username} />
                : <CaptureScreen csrf={session.csrf_token} />)}
    </main>
  </>;
}
