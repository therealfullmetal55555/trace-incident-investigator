import json, os, sys, unittest
from io import BytesIO
from unittest.mock import patch
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app

class FakeResponse:
    def __init__(self, obj): self.buf=BytesIO(json.dumps(obj).encode())
    def __enter__(self): return self.buf
    def __exit__(self,*args): pass

def response(result): return {'candidates':[{'content':{'parts':[{'text':json.dumps(result)}]}}]}

class Tests(unittest.TestCase):
    def test_scenarios_unique_and_have_ground_truth(self):
        self.assertEqual(len({s['id'] for s in app.SCENARIOS}),len(app.SCENARIOS))
        for s in app.SCENARIOS:
            self.assertTrue(s['expected']); self.assertEqual(len({e['id'] for e in s['events']}),len(s['events']))
    @patch('app.urllib.request.urlopen')
    def test_filters_invented_evidence(self, urlopen):
        urlopen.return_value=FakeResponse(response({'summary':'s','hypothesis':'h','uncertainty':'u','next_steps':['a'],'evidence_ids':['E01','made-up','E01']}))
        out=app.investigate(app.SCENARIOS[0], 'fake-key')
        self.assertEqual(out['evidence_ids'],['E01'])
        req=urlopen.call_args.args[0]; self.assertNotIn('fake-key',req.full_url); self.assertEqual(req.get_header('X-goog-api-key'),'fake-key')
    @patch('app.urllib.request.urlopen')
    def test_bad_model_response_is_error(self, urlopen):
        urlopen.return_value=FakeResponse(response({'summary':'bad'}))
        with self.assertRaises(RuntimeError): app.investigate(app.SCENARIOS[0], 'fake')
    def test_rejects_bad_model(self):
        with self.assertRaises(ValueError): app.investigate(app.SCENARIOS[0], 'fake', '../oops')
if __name__=='__main__': unittest.main()
