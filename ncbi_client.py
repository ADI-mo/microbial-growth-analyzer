import requests
import xml.etree.ElementTree as ET

class NCBIClient:
    """
    Handles interactions with the NCBI Entrez API (E-utilities).
    """
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, api_key=None, tool_name="science_fetcher"):
        self.api_key = api_key
        self.tool_name = tool_name

    def _get_base_params(self):
        # NCBI requires a tool parameter and email is recommended
        params = {"tool": self.tool_name, "email": "user@example.com"}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def search_pubmed(self, term, max_results=5):
        url = f"{self.BASE_URL}/esearch.fcgi"
        params = self._get_base_params()
        
        params.update({
            "db": "pubmed",
            "term": term,
            "retmax": max_results,
            "sort": "relevance",
            "retmode": "json"
        })

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"NCBI Search Error: {e}")
            return []

    def fetch_details(self, id_list):
        if not id_list:
            return []

        url = f"{self.BASE_URL}/efetch.fcgi"
        params = self._get_base_params()
        params.update({
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        })

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse complex XML from PubMed
            root = ET.fromstring(response.content)
            results = []

            for article in root.findall(".//PubmedArticle"):
                # Title
                title = article.findtext(".//ArticleTitle") or "No Title"
                journal = article.findtext(".//Journal/Title") or "Unknown Journal"
                
                # PMID
                pmid = article.findtext(".//MedlineCitation/PMID")
                
                # Year logic
                year = article.findtext(".//Journal/JournalIssue/PubDate/Year")
                if not year:
                    year = article.findtext(".//PubDate/MedlineDate")
                
                # Abstract
                abstract_texts = article.findall(".//AbstractText")
                full_abstract = " ".join(["".join(t.itertext()) for t in abstract_texts])
                if not full_abstract:
                    full_abstract = "No Abstract Available."

                # Authors
                authors = []
                for author in article.findall(".//Author"):
                    last = author.findtext("LastName")
                    initials = author.findtext("Initials")
                    if last and initials:
                        authors.append(f"{last} {initials}")
                
                results.append({
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "year": year,
                    "authors": ", ".join(authors),
                    "abstract": full_abstract
                })
            
            return results

        except Exception as e:
            print(f"NCBI Fetch Error: {e}")
            return []