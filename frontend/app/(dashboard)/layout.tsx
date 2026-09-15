"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { toast } from "sonner";

import { useAuth } from "@/features/auth/context/auth-context";
import { DashboardNav } from "@/features/dashboard/components/dashboard-nav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;

    if (window.sessionStorage.getItem("trend-intelligence-auth-notice") === "welcome-back") {
      window.sessionStorage.removeItem("trend-intelligence-auth-notice");
      toast.success("Welcome back.");
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        Loading...
      </div>
    );
  }

  return (
    <div className="relative flex flex-1">
      <div className="dashboard-backdrop" aria-hidden="true" />
      <div className="relative z-10 flex flex-1">
        <DashboardNav />
        <div className="flex flex-1 flex-col overflow-x-hidden pb-16 md:pb-0">{children}</div>
      </div>
    </div>
  );
}
