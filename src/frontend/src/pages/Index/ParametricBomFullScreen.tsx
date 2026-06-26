import { Navigate } from 'react-router-dom';

import { useUserState } from '../../states/UserState';

export default function ParametricBomFullScreen() {
  const { isLoggedIn } = useUserState();

  if (!isLoggedIn()) {
    return <Navigate to='/logged-in' />;
  }

  return (
    <iframe
      src='/parametric-bom/?embedded=1&page=products'
      style={{
        width: '100%',
        height: '100vh',
        border: 'none'
      }}
      title='参数化BOM'
    />
  );
}
