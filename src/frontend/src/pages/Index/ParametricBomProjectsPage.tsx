import { Container } from '@mantine/core';

export default function ParametricBomProjectPage() {
  return (
    <Container size='100%' p={0} style={{ height: 'calc(100vh - 60px)' }}>
      <iframe
        src='/parametric-bom/?embedded=1&page=projects'
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
