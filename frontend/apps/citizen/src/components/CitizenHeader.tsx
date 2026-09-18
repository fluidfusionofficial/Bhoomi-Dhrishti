'use client';

import * as React from 'react';
import Link from 'next/link';
import { Bell, Check, X, Shield, Clock } from 'lucide-react';
import { fetchUserNotifications, markNotificationAsRead, NotificationItem } from '@bhoomi/api-client';

export function CitizenHeader() {
  const [notifications, setNotifications] = React.useState<NotificationItem[]>([]);
  const [showDrawer, setShowDrawer] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  // Poll or load notifications for citizen
  React.useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const res = await fetchUserNotifications('citizen_demo_user');
      if (Array.isArray(res)) {
        setNotifications(res);
      }
    } catch {
      // Fallback notifications if endpoint is not serving this user yet
      setNotifications([
        {
          id: 'notif-1',
          user_id: 'citizen_demo_user',
          title: 'Mutation Hearing Scheduled',
          message: 'Hearing scheduled for Survey No. 42/1B on 24 Sep 2026 before Tahsildar.',
          type: 'INFO',
          created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
          is_read: false,
        },
        {
          id: 'notif-2',
          user_id: 'citizen_demo_user',
          title: 'Encumbrance Certificate Issued',
          message: 'Certificate No. EC-2026-8910 is ready to download.',
          type: 'SUCCESS',
          created_at: new Date(Date.now() - 3600000 * 28).toISOString(),
          is_read: true,
        },
      ]);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationAsRead(id);
    } catch {}
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <>
      {/* 3px Indian Tricolor Top Strip (§2.1 optional but standard on Indian public service sites) */}
      <div className="w-full h-[3px] flex" role="presentation">
        <div className="flex-1 bg-[#FF9933]" />
        <div className="flex-1 bg-[#FFFFFF]" />
        <div className="flex-1 bg-[#138808]" />
      </div>

      {/* Main Official Header */}
      <header className="bg-[#14548C] text-white px-4 py-3 sticky top-0 z-30 shadow-none border-b border-[#103F68]">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-[4px] bg-white text-[#14548C] flex items-center justify-center font-serif font-bold text-base">
              BD
            </div>
            <div>
              <div className="text-base font-bold tracking-tight leading-none">
                Bhoomi Dhrishti
              </div>
              <div className="text-[10px] text-[#E2ECF5] tracking-wide mt-0.5 opacity-90">
                Department of Land Resources (DoLR)
              </div>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowDrawer(true)}
              aria-label={`Notifications (${unreadCount} unread)`}
              className="relative p-2 rounded-[4px] hover:bg-[#103F68] transition-colors"
            >
              <Bell className="w-5 h-5 text-white" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 bg-[#A32E2E] text-white text-[10px] font-bold rounded-full flex items-center justify-center tabular-nums">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Notifications Drawer */}
      {showDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-filter-none">
          <div className="w-full max-w-sm bg-white h-full shadow-lg flex flex-col">
            <div className="p-4 bg-[#14548C] text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4" />
                <span className="font-semibold text-sm">Notifications</span>
                {unreadCount > 0 && (
                  <span className="bg-[#A32E2E] px-1.5 py-0.2 rounded-full text-[11px] font-bold">
                    {unreadCount} new
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setShowDrawer(false)}
                className="p-1 hover:bg-[#103F68] rounded"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-[#DCE3EA]">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#4A5B6E]">
                  No notifications to display.
                </div>
              ) : (
                notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`p-4 transition-colors ${
                      notif.is_read ? 'bg-white' : 'bg-[#E2ECF5]/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-semibold text-[#16212E]">
                        {notif.title}
                      </h4>
                      {!notif.is_read && (
                        <button
                          type="button"
                          onClick={() => handleMarkAsRead(notif.id)}
                          title="Mark as read"
                          className="text-[#14548C] hover:text-[#103F68] p-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-[#4A5B6E] mt-1 leading-relaxed">
                      {notif.message}
                    </p>
                    <div className="flex items-center gap-1 text-[10px] text-[#4A5B6E] mt-2">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(notif.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 border-t border-[#DCE3EA] bg-[#F6F7F9] text-center">
              <button
                type="button"
                onClick={() => {
                  notifications.forEach((n) => handleMarkAsRead(n.id));
                }}
                className="text-xs text-[#14548C] font-semibold hover:underline"
              >
                Mark all as read
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}