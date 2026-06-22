import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";

// Police = Geist (le défaut du template) via le package LOCAL `geist` : la police est embarquée,
// donc aucun fetch Google au build → chargement fiable en dev comme en prod (rendu identique à Vercel).
// Variables : GeistSans -> --font-geist-sans, GeistMono -> --font-geist-mono.

export const fontRegistry = {
  geist: {
    label: "Geist",
    font: GeistSans,
  },
  geistMono: {
    label: "Geist Mono",
    font: GeistMono,
  },
} as const;

export type FontKey = keyof typeof fontRegistry;

export const fontVars = (Object.values(fontRegistry) as Array<(typeof fontRegistry)[FontKey]>)
  .map((f) => f.font.variable)
  .join(" ");

export const fontOptions = (Object.entries(fontRegistry) as Array<[FontKey, (typeof fontRegistry)[FontKey]]>).map(
  ([key, f]) => ({
    key,
    label: f.label,
    variable: f.font.variable,
  }),
);
