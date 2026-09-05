import unittest
from core.ai_provider import OpenAICompatibleProvider


class FakeProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(base_url='https://example.invalid/v1', api_key='test')
        self.calls = []

    def _post(self, path, payload):
        self.calls.append((path, payload))
        return {'choices': [{'message': {'content': 'رد من الذكاء'}}]}


class AIProviderTests(unittest.TestCase):
    def test_chat_text(self):
        provider = FakeProvider()
        self.assertEqual(provider.chat('هلا'), 'رد من الذكاء')
        self.assertEqual(provider.calls[0][0], '/chat/completions')
        self.assertEqual(provider.calls[0][1]['messages'][0]['content'][0]['text'], 'هلا')

    def test_chat_image(self):
        provider = FakeProvider()
        result = provider.chat('حللها', b'fake-image')
        self.assertEqual(result, 'رد من الذكاء')
        content = provider.calls[0][1]['messages'][0]['content']
        self.assertEqual(content[1]['type'], 'image_url')
        self.assertTrue(content[1]['image_url']['url'].startswith('data:image/jpeg;base64,'))


if __name__ == '__main__':
    unittest.main()
