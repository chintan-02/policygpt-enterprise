import { EvaluationNavigation } from "@/components/system/evaluation-navigation";

export default function EvaluationsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <EvaluationNavigation />
      {children}
    </>
  );
}
