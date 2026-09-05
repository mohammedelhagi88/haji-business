const API_URL = process.env.EXPO_PUBLIC_HAJI_API_URL || '';

export async function sendToHaji({ text = '', imageUri = null }) {
  if (!API_URL) return { text: imageUri ? 'وصلتني الصورة. التطبيق جاهز لتحليلها عند تشغيل الخادم.' : `استلمت طلبك: ${text}`, requiresApproval: false };
  const form = new FormData(); form.append('text', text);
  if (imageUri) form.append('image', { uri: imageUri, name: 'haji-image.jpg', type: 'image/jpeg' });
  const response = await fetch(`${API_URL}/v1/agent/message`, { method: 'POST', body: form, headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`Haji API error: ${response.status}`);
  return response.json();
}

export async function sendVoiceToHaji(audioUri) {
  if (!API_URL) return { text: 'التسجيل محفوظ في التطبيق، لكن الخادم مش مربوط حالياً بتحويل الصوت إلى نص.', requiresApproval: false };
  const form = new FormData();
  form.append('audio', { uri: audioUri, name: 'haji-voice.m4a', type: 'audio/mp4' });
  const response = await fetch(`${API_URL}/v1/agent/voice`, { method: 'POST', body: form, headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`Haji voice API error: ${response.status}`);
  return response.json();
}

export async function approveWithHaji(approvalId) {
  if (!API_URL || !approvalId) return { ok: false, error: 'api_or_approval_missing' };
  const response = await fetch(`${API_URL}/v1/agent/approval/${encodeURIComponent(approvalId)}`, { method: 'POST', headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`Haji approval error: ${response.status}`);
  return response.json();
}
