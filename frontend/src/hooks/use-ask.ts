"use client";

import { useAskWorkspaceContext } from "@/components/ask/ask-workspace-provider";

export type { AskWorkspaceState } from "@/lib/domain/ask-workspace";

export function useAsk() {
  return useAskWorkspaceContext();
}
