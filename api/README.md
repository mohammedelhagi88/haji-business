# Haji API

واجهة HTTP خفيفة للتطبيق المحمول.

## تشغيل محلي

```bash
python -m api.app
```

تعمل افتراضياً على `http://localhost:8000`.

### Endpoint

`POST /v1/agent/message`

يمكن إرسال JSON مثل:

```json
{"text":"شن عندي من مهام اليوم؟","image":null}
```

وفي الإنتاج يجب وضع طبقة HTTPS ومصادقة وتحديد حجم الملفات ومعدل الطلبات قبل فتح الواجهة للإنترنت.
