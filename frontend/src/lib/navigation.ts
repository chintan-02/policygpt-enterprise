import {
  Activity,
  BookOpenText,
  FileStack,
  Gauge,
  MessageSquareText,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export type NavigationItemDefinition = {
  label: string;
  href: string;
  icon: LucideIcon;
  matchPrefix?: string;
};

export type NavigationGroup = {
  label: string;
  items: NavigationItemDefinition[];
};

export const navigationGroups: NavigationGroup[] = [
  {
    label: "Workspace",
    items: [
      { label: "Overview", href: "/", icon: Gauge },
      { label: "Documents", href: "/documents", icon: FileStack },
      { label: "Ask PolicyGPT", href: "/ask", icon: MessageSquareText },
    ],
  },
  {
    label: "Quality",
    items: [
      {
        label: "Evaluations",
        href: "/evaluations/overview",
        icon: ShieldCheck,
        matchPrefix: "/evaluations",
      },
    ],
  },
  {
    label: "Platform",
    items: [{ label: "System", href: "/system", icon: Activity }],
  },
];

export const evaluationNavigation = [
  { label: "Overview", href: "/evaluations/overview" },
  { label: "Cases", href: "/evaluations/cases" },
  { label: "Confidence", href: "/evaluations/confidence" },
  { label: "Provider", href: "/evaluations/provider" },
  { label: "Run details", href: "/evaluations/runs/latest" },
];

export const pageBreadcrumbs: Record<
  string,
  { section: string; page: string }
> = {
  "/": { section: "Workspace", page: "Overview" },
  "/documents": { section: "Workspace", page: "Documents" },
  "/ask": { section: "Workspace", page: "Ask PolicyGPT" },
  "/evaluations/overview": {
    section: "Quality",
    page: "Evaluation overview",
  },
  "/evaluations/cases": { section: "Quality", page: "Cases" },
  "/evaluations/confidence": { section: "Quality", page: "Confidence" },
  "/evaluations/provider": { section: "Quality", page: "Provider" },
  "/evaluations/runs/latest": { section: "Quality", page: "Run details" },
  "/system": { section: "Platform", page: "System" },
};

export const architectureSteps = [
  { label: "Documents", icon: BookOpenText },
  { label: "Extract & chunk", icon: FileStack },
  { label: "Vector index", icon: Activity },
  { label: "Calibrate evidence", icon: Gauge },
  { label: "Answer or fallback", icon: ShieldCheck },
  { label: "Cite & trace", icon: MessageSquareText },
];
