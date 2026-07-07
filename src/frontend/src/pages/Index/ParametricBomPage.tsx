import { Container } from '@mantine/core';
import { useSearchParams } from 'react-router-dom';

export default function ParametricBomPage() {
  const [searchParams] = useSearchParams();
  const page = searchParams.get('page') || 'products';
  const iframeSrc = `/parametric-bom/?embedded=1&page=${encodeURIComponent(page)}`;

  return (
    <Container size='100%' p={0} style={{ height: 'calc(100vh - 60px)' }}>
      <iframe
        src={iframeSrc}
        style={{
          width: '100%',
          height: '100%',
          border: 'none'
        }}
        title='参数化BOM'
      />
    </Container>
  );
}
