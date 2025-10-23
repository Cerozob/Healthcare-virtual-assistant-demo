import { Authenticator, type AuthenticatorProps } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

// Header component for the authenticator
function AuthHeader() {
  return (
    <div style={{ textAlign: 'center', padding: '2rem 0' }}>
      <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#232f3e' }}>
        AnyHealthcare Demo
      </h1>
      <p style={{ color: '#687078', marginTop: '0.5rem' }}>
        Inicie sesión para continuar
      </p>
    </div>
  );
}

type SpanishAuthenticatorProps = {
  children: AuthenticatorProps['children'];
};

export function SpanishAuthenticator({ children }: SpanishAuthenticatorProps) {
  return (
    <Authenticator
      formFields={{
        signIn: {
          username: {
            label: 'Correo electrónico',
            placeholder: 'Ingrese su correo electrónico',
          },
          password: {
            label: 'Contraseña',
            placeholder: 'Ingrese su contraseña',
          },
        },
        signUp: {
          email: {
            label: 'Correo electrónico',
            placeholder: 'Ingrese su correo electrónico',
            order: 1,
          },
          password: {
            label: 'Contraseña',
            placeholder: 'Ingrese su contraseña',
            order: 2,
          },
          confirm_password: {
            label: 'Confirmar contraseña',
            placeholder: 'Confirme su contraseña',
            order: 3,
          },
          'custom:fullname': {
            label: 'Nombre completo',
            placeholder: 'Ingrese su nombre completo',
            order: 4,
          },
        },
        forceNewPassword: {
          password: {
            label: 'Nueva contraseña',
            placeholder: 'Ingrese su nueva contraseña',
          },
        },
        confirmResetPassword: {
          confirmation_code: {
            label: 'Código de confirmación',
            placeholder: 'Ingrese el código de confirmación',
          },
          password: {
            label: 'Nueva contraseña',
            placeholder: 'Ingrese su nueva contraseña',
          },
          confirm_password: {
            label: 'Confirmar contraseña',
            placeholder: 'Confirme su nueva contraseña',
          },
        },
        confirmSignUp: {
          confirmation_code: {
            label: 'Código de confirmación',
            placeholder: 'Ingrese el código de confirmación',
          },
        },
      }}
      components={{
        Header: AuthHeader,
      }}
    >
      {children}
    </Authenticator>
  );
}
