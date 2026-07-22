import { Container, Loader } from '@mantine/core';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useUserState } from '../../states/UserState';

/**
 * ParametricBomProjectDetailPage — 项目详情独立页面。
 *
 * 使用 SPA 的用户状态确认登录后再加载 iframe，避免闪现登录页。
 * 路由: /web/project/:id/
 */
export default function ParametricBomProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const userState = useUserState();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // 等待 SPA 认证完成后再加载 iframe
    if (userState.isLoggedIn()) {
      setReady(true);
    }
  }, [userState.isLoggedIn()]);

  if (!ready) {
    return (
      <Container size='100%' p={0} style={{ height: 'calc(100vh - 60px)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const iframeSrc = `/parametric-bom/projects/${id}/?embedded=1`;

  return (
    <Container size='100%' p={0} style={{ height: 'calc(100vh - 60px)' }}>
      <iframe
        src={iframeSrc}
        style={{
          width: '100%',
          height: '100%',
          border: 'none'
        }}
        title='项目详情'
      />
    </Container>
  );
}
