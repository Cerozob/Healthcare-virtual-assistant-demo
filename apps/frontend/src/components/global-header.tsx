import { useState } from "react";
import { Container, TopNavigation } from "@cloudscape-design/components";
import type { TopNavigationProps } from "@cloudscape-design/components";
import { Mode } from "@cloudscape-design/global-styles";
import { StorageHelper } from "../common/helpers/storage-helper";

export default function GlobalHeader() {
  const [theme, setTheme] = useState<Mode>(StorageHelper.getTheme());

  const onChangeThemeClick = () => {
    if (theme === Mode.Dark) {
      setTheme(StorageHelper.applyTheme(Mode.Light));
    } else {
      setTheme(StorageHelper.applyTheme(Mode.Dark));
    }
  };

  const utilities: TopNavigationProps.Utility[] = [
    {
      type: "button",
      text: theme === Mode.Dark ? "Modo Claro" : "Modo Oscuro",
      onClick: onChangeThemeClick,
    },
  ];

  return (
    <Container>
      <TopNavigation
        identity={{
          href: "/",
          title: "Sistema de Salud",
          logo: { src: "/images/logo.png", alt: "Sistema de Salud Logo" },
        }}
        utilities={utilities}
        i18nStrings={{
          searchIconAriaLabel: "Buscar",
          searchDismissIconAriaLabel: "Cerrar búsqueda",
          overflowMenuTriggerText: "Más opciones",
        }}
      />
    </Container>



  );
}
