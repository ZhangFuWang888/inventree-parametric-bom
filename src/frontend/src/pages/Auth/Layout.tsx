import { StylishText } from '@lib/components/StylishText';
import { Trans } from '@lingui/react/macro';
import {
  Button,
  Center,
  Container,
  Divider,
  Group,
  Loader,
  Paper,
  Stack,
  Text
} from '@mantine/core';
import { Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import SplashScreen from '../../components/SplashScreen';
import { doLogout } from '../../functions/auth';
import { api } from '../../App';
import { apiUrl } from '@lib/functions/Api';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';

export default function LoginLayoutComponent() {
  return (
    <SplashScreen>
      <div
        style={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #f0f9ff 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1.5rem'
        }}
      >
        <Container>
          <Outlet />
        </Container>
      </div>
    </SplashScreen>
  );
}

export function Wrapper({
  children,
  titleText,
  logOff = false,
  loader = false,
  smallPadding = false
}: Readonly<{
  children?: React.ReactNode;
  titleText: string;
  logOff?: boolean;
  loader?: boolean;
  smallPadding?: boolean;
}>) {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState('');

  useEffect(() => {
    api
      .get(apiUrl(ApiEndpoints.api_server_info))
      .then((response) => {
        const company = response.data?.customize?.company_name;
        if (company) setCompanyName(company);
      })
      .catch(() => {});
  }, []);

  return (
    <Paper
      p='xl'
      withBorder
      miw={425}
      shadow='xl'
      radius='md'
      style={{
        borderColor: '#e2e8f0'
      }}
    >
        <Stack gap={smallPadding ? 0 : 'md'}>
          {/* Company Branding */}
          {companyName && (
            <div style={{ textAlign: 'center', marginBottom: '0.75rem' }}>
              <Text
                size='24px'
                fw={700}
                c='#1e293b'
                style={{ letterSpacing: '0.02em' }}
              >
                🏭 {companyName}
              </Text>
              <Text size='sm' c='#64748b' mt={4}>
                参数化BOM管理系统
              </Text>
            </div>
          )}
          {!companyName && (
            <div style={{ textAlign: 'center', marginBottom: '0.75rem' }}>
              <Text size='sm' c='#64748b' mt={4}>
                参数化BOM管理系统
              </Text>
            </div>
          )}
          <Divider p='xs' />
          {loader && (
            <Group justify='center'>
              <Loader />
            </Group>
          )}
          {children}
          {logOff && (
            <>
              <Divider p='xs' />
              <Button onClick={() => doLogout(navigate)} color='red'>
                <Trans>Log off</Trans>
              </Button>
            </>
          )}
          {/* Footer */}
          {companyName && (
            <Text ta='center' size='10px' c='#94a3b8' mt='sm'>
              © 2026 {companyName}
            </Text>
          )}
        </Stack>
      </Paper>
  );
}
