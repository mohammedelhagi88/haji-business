const API_URL = process.env.EXPO_PUBLIC_HAJI_API_URL || '';

export async function sendToHaji({ text = '', imageUri = null }) {
  if (!API_URL) {
    return {
      text: imageUri
        ? 'وصلتني الصورة. التطبيق جاهز لتوصيلها بمحرك حاجي للتحليل الحقيقي.'
        : `استلمت طلبك: ${text}`,
      requiresApproval: false,
    };
  }

  const form = new FormData();
  form.append('text', text);
  if (imageUri) {
    form.append('image', {
      uri: imageUri,
      name: 'haji-image.jpg',
      type: 'image/jpeg',
    });
  }

  const response = await fetch(`${API_URL}/v1/agent/message`, {
    method: 'POST',
    body: form,
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) throw new Error(`Haji API error: ${response.status}`);
  return response.json();
}
