import { Container } from '@mantine/core';

export default function ParametricBomPage() {
  return (
    <Container size='100%' p={0} style={{ height: 'calc(100vh - 60px)' }}>
      <iframe
        src='/parametric-bom/?embedded=1&page=products'
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
