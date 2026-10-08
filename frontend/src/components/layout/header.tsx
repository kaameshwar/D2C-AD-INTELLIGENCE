"use client";

import { Bell, Search, Bot, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";

export function Header() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  if (pathname === "/login" || pathname === "/signup") return null;

  const initials = user?.name ? user.name.split(" ").map((n) => n[0]).join("").substring(0, 2).toUpperCase() : "U";

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search campaigns, products..."
            className="h-9 w-64 rounded-md border bg-gray-50 pl-9 pr-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-xs text-gray-500 flex items-center">
          <span className="relative flex h-2 w-2 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          {user ? user.organization_name : "Loading..."}
        </div>
        <Link href="/ai" className="hidden sm:block">
          <Button variant="outline" size="sm" className="text-indigo-600 border-indigo-200 hover:bg-indigo-50">
            <Bot className="mr-2 h-4 w-4" />
            Ask DeciFlow
          </Button>
        </Link>
        <Button variant="ghost" size="icon" className="text-gray-500 hover:text-gray-900" onClick={() => alert("You have no new notifications.")}>
          <Bell className="h-5 w-5" />
        </Button>
        <Link href="/settings">
          <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold hover:ring-2 hover:ring-indigo-300 transition-all cursor-pointer" title={user?.name || ""}>
            {initials}
          </div>
        </Link>
        <Button variant="ghost" size="icon" className="text-gray-500 hover:text-red-600" onClick={logout} title="Logout">
          <LogOut className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
