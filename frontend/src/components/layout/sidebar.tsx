"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  BarChart3, 
  BrainCircuit, 
  Target, 
  Zap, 
  Activity, 
  Settings,
  LayoutDashboard,
  Megaphone,
  Box,
  MonitorPlay,
  Waypoints,
  TrendingUp,
  History,
  FileText
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Campaigns", href: "/analytics/campaigns", icon: Megaphone },
  { name: "Products", href: "/analytics/products", icon: Box },
  { name: "Customers", href: "/analytics/customers", icon: Target },
  { name: "Opportunities", href: "/ai/opportunities", icon: Zap },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Journey", href: "/analytics/journey", icon: Waypoints },
  { name: "AI Command Center", href: "/ai", icon: BrainCircuit },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  if (pathname === "/login" || pathname === "/signup") return null;

  return (
    <div className="flex h-full w-64 flex-col border-r bg-slate-900 text-slate-100">
      <div className="flex h-16 items-center border-b border-slate-800 px-6">
        <Target className="mr-2 h-6 w-6 text-indigo-400" />
        <span className="text-lg font-bold">DeciFlow</span>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-6 px-4">
          {navigation.map((section, idx) => (
            <div key={idx}>
                <Link
                  href={section.href}
                  className={cn(
                    "group flex items-center rounded-md px-2 py-2 text-sm font-medium",
                    pathname === section.href || pathname.startsWith(section.href + '/')
                      ? "bg-indigo-600 text-white"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  )}
                >
                  <section.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                  {section.name}
                </Link>
            </div>
          ))}
        </nav>
      </div>
    </div>
  );
}
