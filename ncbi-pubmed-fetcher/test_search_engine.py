import pytest
import requests
from unified_client import UnifiedSearchManager
from ncbi_client import NCBIClient

# --- Fixtures (הכנות לבדיקה) ---

@pytest.fixture
def manager():
    return UnifiedSearchManager()

@pytest.fixture
def ncbi_client():
    return NCBIClient()

@pytest.fixture
def sample_xml_response():
    """XML תקין לבדיקות רגילות"""
    return """
    <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>12345678</PMID>
                <Article>
                    <ArticleTitle>Test Article Title for Pytest</ArticleTitle>
                    <Journal>
                        <Title>Journal of Testing</Title>
                        <JournalIssue>
                            <PubDate>
                                <Year>2024</Year>
                            </PubDate>
                        </JournalIssue>
                    </Journal>
                    <AuthorList>
                        <Author>
                            <LastName>Doe</LastName>
                            <Initials>J</Initials>
                        </Author>
                    </AuthorList>
                    <Abstract>
                        <AbstractText>This is a sample abstract.</AbstractText>
                    </Abstract>
                </Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>
    """

@pytest.fixture
def incomplete_xml_response():
    """XML חסר (בלי אבסטרקט ובלי שנה) לבדיקת יציבות"""
    return """
    <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>999999</PMID>
                <Article>
                    <ArticleTitle>Mystery Paper</ArticleTitle>
                    <Journal>
                        <Title>Ghost Journal</Title>
                    </Journal>
                    </Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>
    """

# --- Tests (הבדיקות) ---

def test_priority_logic(manager):
    """בדיקה בסיסית: העדפת PubMed"""
    high = {"title": "Paper A", "source": "PubMed", "url": "http://a"}
    low = {"title": "PAPER A", "source": "Crossref", "url": "http://b"}
    
    res = manager._merge_and_deduplicate([low, high])