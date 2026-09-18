import { PageIntro } from "@/components/ui/page-intro";
import { NotificationList } from "@/features/notifications/components/notification-list";

export default function NotificationsPage() {
  return (
    <main className="flex flex-1 flex-col gap-6 p-4 sm:p-8">
      <PageIntro
        eyebrow="Stay in the loop"
        title="Notifications"
        description="High-value trend alerts, expiring opportunities, and content generation updates."
      />
      <NotificationList />
    </main>
  );
}
