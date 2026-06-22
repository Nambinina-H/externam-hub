export const DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];

// `items` permet à <SelectValue/> (base-ui) d'afficher le libellé au lieu de la valeur brute.
export const DAY_ITEMS = DAYS.map((label, value) => ({ value: String(value), label }));
