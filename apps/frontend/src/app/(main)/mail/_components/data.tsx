import { FileText, type LucideIcon, Send } from "lucide-react";

export type MailNavItem = {
  id: string;
  title: string;
  label?: string;
  icon: LucideIcon;
};

type MailNavigation = {
  navMain: MailNavItem[];
};

export const mailNavigation: MailNavigation = {
  navMain: [
    { id: "sent", title: "Boîte d'envoi", icon: Send },
    { id: "templates", title: "Modèles", icon: FileText },
  ],
};
