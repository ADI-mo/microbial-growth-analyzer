import requests
import concurrent.futures 
from ncbi_client import NCBIClient

# --- 1. PubMed Wrapper (Priority #1) ---
class PubMedWrapper:
    def __init__(self):
        self.client = NCBIClient()
    
    def search(self, term, max_results=3):
        try:
            ids = self.client.search_pubmed(term, max_results)
            data = self.client.fetch_details(ids)
            
            for item in data:
                item['source'] = "PubMed"
                pmid = item.get('pmid')
                if pmid:
                    item['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                else:
                    item['url'] = "https://pubmed.ncbi.nlm.nih.gov/"
            return data
        except Exception as e:
            print(f"PubMed Error: {e}")
            return []

# --- 2. Semantic Scholar Client (Priority #2) ---
class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def search(self, term, max_results=3):
        params = {
            "query": term, 
            "limit": max_results, 
            "fieldsOfStudy": "Biology,Medicine", 
            "fields": "title,authors,year,abstract,journal,url,isOpenAccess"
        }
        try:
            r = requests.get(self.BASE_URL, params=params, headers={"User-Agent": "Bot"}, timeout=10).json()
            return self._parse(r)
        except: return []

    def _parse(self, data):
        res = []
        for p in data.get("data", []):
            auth = ", ".join([a["name"] for a in p.get("authors", [])[:3]])
            res.append({
                "title": p.get("title"), 
                "journal": p.get("journal",{}).get("name","Semantic Scholar"), 
                "year": str(p.get("year","")), 
                "authors": auth, 
                "abstract": p.get("abstract") or "No Abstract Available.", 
                "source": "Semantic Scholar", 
                "url": p.get("url", "N/A")
            })
        return res

# --- 3. Europe PMC Client (Priority #3) ---
class EuropePmcClient:
    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    def search(self, term, max_results=3):
        query = f"{term} AND (SRC:PPR OR SRC:MED) AND LANGUAGE:english"
        params = {"query": query, "format": "json", "pageSize": max_results}
        try:
            return self._parse(requests.get(self.BASE_URL, params=params, timeout=10).json())
        except: return []

    def _parse(self, data):
        res = []
        for i in data.get("resultList", {}).get("result", []):
            pmid = i.get("id")
            url = f"https://europepmc.org/article/MED/{pmid}" if pmid else "N/A"
            res.append({
                "title": i.get("title"), 
                "journal": i.get("journalInfo",{}).get("journal",{}).get("title","EuropePMC"), 
                "year": i.get("journalInfo",{}).get("yearOfPublication","N/A"), 
                "authors": i.get("authorString",""), 
                "abstract": i.get("abstractText","No Abstract Available."), 
                "source": "EuropePMC", 
                "url": url
            })
        return res

# --- 4. OpenAlex Client (Priority #4) ---
class OpenAlexClient:
    BASE_URL = "https://api.openalex.org/works"
    
    def search(self, term, max_results=3):
        try:
            params = {
                "search": term, 
                "per-page": max_results, 
                "filter": "has_abstract:true,language:en"
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
            
            res.append({
                "title": i.get("display_name"), 
                "journal": i.get("primary_location",{}).get("source",{}).get("display_name","OpenAlex"),
                "year": str(i.get("publication_year","")), 
                "authors": auth, 
                "abstract": abstract, 
                "source": "OpenAlex", 
                "url": url
            })
        return res

# --- 5. PLOS Client (Priority #5) ---
class PlosClient:
    BASE_URL = "http://api.plos.org/search"
    def search(self, term, max_results=3):
        try:
            q = f'title:"{term}" OR abstract:"{term}"'
            r = requests.get(self.BASE_URL, params={"q": q, "wt":"json", "rows":max_results, "fl":"id,title,journal,auth_display,abstract,publication_date"}, timeout=10).json()
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
                "abstract": str(d.get("abstract",["N/A"])[0]), "source": "PLOS", "url": url
            })
        return res

# --- 6. Crossref Client (Priority #6) ---
class CrossrefClient:
    BASE_URL = "https://api.crossref.org/works"
    def search(self, term, max_results=3):
        params = {"query": term, "rows": max_results, "sort": "relevance"}
        try:
            headers = {"User-Agent": "StudentProject/1.0"}
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
            return self._parse(response.json())
        except: return []
    def _parse(self, data):
        results = []
        for item in data.get("message", {}).get("items", []):
            if item.get("language") and "en" not in item.get("language"):
                continue

            title = item.get("title", ["No Title"])[0]
            authors = [f"{a.get('family','')} {a.get('given','')}" for a in item.get("author", [])]
            date_parts = item.get("published-print", {}).get("date-parts", []) or item.get("published-online", {}).get("date-parts", [])
            year = str(date_parts[0][0]) if date_parts else "N/A"
            url = item.get("URL", "N/A")
            results.append({
                "title": title, "journal": item.get("container-title", ["Crossref"])[0],
                "year": year, "authors": ", ".join(authors[:3]),
                "abstract": "Abstract available at link.", "source": "Crossref", "url": url
            })
        return results

# --- MAIN MANAGER ---
# חשוב: זו המחלקה שהייתה חסרה לך בשגיאה הקודמת
class UnifiedSearchManager:
    def __init__(self):
        # Dictionary of clients
        self.clients = {
            "PubMed": PubMedWrapper(),
            "Semantic Scholar": SemanticScholarClient(),
            "Europe PMC": EuropePmcClient(),
            "OpenAlex": OpenAlexClient(),
            "PLOS": PlosClient(),
            "Crossref": CrossrefClient()
        }
        
        # DEFINING THE PRIORITY ORDER
        self.priority_order = [
            "PubMed", 
            "Semantic Scholar", 
            "Europe PMC", 
            "OpenAlex", 
            "PLOS", 
            "Crossref"
        ]

    def search_all(self, term, active_sources=None, limit_per_source=3):
        if active_sources is None: active_sources = self.clients.keys()
        
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            for name in active_sources:
                if name in self.clients:
                    future_to_source[executor.submit(self.clients[name].search, term, limit_per_source)] = name
            
            for future in concurrent.futures.as_completed(future_to_source):
                try:
                    data = future.result()
                    all_results.extend(data)
                except Exception: pass

        return self._merge_and_deduplicate(all_results)

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

    def save_data(self, data, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("================================================================\n")
                f.write("  SCIENTIFIC SEARCH RESULTS EXPORT\n")
                f.write("================================================================\n\n")
                
                for i, item in enumerate(data, 1):
                    source = item.get('source', 'Unknown Source')
                    title = item.get('title', 'No Title')
                    url = item.get('url', 'N/A')
                    authors = item.get('authors', 'N/A')
                    journal = item.get('journal', 'N/A')
                    year = item.get('year', 'N/A')
                    abstract = item.get('abstract', 'No Abstract')

                    f.write(f"Result #{i}  [{source}]\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"TITLE:    {title}\n")
                    f.write(f"LINK:     {url}\n")
                    f.write(f"JOURNAL:  {journal} ({year})\n")
                    f.write(f"AUTHORS:  {authors}\n")
                    f.write(f"\nABSTRACT:\n{abstract}\n")
                    f.write("\n" + "="*80 + "\n\n")
            return True
        except IOError: return False