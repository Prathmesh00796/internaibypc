"use client";

import { useEffect, useState } from "react";
import { Bell, CheckCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";

interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body: string | null;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    const res = await api.get("/notifications");
    setNotifications(res.data);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function markAllRead() {
    await api.post("/notifications/mark-all-read");
    load();
  }

  return (
    <div className="space-y-6 animate-fade-up max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Notifications</h1>
          <p className="text-sm text-ink-secondary mt-1">New matches, status changes, and daily summaries.</p>
        </div>
        <Button size="sm" variant="secondary" onClick={markAllRead}>
          <CheckCheck size={14} /> Mark all read
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 rounded-xl bg-base-elevated animate-pulse" />)}</div>
      ) : notifications.length === 0 ? (
        <Card className="p-12 text-center">
          <Bell size={28} className="mx-auto text-ink-muted mb-3" />
          <p className="text-ink-secondary">No notifications yet.</p>
        </Card>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <Card key={n.id} className={`p-4 ${!n.is_read ? "border-signal-violet/30" : ""}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">{n.title}</p>
                  {n.body && <p className="text-xs text-ink-secondary mt-1" dangerouslySetInnerHTML={{ __html: n.body }} />}
                </div>
                {!n.is_read && <span className="w-2 h-2 rounded-full bg-signal-violet shrink-0 mt-1" />}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
