import React, { useEffect, useState } from 'react';
import { SafeAreaView, View, Text, TextInput, Pressable, Image, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import { approveWithHaji, sendToHaji, sendVoiceToHaji } from './src/agent';

export default function App() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([{ role: 'haji', text: 'هلا بيك 👋 أنا حاجي. شن تبي نديرلك اليوم؟' }]);
  const [imageUri, setImageUri] = useState(null);
  const [recording, setRecording] = useState(null);
  const [busy, setBusy] = useState(false);
  const [approvalBusy, setApprovalBusy] = useState(null);

  useEffect(() => () => { if (recording) recording.stopAndUnloadAsync().catch(() => {}); }, [recording]);

  const speak = (text) => Speech.speak(text, { language: 'ar', rate: 0.95 });

  const send = async () => {
    const text = message.trim();
    if ((!text && !imageUri) || busy) return;
    const attachedImage = imageUri;
    setMessages((items) => [...items, { role: 'user', text: text || 'حلل الصورة هذي', image: attachedImage }]);
    setMessage(''); setImageUri(null); setBusy(true);
    try {
      const result = await sendToHaji({ text, imageUri: attachedImage });
      const answer = result.text || result.message || 'تم استلام الطلب.';
      setMessages((items) => [...items, { role: 'haji', text: answer, approval: result.requiresApproval, approvalId: result.approvalId }]);
      speak(answer);
    } catch (error) {
      const answer = 'صار خلل في الاتصال بحاجي. الطلب ما تنفذش.';
      setMessages((items) => [...items, { role: 'haji', text: answer }]); speak(answer);
    } finally { setBusy(false); }
  };

  const startVoice = async () => {
    if (busy || recording) return;
    const permission = await Audio.requestPermissionsAsync();
    if (!permission.granted) { setMessages((items) => [...items, { role: 'haji', text: 'نحتاج إذن الميكروفون باش نسمعك.' }]); return; }
    await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
    const created = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
    setRecording(created.recording);
  };

  const stopVoice = async () => {
    if (!recording || busy) return;
    const current = recording;
    setRecording(null); setBusy(true);
    try {
      await current.stopAndUnloadAsync();
      const uri = current.getURI();
      if (!uri) throw new Error('recording_uri_missing');
      setMessages((items) => [...items, { role: 'user', text: '🎙️ تسجيل صوتي...' }]);
      const result = await sendVoiceToHaji(uri);
      const transcript = result.transcript ? `سمعتك: ${result.transcript}` : '';
      const answer = result.text || result.message || (result.transcript ? `فهمتك: ${result.transcript}` : 'وصلني التسجيل، لكن تحويل الصوت لنص مش مفعّل في الخادم حالياً.');
      setMessages((items) => [...items, { role: 'haji', text: `${transcript}${transcript ? '\n\n' : ''}${answer}`, approval: result.requiresApproval, approvalId: result.approvalId }]);
      speak(answer);
    } catch (error) {
      const answer = 'ما قدرتش نعالج التسجيل الصوتي حالياً.';
      setMessages((items) => [...items, { role: 'haji', text: answer }]); speak(answer);
    } finally { setBusy(false); }
  };

  const approve = async (approvalId, index) => {
    if (!approvalId || approvalBusy) return;
    setApprovalBusy(approvalId);
    try {
      const result = await approveWithHaji(approvalId);
      setMessages((items) => items.map((item, i) => i === index ? { ...item, approval: false, approved: result.ok, text: `${item.text}\n\n✅ تمت الموافقة.` } : item));
    } catch (error) { setMessages((items) => [...items, { role: 'haji', text: 'ما قدرتش نسجل الموافقة حالياً.' }]); }
    finally { setApprovalBusy(null); }
  };

  const chooseImage = async (source) => {
    try {
      let result;
      if (source === 'camera') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          setMessages((items) => [...items, { role: 'haji', text: 'نحتاج إذن الكاميرا باش نصوّر الصورة.' }]);
          return;
        }
        result = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.85 });
      } else {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          setMessages((items) => [...items, { role: 'haji', text: 'نحتاج إذن الصور باش نختار صورة من الجهاز.' }]);
          return;
        }
        result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.85 });
      }
      if (!result.canceled && result.assets?.[0]?.uri) setImageUri(result.assets[0].uri);
    } catch (error) {
      setMessages((items) => [...items, { role: 'haji', text: 'ما قدرتش نفتح الكاميرا أو الصور حالياً.' }]);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}><View><Text style={styles.title}>حاجي AI</Text><Text style={styles.status}>● متصل وجاهز</Text></View><Text style={styles.brain}>🧠</Text></View>
      <ScrollView contentContainerStyle={styles.chat}>
        {messages.map((item, index) => <View key={index} style={[styles.bubble, item.role === 'user' ? styles.user : styles.haji]}>
          {item.image && <Image source={{ uri: item.image }} style={styles.messageImage} />}
          <Text style={styles.bubbleText}>{item.text}</Text>
          {item.approval && <><Text style={styles.approval}>⚠️ هذا الإجراء يحتاج موافقتك الصريحة</Text><Pressable style={styles.approve} onPress={() => approve(item.approvalId, index)} disabled={approvalBusy === item.approvalId}>{approvalBusy === item.approvalId ? <ActivityIndicator color="#fff" /> : <Text style={styles.white}>موافقة</Text>}</Pressable></>}
        </View>)}
        {imageUri && <Image source={{ uri: imageUri }} style={styles.preview} />}
      </ScrollView>
      <View style={styles.composer}>
        <Pressable style={styles.iconButton} onPress={() => chooseImage('gallery')}><Text>🖼️</Text></Pressable>
        <Pressable style={styles.iconButton} onPress={() => chooseImage('camera')}><Text>📷</Text></Pressable>
        <TextInput value={message} onChangeText={setMessage} placeholder="كلم حاجي..." placeholderTextColor="#7b8794" style={styles.input} multiline />
        <Pressable style={[styles.voice, recording && styles.recording]} onPress={recording ? stopVoice : startVoice} disabled={busy}><Text style={styles.white}>{recording ? '⏹️' : '🎙️'}</Text></Pressable>
        <Pressable style={styles.send} onPress={send} disabled={busy}>{busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.white}>➤</Text>}</Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#07111f' }, header: { padding: 22, paddingTop: 28, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#17263a' },
  title: { color: '#fff', fontSize: 28, fontWeight: '800' }, status: { color: '#55d68a', marginTop: 4, fontSize: 13 }, brain: { fontSize: 30 }, chat: { padding: 18, gap: 12, paddingBottom: 25 },
  bubble: { maxWidth: '84%', padding: 14, borderRadius: 18 }, haji: { alignSelf: 'flex-start', backgroundColor: '#122238' }, user: { alignSelf: 'flex-end', backgroundColor: '#1d6b55' }, bubbleText: { color: '#f4f7fb', fontSize: 16, lineHeight: 24 },
  approval: { color: '#ffd166', marginTop: 8, fontSize: 13 }, approve: { marginTop: 10, paddingVertical: 10, paddingHorizontal: 18, borderRadius: 12, backgroundColor: '#1d8b68', alignItems: 'center' },
  messageImage: { width: 180, height: 180, borderRadius: 14, marginBottom: 8 }, preview: { width: 180, height: 180, borderRadius: 16, alignSelf: 'flex-end' },
  composer: { flexDirection: 'row', alignItems: 'flex-end', padding: 12, gap: 8, borderTopWidth: 1, borderTopColor: '#17263a' }, iconButton: { width: 42, height: 42, borderRadius: 21, backgroundColor: '#122238', alignItems: 'center', justifyContent: 'center' },
  input: { flex: 1, minHeight: 44, maxHeight: 110, paddingHorizontal: 15, paddingVertical: 11, color: '#fff', backgroundColor: '#101c2c', borderRadius: 22, textAlign: 'right' }, voice: { width: 42, height: 42, borderRadius: 21, backgroundColor: '#2457a6', alignItems: 'center', justifyContent: 'center' }, recording: { backgroundColor: '#a63a3a' }, send: { width: 42, height: 42, borderRadius: 21, backgroundColor: '#1d8b68', alignItems: 'center', justifyContent: 'center' }, white: { color: '#fff', fontSize: 18 },
});
