export type ThemeColors = {
  background: string;
  surface: string;
  surfaceElevated: string;
  primary: string;
  onPrimary: string;
  text: string;
  muted: string;
  danger: string;
  border: string;
};

export type Theme = {
  id: string;
  name: string;
  emoji: string;
  isDark: boolean;
  colors: ThemeColors;
};

export const themes: Theme[] = [
  {
    id: "midnight",
    name: "Midnight",
    emoji: "🌙",
    isDark: true,
    colors: {
      background: "#0B0F1A",
      surface: "#151B2B",
      surfaceElevated: "#1E263B",
      primary: "#7C9CFF",
      onPrimary: "#0B0F1A",
      text: "#F4F6FB",
      muted: "#8892B0",
      danger: "#FF6B6B",
      border: "#262E45",
    },
  },
  {
    id: "golden-hour",
    name: "Golden Hour",
    emoji: "🌅",
    isDark: true,
    colors: {
      background: "#1F1408",
      surface: "#2C1D0C",
      surfaceElevated: "#3A2812",
      primary: "#F2A65A",
      onPrimary: "#1F1408",
      text: "#FBF1E6",
      muted: "#C9A585",
      danger: "#FF6B6B",
      border: "#4A3417",
    },
  },
  {
    id: "forest",
    name: "Forest",
    emoji: "🌲",
    isDark: true,
    colors: {
      background: "#0E1A12",
      surface: "#152619",
      surfaceElevated: "#1D3322",
      primary: "#6FCF97",
      onPrimary: "#0E1A12",
      text: "#EAF6EE",
      muted: "#8FB89C",
      danger: "#FF6B6B",
      border: "#22402C",
    },
  },
  {
    id: "ocean",
    name: "Ocean",
    emoji: "🌊",
    isDark: true,
    colors: {
      background: "#081826",
      surface: "#0F2536",
      surfaceElevated: "#153347",
      primary: "#4FC3E8",
      onPrimary: "#081826",
      text: "#EAF7FC",
      muted: "#83AEC0",
      danger: "#FF6B6B",
      border: "#1B4058",
    },
  },
  {
    id: "vintage",
    name: "Vintage",
    emoji: "📜",
    isDark: true,
    colors: {
      background: "#2A2117",
      surface: "#372C1F",
      surfaceElevated: "#443628",
      primary: "#D9A566",
      onPrimary: "#2A2117",
      text: "#F1E7D6",
      muted: "#B7A78E",
      danger: "#E4756A",
      border: "#4F3F2C",
    },
  },
  {
    id: "dreamy",
    name: "Dreamy",
    emoji: "🌸",
    isDark: true,
    colors: {
      background: "#1E1526",
      surface: "#2A1D34",
      surfaceElevated: "#372640",
      primary: "#D9A7F0",
      onPrimary: "#1E1526",
      text: "#F6ECFB",
      muted: "#B79ACB",
      danger: "#FF7A9A",
      border: "#402D4C",
    },
  },
  {
    id: "library",
    name: "Library",
    emoji: "📚",
    isDark: true,
    colors: {
      background: "#1B1712",
      surface: "#25201A",
      surfaceElevated: "#312A21",
      primary: "#C9A26B",
      onPrimary: "#1B1712",
      text: "#F2ECE1",
      muted: "#A99A85",
      danger: "#E4756A",
      border: "#3C3225",
    },
  },
  {
    id: "minimal",
    name: "Minimal",
    emoji: "◻️",
    isDark: false,
    colors: {
      background: "#FFFFFF",
      surface: "#F5F5F7",
      surfaceElevated: "#EDEDF0",
      primary: "#111827",
      onPrimary: "#FFFFFF",
      text: "#111827",
      muted: "#6B7280",
      danger: "#DC2626",
      border: "#E5E7EB",
    },
  },
];

export const defaultTheme = themes[0];

export function getThemeById(id: string): Theme {
  return themes.find((theme) => theme.id === id) ?? defaultTheme;
}
