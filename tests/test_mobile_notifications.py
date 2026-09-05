from modules.notifications.mobile import MobileNotificationInbox


def test_mobile_notification_inbox_round_trip():
    inbox = MobileNotificationInbox()
    inbox.push({"type": "task.created", "text": "مهمة جديدة"})
    assert inbox.list()[0]["type"] == "task.created"
    inbox.clear()
    assert inbox.list() == []
