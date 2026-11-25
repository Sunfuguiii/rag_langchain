"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuthContext } from "@/lib/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Trash2, RefreshCw, FileText } from "lucide-react";
import { useRouter } from "next/navigation";

interface DocumentItem {
  id: string;
  name: string;
  status: string;
  chunk_count: number;
  file_size: number;
  created_at: string;
}

export default function DocumentsPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/chat");
      return;
    }
    loadDocs();
  }, [user]);

  const loadDocs = async () => {
    try {
      const data = await api.get<{ documents: DocumentItem[] }>("/documents");
      setDocs(data.documents);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await api.upload<DocumentItem>("/documents/upload", file);
      await loadDocs();
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/documents/${id}`);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  };

  const handleReindex = async (id: string) => {
    try {
      await api.post(`/documents/${id}/reindex`);
      await loadDocs();
    } catch (err) {
      console.error("Reindex failed:", err);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      ready: "default",
      indexing: "secondary",
      pending: "outline",
      error: "destructive",
    };
    const labels: Record<string, string> = {
      ready: "就绪",
      indexing: "索引中",
      pending: "等待中",
      error: "错误",
    };
    return <Badge variant={variants[status] || "outline"}>{labels[status] || status}</Badge>;
  };

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">文档管理</h1>
            <p className="text-sm text-muted-foreground">管理知识库文档</p>
          </div>
          <div>
            <input
              type="file"
              accept=".md,.txt"
              onChange={handleUpload}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <Button
              variant="default"
              disabled={uploading}
              onClick={() => document.getElementById("file-upload")?.click()}
            >
              <Upload className="h-4 w-4 mr-2" />
              {uploading ? "上传中..." : "上传文档"}
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">知识库文档</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">加载中...</p>
            ) : docs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>暂无文档，请上传 .md 或 .txt 文件</p>
              </div>
            ) : (
              <ScrollArea className="max-h-[600px]">
                <div className="space-y-2">
                  {docs.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{doc.name}</p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            {getStatusBadge(doc.status)}
                            <span>{doc.chunk_count} 个文档块</span>
                            <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => handleReindex(doc.id)}
                          title="重新索引"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive"
                          onClick={() => handleDelete(doc.id)}
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
