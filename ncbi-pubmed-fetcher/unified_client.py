import requests
import concurrent.futures
import datetime
from ncbi_client import NCBIClient

# --- HELPERS ---
def get_current_year():
    return datetime.datetime.now().year

# --- 1. PubMed Wrapper ---
class PubMedWrapper:
    def __init__(self):
        self.client = NCBIClient()
    
    def search(self, term, start_year=None, max_results=5):
        try:
            # Smart Search & Date Filtering via Query Expansion
            # We append the date range directly to the query string for PubMed
            final_term = term
            if start_year:
                current_year = get_current_year()
                final_term = f"{term} AND {start_year}:{current_year}[dp]"
            
            ids = self.client.search_pubmed(final_term, max_results)
            data = self.client.fetch_details(ids)
            
            for item in data:
                item['source'] = "PubMed"
                item['citations'] = "N/A" # PubMed XML doesn't easily give citation counts without extra calls
                item['pdf_url'] = "N/A"   # PubMed is a catalog, rarely has direct PDF links
                
                pmid = item.get('pmid')
                if pmid:
                    item['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    # Try to construct a DOI if missing, for cross-referencing later
                    if 'doi' not in item:
                        item['doi'] = None 
                else:
                    item['url'] = "https://pubmed.ncbi.nlm.nih.gov/"
            return data
        except Exception as e:
            print(f"PubMed Error: {e}")
            return []

# --- 2. Semantic Scholar Client ---
class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def search(self, term, start_year=None, max_results=5):
        # Date Range Logic
        year_range = ""
        if start_year:
            year_range = f"{start_year}-{get_current_year()}"

        params = {
            "query": term, 
            "limit": max_results, 
            "fieldsOfStudy": "Biology,Medicine",
            # Requesting Citation Count and Open Access PDF
            "fields": "title,authors,year,abstract,journal,url,isOpenAccess,openAccessPdf,citationCount,externalIds"
        }
        
        if year_range:
            params["year"] = year_range

        try:
            r = requests.get(self.BASE_URL, params=params, headers={"User-Agent": "Bot"}, timeout=10).json()
            return self._parse(r)
        except: return []

    def _parse(self, data):
        res = []
        for p in data.get("data", []):
            auth = ", ".join([a["name"] for a in p.get("authors", [])[:3]])
            
            # PDF Logic
            pdf_link = "N/A"
            if p.get("openAccessPdf"):
                pdf_link = p.get("openAccessPdf", {}).get("url", "N/A")
            
            # DOI for cross-referencing
            doi = p.get("externalIds", {}).get("DOI")

            res.append({
                "title": p.get("title"), 
                "journal": p.get("journal",{}).get("name","Semantic Scholar"), 
                "year": str(p.get("year","")), 
                "authors": auth, 
                "abstract": p.get("abstract") or "No Abstract Available.", 
                "source": "Semantic Scholar", 
                "url": p.get("url", "N/A"),
                "citations": p.get("citationCount", 0),
                "pdf_url": pdf_link,
                "doi": doi
            })
        return res

# --- 3. Europe PMC Client ---
class EuropePmcClient:
    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    def search(self, term, start_year=None, max_results=5):
        # Query Expansion with Date
        query = f"{term} AND (SRC:PPR OR SRC:MED) AND LANGUAGE:english"
        if start_year:
            query += f" AND PUB_YEAR:[{start_year} TO {get_current_year()}]"

        params = {"query": query, "format": "json", "pageSize": max_results}
        try:
            return self._parse(requests.get(self.BASE_URL, params=params, timeout=10).json())
        except: return []

    def _parse(self, data):
        res = []
        for i in data.get("resultList", {}).get("result", []):
            pmid = i.get("id")
            doi = i.get("doi")
            url = f"https://europepmc.org/article/MED/{pmid}" if pmid else "N/A"
            
            # Citations (EuropePMC gives citedByCount)
            cites = i.get("citedByCount", 0)
            
            # PDF (sometimes in fullTextUrlList)
            pdf = "N/A"
            # (Parsing EuropePMC deep links for PDF is complex, leaving simplified)

            res.append({
                "title": i.get("title"), 
                "journal": i.get("journalInfo",{}).get("journal",{}).get("title","EuropePMC"), 
                "year": i.get("journalInfo",{}).get("yearOfPublication","N/A"), 
                "authors": i.get("authorString",""), 
                "abstract": i.get("abstractText","No Abstract Available."), 
                "source": "EuropePMC", 
                "url": url,
                "citations": cites,
                "pdf_url": pdf,
                "doi": doi
            })
        return res

# --- 4. OpenAlex Client ---
class OpenAlexClient:
    BASE_URL = "https://api.openalex.org/works"
    
    def search(self, term, start_year=None, max_results=5):
        try:
            # Filter logic
            filters = "has_abstract:true,language:en"
            if start_year:
                filters += f",from_publication_date:{start_year}-01-01"

            params = {
                "search": term, 
                "per-page": max_results, 
                "filter": filters,
                "sort": "cited_by_count:desc" # Sort by Impact!
            }
            return self._parse(requests.get(self.BASE_URL, params=params, timeout=10).json())
        except: return []

    def _parse(self, data):
        res = []
        for i in data.get("results", []):
            auth = ", ".join([a.get("author",{}).get("display_name","") for a in i.get("authorships",[])[:3]])
            
            abs_idx = i.get("abstract_inverted_index")
            abstract = "Abstract Available at Source."
            if abs_idx:
                word_list = sorted([(pos, w) for w, positions in abs_idx.items() for pos in positions])
                abstract = " ".join([w[1] for w in word_list])
            
            url = i.get("ids", {}).get("openalex", i.get("id"))
            doi = i.get("doi")
            if doi: doi = doi.replace("https://doi.org/", "")
            
            # Metrics & PDF
            citations = i.get("cited_by_count", 0)
            pdf_url = i.get("open_access", {}).get("oa_url", "N/A")

            res.append({
                "title": i.get("display_name"), 
                "journal": i.get("primary_location",{}).get("source",{}).get("display_name","OpenAlex"),
                "year": str(i.get("publication_year","")), 
                "authors": auth, 
                "abstract": abstract, 
                "source": "OpenAlex", 
                "url": url,
                "citations": citations,
                "pdf_url": pdf_url,
                "doi": doi
            })
        return res

# --- 5. PLOS Client ---
class PlosClient:
    BASE_URL = "http://api.plos.org/search"
    def search(self, term, start_year=None, max_results=5):
        try:
            # Boolean logic works natively in Solr/PLOS ("DNA" AND "RNA")
            q = f'title:"{term}" OR abstract:"{term}"'
            if start_year:
                 q += f' AND publication_date:[{start_year}-01-01T00:00:00Z TO *]'
            
            r = requests.get(self.BASE_URL, params={"q": q, "wt":"json", "rows":max_results, "fl":"id,title,journal,auth_display,abstract,publication_date,score"}, timeout=10).json()
            return self._parse(r)
        except: return []
    def _parse(self, data):
        res = []
        for d in data.get("response", {}).get("docs", []):
            doi = d.get("id", "")
            url = f"https://journals.plos.org/plosone/article?id={doi}" if doi else "N/A"
            res.append({
                "title": d.get("title"), "journal": d.get("journal","PLOS"), 
                "year": d.get("publication_date","")[:4], "authors": ",".join(d.get("auth_display",[])), 
                "abstract": str(d.get("abstract",["N/A"])[0]), "source": "PLOS", "url": url,
                "citations": "N/A", "pdf_url": "N/A", "doi": doi
            })
        return res

# --- MAIN MANAGER ---
class UnifiedSearchManager:
    def __init__(self):
        self.clients = {
            "PubMed": PubMedWrapper(),
            "Semantic Scholar": SemanticScholarClient(),
            "Europe PMC": EuropePmcClient(),
            "OpenAlex": OpenAlexClient(),
            "PLOS": PlosClient()
        }
        
        self.priority_order = [
            "PubMed", 
            "Semantic Scholar", 
            "Europe PMC", 
            "OpenAlex", 
            "PLOS"
        ]

    def search_all(self, term, active_sources=None, limit_per_source=5, start_year=None):
        """
        Main entry point. 
        start_year: int (e.g., 2018). If None, defaults to 10 years ago to ensure recency.
        """
        if active_sources is None: active_sources = self.clients.keys()
        
        # Default Recency Logic (Last 10 years if not specified)
        if start_year is None:
            start_year = get_current_year() - 10

        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            for name in active_sources:
                if name in self.clients:
                    # Pass the start_year to all clients
                    future_to_source[executor.submit(self.clients[name].search, term, start_year, limit_per_source)] = name
            
            for future in concurrent.futures.as_completed(future_to_source):
                try:
                    data = future.result()
                    all_results.extend(data)
                except Exception: pass

        # 1. Merge duplicates
        merged = self._merge_and_deduplicate(all_results)
        
        # 2. Enrich missing data (Cross-Referencing Logic)
        enriched = self._enrich_missing_data(merged)
        
        # 3. Sort by Impact (Citation count)
        enriched.sort(key=lambda x: int(x.get('citations', 0)) if isinstance(x.get('citations'), int) else 0, reverse=True)
        
        return enriched

    def _merge_and_deduplicate(self, all_items):
        def get_priority(item):
            src = item.get('source', '')
            if src in self.priority_order:
                return self.priority_order.index(src)
            return 99
        
        all_items.sort(key=get_priority)

        final_list = []
        seen_titles = set()
        
        def normalize(text): 
            return "".join(e for e in str(text) if e.isalnum()).lower()

        for item in all_items:
            title = item.get('title', '')
            norm_title = normalize(title)
            if not norm_title: continue
            
            if norm_title not in seen_titles:
                seen_titles.add(norm_title)
                final_list.append(item)
                
        return final_list

    def _enrich_missing_data(self, results):
        """
        Cross-Referencing: If abstract is missing but DOI exists, query OpenAlex/SemanticScholar
        to fill the holes.
        """
        for item in results:
            abstract = item.get('abstract', '')
            doi = item.get('doi')
            
            is_empty = not abstract or abstract == "No Abstract Available." or len(abstract) < 50
            
            if is_empty and doi:
                # Try to fetch from OpenAlex using DOI (It's fast and free)
                try:
                    clean_doi = doi.replace("https://doi.org/", "")
                    url = f"https://api.openalex.org/works/https://doi.org/{clean_doi}"
                    r = requests.get(url, timeout=3)
                    if r.status_code == 200:
                        data = r.json()
                        # Extract Abstract
                        abs_idx = data.get("abstract_inverted_index")
                        if abs_idx:
                            word_list = sorted([(pos, w) for w, positions in abs_idx.items() for pos in positions])
                            new_abstract = " ".join([w[1] for w in word_list])
                            item['abstract'] = new_abstract + " [Enriched via OpenAlex]"
                        
                        # Extract PDF if we didn't have one
                        if item.get('pdf_url') == "N/A":
                             item['pdf_url'] = data.get("open_access", {}).get("oa_url", "N/A")
                        
                        # Extract Citations if we didn't have them
                        if item.get('citations') == "N/A":
                             item['citations'] = data.get("cited_by_count", 0)

                except Exception:
                    pass # Fail silently, keep original data
        return results

    def save_data(self, data, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("================================================================\n")
                f.write("  SCIENTIFIC SEARCH RESULTS EXPORT (PRO EDITION)\n")
                f.write("================================================================\n\n")
                
                for i, item in enumerate(data, 1):
                    source = item.get('source', 'Unknown')
                    title = item.get('title', 'No Title')
                    url = item.get('url', 'N/A')
                    pdf = item.get('pdf_url', 'N/A')
                    cites = item.get('citations', 'N/A')
                    authors = item.get('authors', 'N/A')
                    journal = item.get('journal', 'N/A')
                    year = item.get('year', 'N/A')
                    abstract = item.get('abstract', 'No Abstract')

                    f.write(f"Result #{i}  [{source}]\n")
                    f.write(f"Impact: {cites} citations\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"TITLE:    {title}\n")
                    f.write(f"LINK:     {url}\n")
                    f.write(f"PDF:      {pdf}\n")
                    f.write(f"JOURNAL:  {journal} ({year})\n")
                    f.write(f"AUTHORS:  {authors}\n")
                    f.write(f"\nABSTRACT:\n{abstract}\n")
                    f.write("\n" + "="*80 + "\n\n")
            return True
        except IOError: return False