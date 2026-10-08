import pytest
from app.ai import AIError, recommend_books
from google import genai
from types import SimpleNamespace


class FakeClient:
    output = '{"recommendations":[{"book_id":1,"reason":"SQL practice","catalog_evidence":"SQL joins"}],"message":"Catalog match"}'
    def __init__(self, **kwargs):
        self.models = self
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def generate_content(self, **kwargs):
        assert kwargs['config']['response_mime_type'] == 'application/json'
        return SimpleNamespace(text=self.output)


def test_sdk_boundary_and_empty_response(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-test-key')
    monkeypatch.setenv('GEMINI_MODEL', 'test-model')
    monkeypatch.setattr(genai, 'Client', FakeClient)
    catalog = [{'id':1,'title':'Demo','author':'Fictional','description':'SQL joins','category':'Databases'}]
    assert recommend_books('SQL', catalog).recommendations[0].book_id == 1
    monkeypatch.setattr(FakeClient, 'output', '')
    with pytest.raises(AIError, match='empty recommendation'):
        recommend_books('SQL', catalog)
