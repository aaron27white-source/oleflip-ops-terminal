export const money = (n: number | null | undefined): string =>
  n === null || n === undefined ? "—" : `$${n.toFixed(2)}`;

export const percent = (n: number | null | undefined): string =>
  n === null || n === undefined ? "—" : `${Math.round(n)}%`;
