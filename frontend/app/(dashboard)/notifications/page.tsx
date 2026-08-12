import { NotificationList } from "@/features/notifications/components/notification-list";

export default function NotificationsPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Notifications</h1>
        <p className="text-muted-foreground">
          High-value trend alerts, expiring trends, and content generation updates.
        </p>
      </div>
      <NotificationList />
    </main>
  );
}
