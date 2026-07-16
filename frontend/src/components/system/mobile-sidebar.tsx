"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import type { FrontendHealthResponse } from "@/lib/api/types";
import type { PublicAppEnvironment } from "@/lib/environment";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { AppSidebar } from "./app-sidebar";

export function MobileSidebar({
  health,
  app,
}: {
  health: FrontendHealthResponse;
  app: PublicAppEnvironment;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={<Button variant="ghost" size="icon" aria-label="Open navigation" />}
      >
        <Menu aria-hidden="true" size={20} strokeWidth={1.75} />
      </SheetTrigger>
      <SheetContent
        side="left"
        showCloseButton
        className="w-[min(100vw,320px)] border-r-0 bg-navy-800 p-0 text-white shadow-sm sm:max-w-[320px]"
      >
        <SheetTitle className="sr-only">PolicyGPT navigation</SheetTitle>
        <SheetDescription className="sr-only">
          Navigate the Evidence Intelligence Console.
        </SheetDescription>
        <AppSidebar
          health={health}
          app={app}
          mobile
          onNavigate={() => setOpen(false)}
        />
      </SheetContent>
    </Sheet>
  );
}
