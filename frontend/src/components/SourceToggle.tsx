"use client";

import { Button } from "@/components/ui/button";
import { Bookmark, BookmarkCheck } from "lucide-react";

interface SourceToggleProps {
  showSources: boolean;
  onChange: (show: boolean) => void;
}

export function SourceToggle({ showSources, onChange }: SourceToggleProps) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onChange(!showSources)}
      className="gap-1 text-xs text-muted-foreground"
      title={showSources ? "隐藏来源引用" : "显示来源引用"}
    >
      {showSources ? (
        <BookmarkCheck className="h-3.5 w-3.5" />
      ) : (
        <Bookmark className="h-3.5 w-3.5" />
      )}
      来源
    </Button>
  );
}
