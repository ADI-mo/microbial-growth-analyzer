import requests
import concurrent.futures
import datetime
import csv
import re
from ncbi_client import NCBIClient

def get_current_year():
    return datetime.datetime.now().year

# --- 1. PubMed Wrapper ---
class PubMedWrapper:
    def __init__(self):
        self.client = NCBIClient()
    
    def search(self, term, start_year=None, max_results=5, only_free=False):
        try:
            final_term = term
            if start_year:
                current_year = get_current_year()
                final_term += f" AND {start_year}:{current_year}[dp]"
            
            if only_free:
                final_term += " AND (free full text[Filter])"

            ids = self.client.search_pubmed(final_term, max_results)
            data = self.client.fetch_details(ids)
            
            for item in data:
                item['source'] = "PubMed"
                item['citations'] = 0 
                item['pdf_url'] = "Check Link"
                pmid = item.get('pmid')
                item['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "https://pubmed.ncbi.nlm.nih.gov/"
            return data
        except Exception as e:
            print(f"PubMed Error: {e}")
            return []

# --- 2. Semantic Scholar Client ---
class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def search(self, term, start_year=None, max_results=5, only_free=False):
        params = {
            "query": term, 
            "limit": max_results, 
            "fieldsOfStudy": "Biology,Medicine",
            "fields": "title,authors,year,abstract,journal,url,isOpenAccess,openAccessPdf,citationCount,externalIds"
        }
        if start_year:
            params["year"] = f"{start_year}-{get_current_year()}"
        
        try:
            r = requests.get(self.BASE_URL, params=params, headers={"User-Agent": "Bot"}, timeout=10).json()
            results = self._parse(r)
            if only_free:
                return [r for r in results if r['pdf_url'] != "N/A"]
            return results
        except: return []

    def _parse(self, data):
        res = []
        for p in data.get("data", []):
            auth = ", ".join([a["name"] for a in p.get("authors", [])[:3]])
            pdf_link = p.get("openAccessPdf", {}).get("url", "N/A") if p.get("openAccessPdf") else "N/A"
            doi = p.get("externalIds", {}).get("DOI")

            res.append({
                "title": p.get("title") or "Unknown Title", 
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
    
    def search(self, term, start_year=None, max_results=5, only_free=False):
        query = term
        if start_year:
            query += f" AND PUB_YEAR:[{start_year} TO {get_current_year()}]"
        if only_free:
            query += " AND (OPEN_ACCESS:y)"

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
            cites = i.get("citedByCount", 0)
            
            pdf = "N/A"
            if i.get("fullTextUrlList"):
                for link in i.get("fullTextUrlList", {}).get("fullTextUrl", []):
                    if link.get("documentStyle") == "pdf":
                        pdf = link.get("url")
                        break

            res.append({
                "title": i.get("title") or "Unknown Title", 
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
    
    def search(self, term, start_year=None, max_results=5, only_free=False):
        try:
            filters = "has_abstract:true,language:en,type:article"
            if start_year:
                filters += f",from_publication_date:{start_year}-01-01"
            if only_free:
                filters += ",is_oa:true"

            params = {
                "search": term, 
                "per-page": max_results, 
                "filter": filters,
                "sort": "cited_by_count:desc"
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
            
            citations = i.get("cited_by_count", 0)
            pdf_url = i.get("open_access", {}).get("oa_url", "N/A")

            res.append({
                "title": i.get("display_name") or "Unknown Title", 
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
    def search(self, term, start_year=None, max_results=5, only_free=False):
        try:
            q = f'title:"{term}" OR abstract:"{term}"'
            if start_year:
                 q += f' AND publication_date:[{start_year}-01-01T00:00:00Z TO *]'
            
            r = requests.get(self.BASE_URL, params={"q": q, "wt":"json", "rows":max_results, "fl":"id,title,journal,author_display,abstract,publication_date,score"}, timeout=10).json()
            return self._parse(r)
        except: return []
    
    def _parse(self, data):
        res = []
        for d in data.get("response", {}).get("docs", []):
            doi = d.get("id", "")
            url = f"https://journals.plos.org/plosone/article?id={doi}" if doi else "N/A"
            authors_list = d.get("author_display", []) or d.get("auth_display", [])
            authors_str = ", ".join(authors_list) if isinstance(authors_list, list) else str(authors_list)

            res.append({
                "title": d.get("title") or "Unknown Title", 
                "journal": d.get("journal","PLOS"), 
                "year": d.get("publication_date","")[:4], 
                "authors": authors_str, 
                "abstract": str(d.get("abstract",["N/A"])[0]), 
                "source": "PLOS", 
                "url": url,
                "citations": 0, 
                "pdf_url": url,
                "doi": doi
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

    def _extract_year(self, date_str):
        if not date_str: return "N/A"
        try:
            return str(int(float(str(date_str))))
        except:
            match = re.search(r'\d{4}', str(date_str))
            return match.group(0) if match else "N/A"

    def calculate_score(self, paper, query):
        score = 0
        if not query: return 0
        
        query_terms = query.lower().split()
        title_lower = (paper.get('title') or '').lower()
        abstract_lower = (paper.get('abstract') or '').lower()

        for term in query_terms:
            if term in title_lower:
                score += 100
            elif term in abstract_lower:
                score += 10
        return score

    def search_all(self, term, active_sources=None, limit_per_source=5, start_year=None, only_free=False):
        if active_sources is None: active_sources = self.clients.keys()
        
        if start_year is None:
            start_year = get_current_year() - 10

        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            for name in active_sources:
                if name in self.clients:
                    future_to_source[executor.submit(self.clients[name].search, term, start_year, limit_per_source, only_free)] = name
            
            for future in concurrent.futures.as_completed(future_to_source):
                try:
                    data = future.result()
                    all_results.extend(data)
                except Exception: pass

        merged = self._merge_and_deduplicate(all_results)
        enriched = self._enrich_missing_data(merged)
        
        # --- Scoring & Sorting ---
        for paper in enriched:
            paper['year'] = self._extract_year(paper.get('year'))
            paper['relevance_score'] = self.calculate_score(paper, term)
            cites = paper.get('citations')
            if not isinstance(cites, int):
                paper['citations'] = 0

        enriched.sort(key=lambda x: (-x['relevance_score'], -x['citations']))
        
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
        for item in results:
            doi = item.get('doi')
            abstract_text = item.get('abstract') or ""
            needs_abstract = len(abstract_text) < 50
            needs_citations = item.get('citations') == 0
            
            if (needs_abstract or needs_citations) and doi:
                try:
                    clean_doi = doi.replace("https://doi.org/", "")
                    url = f"https://api.openalex.org/works/https://doi.org/{clean_doi}"
                    r = requests.get(url, timeout=3)
                    if r.status_code == 200:
                        data = r.json()
                        if needs_abstract:
                            abs_idx = data.get("abstract_inverted_index")
                            if abs_idx:
                                word_list = sorted([(pos, w) for w, positions in abs_idx.items() for pos in positions])
                                new_abstract = " ".join([w[1] for w in word_list])
                                item['abstract'] = new_abstract + " [Enriched]"
                        if item.get('pdf_url') == "N/A":
                             item['pdf_url'] = data.get("open_access", {}).get("oa_url", "N/A")
                        if needs_citations:
                             item['citations'] = data.get("cited_by_count", 0)
                except Exception: pass
        return results

    def save_to_csv(self, data, filename):
        keys = ["source", "title", "citations", "relevance_score", "year", "journal", "authors", "url", "pdf_url", "abstract"]
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for item in data:
                    filtered_item = {k: item.get(k, "N/A") for k in keys}
                    writer.writerow(filtered_item)
            return True
        except Exception as e:
            print(f"CSV Error: {e}")
            return False

    def save_to_text(self, data, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("SCIENTIFIC SEARCH RESULTS\n")
                f.write("=========================\n\n")
                for i, item in enumerate(data, 1):
                    f.write(f"Result #{i}\n")
                    f.write(f"Title: {item.get('title')}\n")
                    f.write(f"Source: {item.get('source')} | Year: {item.get('year')}\n")
                    f.write(f"Citations: {item.get('citations')} | Relevance: {item.get('relevance_score')}\n")
                    f.write(f"Link: {item.get('url')}\n")
                    f.write(f"Abstract: {item.get('abstract')}\n")
                    f.write("-" * 50 + "\n\n")
            return True
        except Exception as e:
            print(f"TXT Error: {e}")
            return False