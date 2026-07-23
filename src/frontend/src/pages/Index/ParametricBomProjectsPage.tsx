import { Container } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

/**
 * ParametricBomProjectPage — 项目列表页面。
 *
 * iframe 加载 Django 项目列表页，并拦截点击项目事件，
 * 将父页面的浏览器地址导航到 /web/project/:id/。
 * 延迟加载 iframe 防止 Session 未就绪时闪现登录页。
 */
export default function ParametricBomProjectPage() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [iframeSrc, setIframeSrc] = useState('about:blank');

  useEffect(() => {
    // 延迟加载，等 SPA Session 稳定
    const timer = setTimeout(() => {
      setIframeSrc('/parametric-bom/?embedded=1&page=projects');
    }, 150);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    function patchIframeNavigation() {
      try {
        const win = (iframe as HTMLIFrameElement).contentWindow as any;
        if (!win || typeof win.showProjectDetail !== 'function') return;

        // 重写 iframe 内的 showProjectDetail 函数
        // 当用户点击项目时，让父页面导航到独立详情页
        win.showProjectDetail = function (projectId: number) {
          window.location.href = `/web/project/${projectId}/`;
        };
      } catch (_e) {
        // 同源 iframe 访问失败（不应该发生）
      }
    }

    iframe.addEventListener('load', patchIframeNavigation);
    if (iframe.contentDocument?.readyState === 'complete') {
      patchIframeNavigation();
    }

    return () => {
      iframe.removeEventListener('load', patchIframeNavigation);
    };
  }, [iframeSrc]);

  return (
    <Container size='100%' p={0} style={{ height: 'calc(100vh - 60px)' }}>
      <iframe
        ref={iframeRef}
        src={iframeSrc}
        style={{
          width: '100%',
          height: '100%',
          border: 'none'
        }}
        title='项目管理'
      />
    </Container>
  );
}
