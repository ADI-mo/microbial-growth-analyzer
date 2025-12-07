import pytest
import csv
import os
import requests
from unified_client import UnifiedSearchManager
from ncbi_client import NCBIClient

# --- Fixtures ---

@pytest.fixture
def manager():
    return UnifiedSearchManager()

@pytest.fixture
def ncbi_client():
    return NCBIClient()

# --- Tests ---

def test_missing_data_handling(manager, monkeypatch):
    """Test 1: Handle missing fields (None) without crashing"""
    def mock_search_broken(*args, **kwargs):
        return [{
            "title": "Mystery Paper",
            "source": "PubMed",
            "year": None,
            "abstract": None,
            "citations": None,
            "url": "http://test.com",
            "pdf_url": "N/A"
        }]
    monkeypatch.setattr(manager.clients["PubMed"], "search", mock_search_broken)
    
    results = manager.search_all("test", active_sources=["PubMed"])
    item = results[0]
    
    # Assertions
    assert item["year"] is None or item["year"] == "N/A"
    assert item["abstract"] is None or item["abstract"] == "" or item["abstract"] == "No Abstract"

def test_long_text_stress(manager, monkeypatch, tmp_path):
    """Test 2: Handle very long text"""
    long_abstract = "Long text... " * 500
    def mock_search_long(*args, **kwargs):
        return [{
            "title": "Long Paper",
            "source": "OpenAlex",
            "abstract": long_abstract,
            "citations": 10,
            "year": "2024",
            "url": "http://a",
            "pdf_url": "http://b"
        }]
    monkeypatch.setattr(manager.clients["OpenAlex"], "search", mock_search_long)
    
    results = manager.search_all("stress", active_sources=["OpenAlex"])
    
    # Verify CSV export
    csv_file = tmp_path / "stress.csv"
    manager.save_to_csv(results, str(csv_file))
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        row = next(csv.DictReader(f))
        assert len(row['abstract']) > 5000

def test_zero_results(manager, monkeypatch):
    """Test 3: Handle zero results"""
    for client_name in manager.clients:
        monkeypatch.setattr(manager.clients[client_name], "search", lambda *a, **k: [])
    
    results = manager.search_all("Xylophone_123")
    assert len(results) == 0
    # Should not crash on save
    manager.save_to_csv(results, "empty.csv")

def test_csv_formatting_integrity(manager, tmp_path):
    """Test 4: Handle commas in title"""
    data = [{"source": "S", "title": "A, B, and C", "abstract": "T", "year": "2023"}]
    csv_file = tmp_path / "tricky.csv"
    manager.save_to_csv(data, str(csv_file))
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        row = next(csv.DictReader(f))
        assert row['title'] == "A, B, and C"

def test_priority_logic(manager):
    """Test 5: Priority logic"""
    high = {"title": "Paper A", "source": "PubMed", "url": "http://a"}
    low = {"title": "PAPER A", "source": "Semantic Scholar", "url": "http://b"}
    res = manager._merge_and_deduplicate([low, high])
    assert len(res) == 1
    assert res[0]["source"] == "PubMed"

def test_ncbi_xml_parsing(ncbi_client, requests_mock):
    """Test 6: XML Parsing"""
    xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>1</PMID>
    <Article><ArticleTitle>T</ArticleTitle><Journal><JournalIssue><PubDate><Year>2024</Year>
    </PubDate></JournalIssue></Journal><AuthorList><Author><LastName>Doe</LastName><Initials>J</Initials></Author></AuthorList>
    <Abstract><AbstractText>A</AbstractText></Abstract>
    </Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""
    requests_mock.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", text=xml)
    res = ncbi_client.fetch_details(["1"])
    assert res[0]["year"] == "2024"

def test_api_timeout_resilience(manager, monkeypatch):
    """Test 7: Timeout resilience"""
    def mock_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Server is down")
    monkeypatch.setattr(manager.clients["Semantic Scholar"], "search", mock_timeout)
    
    def mock_success(*args, **kwargs):
        return [{"title": "Good Paper", "source": "PubMed"}]
    monkeypatch.setattr(manager.clients["PubMed"], "search", mock_success)

    results = manager.search_all("test", active_sources=["PubMed", "Semantic Scholar"])
    assert len(results) == 1
    assert results[0]["title"] == "Good Paper"

def test_unicode_handling(manager, tmp_path):
    """Test 8: Unicode characters"""
    special_title = "Effects of β-blockers on α-cells & 100°C"
    data = [{"title": special_title, "source": "Test", "abstract": "µ-grams"}]
    csv_file = tmp_path / "unicode.csv"
    manager.save_to_csv(data, str(csv_file))
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        row = next(csv.DictReader(f))
        assert row['title'] == special_title

def test_free_full_text_filter(manager, monkeypatch):
    """Test 9: Free text filter logic"""
    mock_results = [
        {"title": "Free Paper", "source": "Semantic Scholar", "pdf_url": "http://pdf"},
        {"title": "Paid Paper", "source": "Semantic Scholar", "pdf_url": "N/A"}
    ]
    client = manager.clients["Semantic Scholar"]
    
    # Mocking the search method of the client
    def mock_search_with_filter(term, start_year=None, max_results=5, only_free=False):
        if only_free:
             return [r for r in mock_results if r['pdf_url'] != "N/A"]
        return mock_results

    monkeypatch.setattr(client, "search", mock_search_with_filter)

    results = manager.search_all("test", active_sources=["Semantic Scholar"], only_free=True)
    assert len(results) == 1
    assert results[0]["title"] == "Free Paper"

def test_date_range_logic(manager, monkeypatch):
    """Test 10: Date range logic"""
    received_year = {}
    def mock_search(term, start_year=None, max_results=5, only_free=False):
        received_year['year'] = start_year
        return []

    monkeypatch.setattr(manager.clients["PubMed"], "search", mock_search)
    manager.search_all("test", active_sources=["PubMed"], start_year=2020)
    assert received_year['year'] == 2020