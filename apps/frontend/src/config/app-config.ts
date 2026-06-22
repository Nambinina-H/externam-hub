import packageJson from "../../package.json";

const currentYear = new Date().getFullYear();

export const APP_CONFIG = {
  name: "Externam Studio Hub",
  logo: "/logo.png",
  version: packageJson.version,
  copyright: `© ${currentYear}, Externam Studio Hub.`,
  meta: {
    title: "Externam Studio Hub",
    description: "Automatisation de scripts et gestion des ads Meta (rapports hebdomadaires aux clients).",
  },
};
