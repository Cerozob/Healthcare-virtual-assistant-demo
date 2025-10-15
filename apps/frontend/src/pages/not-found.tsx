import {
  Alert,
  BreadcrumbGroup,
  Container,
  ContentLayout,
  Header,
  SpaceBetween,
  Button,
} from "@cloudscape-design/components";
import { useOnFollow } from "../common/hooks/use-on-follow";
import BaseAppLayout from "../components/base-app-layout";

export default function NotFound() {
  const onFollow = useOnFollow();

  return (
    <BaseAppLayout
      breadcrumbs={
        <BreadcrumbGroup
          onFollow={onFollow}
          items={[
            {
              text: "Sistema de Salud",
              href: "/",
            },
            {
              text: "Página No Encontrada",
              href: "/not-found",
            },
          ]}
          expandAriaLabel="Mostrar ruta"
          ariaLabel="Migas de pan"
        />
      }
      content={
        <ContentLayout
          header={<Header variant="h1">Página No Encontrada</Header>}
        >
          <SpaceBetween size="l">
            <Container>
              <Alert 
                type="error" 
                header="Página No Encontrada"
                action={
                  <Button 
                    onClick={() => window.location.href = '/'}
                    variant="primary"
                  >
                    Ir al Inicio
                  </Button>
                }
              >
                La página que buscas no existe.
              </Alert>
            </Container>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}
