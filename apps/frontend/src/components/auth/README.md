# Componentes de Autenticación

Este directorio contiene los componentes relacionados con la autenticación de usuarios.

## Componentes

### SpanishAuthenticator

Wrapper personalizado del componente `Authenticator` de AWS Amplify con traducciones en español.

#### Características

- Traducciones completas en español latinoamericano
- Campos de formulario personalizados con etiquetas en español
- Encabezado personalizado con branding del sistema
- Integración completa con AWS Amplify Auth

#### Uso

```typescript
import { SpanishAuthenticator } from './components/auth';

function App() {
  return (
    <SpanishAuthenticator>
      {({ signOut, user }) => (
        <div>
          <p>Bienvenido, {user?.username}</p>
          <button onClick={signOut}>Cerrar sesión</button>
        </div>
      )}
    </SpanishAuthenticator>
  );
}
```

#### Campos de Formulario

**Inicio de Sesión:**
- Correo electrónico
- Contraseña

**Registro:**
- Correo electrónico
- Contraseña
- Confirmar contraseña
- Nombre completo

**Restablecer Contraseña:**
- Código de confirmación
- Nueva contraseña
- Confirmar contraseña

## Configuración

La autenticación está configurada en `amplify/auth/resource.ts` con las siguientes opciones:

- Inicio de sesión con correo electrónico
- Atributos de usuario: email (requerido), fullname (requerido)
- Recuperación de cuenta: solo por correo electrónico
- MFA: deshabilitado

## Personalización

Para personalizar las traducciones o el estilo:

1. Edite `SpanishAuthenticator.tsx`
2. Modifique los campos en la propiedad `formFields`
3. Actualice el componente `AuthHeader` para cambiar el encabezado
4. Use CSS personalizado para estilos adicionales (ver `styles/global.css`)
