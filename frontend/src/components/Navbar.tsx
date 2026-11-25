"use client";

import Link from "next/link";
import { useAuthContext } from "@/lib/AuthContext";
import { ThemeToggle } from "./ThemeToggle";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LogOut, User } from "lucide-react";

export function Navbar() {
  const { user, logout } = useAuthContext();

  return (
    <header className="border-b">
      <div className="flex h-14 items-center px-4 gap-4">
        <Link href="/chat" className="font-bold text-lg">
          🏫 校园生活助手
        </Link>

        <nav className="flex-1 flex items-center gap-4 ml-4">
          <Link href="/chat" className="text-sm text-muted-foreground hover:text-foreground">
            智能问答
          </Link>
          {user?.role === "admin" && (
            <Link
              href="/documents"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              文档管理
            </Link>
          )}
        </nav>

        <ThemeToggle />

        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button variant="ghost" size="icon" className="rounded-full" />
              }
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback>{user.email[0].toUpperCase()}</AvatarFallback>
              </Avatar>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem disabled>
                <User className="mr-2 h-4 w-4" />
                {user.email}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                退出登录
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}
