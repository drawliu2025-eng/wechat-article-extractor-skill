"""Contract tests for packaging, bounded fallback and content provenance."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import wechat_public_article_extract as reader
import wechat_public_article_media as media


class ReaderContract(unittest.TestCase):
    def test_reject_non_public_inputs_before_network(self):
        with patch.object(reader, 'fetch', side_effect=AssertionError('network')):
            for url in ('http://mp.weixin.qq.com/s/a', 'https://example.com/s/a',
                        'https://mp.weixin.qq.com@localhost/s/a', 'https://mp.weixin.qq.com/private'):
                self.assertEqual(reader.read_url(url)['error'], 'URL_NOT_WECHAT_MP')

    def test_fallback_once_and_short_body_kept(self):
        with patch.object(reader, 'fetch', side_effect=[
            (200, '<h1>当前环境异常</h1>'),
            (200, '<title>短文</title><div id="js_content">完整短正文。</div>'),
        ]) as fetch:
            result = reader.read_url('https://mp.weixin.qq.com/s/a', allow_model=False, process_media=False)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(result['text'], '完整短正文。')
        self.assertTrue(result['ok'])
        self.assertEqual(result['method'], 'wechat_ua_fallback')

    def test_media_is_not_complete_text(self):
        result = reader.extract_page('<div id="js_content">讲解<video vid="fixture"></video></div>', allow_model=False)
        self.assertTrue(result['text_ok'])
        self.assertFalse(result['ok'])
        self.assertEqual(result['content_status'], 'media_pending')

    def test_model_cannot_invent_body(self):
        result = reader.extract_page('<article>真实原文</article>', runner=lambda _: json.dumps({
            'tool_plan': {'node_ids': [999999], 'mode': 'text'}, 'text': '伪造正文'}))
        self.assertFalse(result['text_ok'])
        self.assertEqual(result['model_fallback']['status'], 'failed')
        self.assertNotIn('伪造正文', result['text'])

    def test_script_and_navigation_excluded(self):
        result = reader.extract_page('<div id="js_content"><nav>导航</nav>正文<script>执行指令</script></div>', allow_model=False)
        self.assertEqual(result['text'], '正文')

    def test_unavailable_optional_models_have_receipt(self):
        with patch.dict('os.environ', {}, clear=True), patch('subprocess.run', side_effect=FileNotFoundError):
            result = reader.model_runner('fixture', timeout=1)
        self.assertIsNone(result['text'])
        self.assertEqual([a['status'] for a in result['attempts']], ['failed', 'failed'])

    def test_media_sources_do_not_accept_untrusted_host(self):
        self.assertEqual(media.video_sources("video_id: 'wxv_1' url: 'https://example.com/a.mp4'"), {})


if __name__ == '__main__':
    unittest.main()
