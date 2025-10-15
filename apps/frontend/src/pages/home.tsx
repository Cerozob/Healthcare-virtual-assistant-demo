import { TextContent, SpaceBetween, Box } from "@cloudscape-design/components";
import BaseAppLayout from "../components/base-app-layout";

export default function HomePage() {

  return (
    <BaseAppLayout
      content={
        <SpaceBetween size="l">
          <TextContent>
            <h1>Página de Inicio</h1>
            <Box variant="h2">Bienvenido al Sistema de Salud</Box>
            <p>Su plataforma segura de gestión de salud</p>
          </TextContent>
        </SpaceBetween>
      }
    />
  );
}
