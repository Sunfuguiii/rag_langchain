"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Source } from "@/hooks/useChat";

export function SourceCard({ source }: { source: Source }) {
  return (
    <Card className="bg-muted/50">
      <CardContent className="p-3 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="secondary" className="text-xs">
            {source.chapter || "未知章节"}
          </Badge>
          {source.section && (
            <span className="text-xs text-muted-foreground">&gt; {source.section}</span>
          )}
          <span className="text-xs text-muted-foreground ml-auto">
            相关度: {Math.round(source.score * 100)}%
          </span>
        </div>
        <p className="text-xs text-muted-foreground line-clamp-2">{source.content}</p>
      </CardContent>
    </Card>
  );
}
