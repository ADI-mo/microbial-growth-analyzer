from unified_client import UnifiedSearchManager

# יצירת המנהל
manager = UnifiedSearchManager()

print("Testing Europe PMC only...")

# אנו שולחים רשימה שמכילה רק את המקור הזה
# זה ימנע מ-PubMed למחוק אותו
results = manager.search_all("PCR", active_sources=["Europe PMC"])

if len(results) > 0:
    print(f"✅ Success! Found {len(results)} articles from Europe PMC:")
    for item in results:
        print(f"- {item['title']} (Source: {item['source']})")
else:
    print("❌ No results found. Something might be wrong with the API.")