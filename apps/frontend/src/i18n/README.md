# Internacionalización (i18n)

Este directorio contiene los archivos de localización para la aplicación.

## Estructura

- `es.ts` - Traducciones en español latinoamericano
- `index.ts` - Exportaciones principales

## Uso

### En Componentes

```typescript
import { useLanguage } from '../contexts/LanguageContext';

function MyComponent() {
  const { t } = useLanguage();
  
  return (
    <div>
      <h1>{t.common.loading}</h1>
      <button>{t.common.save}</button>
    </div>
  );
}
```

### Agregar Nuevas Traducciones

1. Abra `es.ts`
2. Agregue las nuevas claves en la sección apropiada
3. Las traducciones estarán disponibles automáticamente a través del hook `useLanguage`

## Convenciones

- Use español latinoamericano (es-MX)
- Mantenga las traducciones organizadas por categoría
- Use nombres de claves descriptivos en inglés
- Incluya contexto cuando sea necesario para traducciones ambiguas

## Categorías Actuales

- `auth` - Autenticación y autorización
- `nav` - Navegación
- `common` - Elementos comunes de UI
- `errors` - Mensajes de error
- `chat` - Interfaz de chat
- `patient` - Información de pacientes
- `exam` - Exámenes médicos
- `config` - Configuración
- `fileUpload` - Carga de archivos
- `notifications` - Notificaciones
- `validation` - Mensajes de validación
