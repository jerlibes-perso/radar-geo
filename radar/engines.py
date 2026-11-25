"""Appels aux 5 moteurs, recherche web activée. Chaque fonction renvoie
{"texte": str, "sources": [{"url": str, "titre": str}], "modele": str}."""
import json, os, time, urllib.request, urllib.error

SYSTEME = ("Réponds en français à la question d'un internaute, comme dans une conversation. "
           "Cherche sur le web et cite tes sources.")


def _post(url, headers, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={**headers, "Content-Type": "application/json"}, method="POST")
    for essai in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            corps = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503, 529) and essai < 2:
                time.sleep(20 * (essai + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} : {corps}")
        except urllib.error.URLError:
            if essai < 2:
                time.sleep(10)
                continue
            raise


def openai(q, cfg, loc):
    key = os.environ["OPENAI_API_KEY"]
    d = _post("https://api.openai.com/v1/responses", {"Authorization": f"Bearer {key}"}, {
        "model": cfg["modele"], "instructions": SYSTEME, "input": q,
        "tools": [{"type": "web_search", "user_location": {"type": "approximate", "country": loc["pays"], "city": loc["ville"], "region": loc["region"], "timezone": loc["fuseau"]}}],
        "include": ["web_search_call.action.sources"]})
    texte, sources = "", []
    for item in d.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    texte += c.get("text", "")
                    for a in c.get("annotations", []):
                        if a.get("type") == "url_citation":
                            sources.append({"url": a.get("url", ""), "titre": a.get("title", ""), "citee": True})
        if item.get("type") == "web_search_call":
            for s in (item.get("action") or {}).get("sources", []) or []:
                sources.append({"url": s.get("url", ""), "titre": s.get("title", ""), "citee": False})
    return {"texte": texte, "sources": sources, "modele": d.get("model", cfg["modele"])}


def anthropic(q, cfg, loc):
    key = os.environ["ANTHROPIC_API_KEY"]
    d = _post("https://api.anthropic.com/v1/messages", {"x-api-key": key, "anthropic-version": "2023-06-01"}, {
        "model": cfg["modele"], "max_tokens": 1200, "system": SYSTEME,
        "messages": [{"role": "user", "content": q}],
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 2,
                   "user_location": {"type": "approximate", "city": loc["ville"], "region": loc["region"], "country": loc["pays"], "timezone": loc["fuseau"]}}]})
    texte, sources = "", []
    for b in d.get("content", []):
        if b.get("type") == "text":
            texte += b.get("text", "")
            for c in b.get("citations") or []:
                sources.append({"url": c.get("url", ""), "titre": c.get("title", ""), "citee": True})
        elif b.get("type") == "web_search_tool_result":
            for r in b.get("content") or []:
                if isinstance(r, dict) and r.get("url"):
                    sources.append({"url": r["url"], "titre": r.get("title", ""), "citee": False})
    return {"texte": texte, "sources": sources, "modele": d.get("model", cfg["modele"])}


def gemini(q, cfg, loc):
    key = os.environ["GEMINI_API_KEY"]
    d = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['modele']}:generateContent?key={key}", {}, {
        "systemInstruction": {"parts": [{"text": SYSTEME + f" L'internaute se trouve à {loc['ville']}, en France."}]},
        "contents": [{"role": "user", "parts": [{"text": q}]}],
        "tools": [{"google_search": {}}]})
    cand = (d.get("candidates") or [{}])[0]
    texte = "".join(p.get("text", "") for p in (cand.get("content") or {}).get("parts", []))
    sources = []
    for ch in (cand.get("groundingMetadata") or {}).get("groundingChunks", []) or []:
        w = ch.get("web") or {}
        # l'URL est une redirection Google ; le titre porte le domaine de la source
        sources.append({"url": w.get("uri", ""), "titre": w.get("title", ""), "domaine": w.get("domain", "") or w.get("title", ""), "citee": True})
    return {"texte": texte, "sources": sources, "modele": cfg["modele"]}


def perplexity(q, cfg, loc):
    key = os.environ["PERPLEXITY_API_KEY"]
    d = _post("https://api.perplexity.ai/chat/completions", {"Authorization": f"Bearer {key}"}, {
        "model": cfg["modele"], "messages": [{"role": "system", "content": SYSTEME}, {"role": "user", "content": q}],
        "web_search_options": {"search_context_size": "low", "user_location": {"country": loc["pays"], "city": loc["ville"], "region": loc["region"]}}})
    texte = d["choices"][0]["message"]["content"]
    sources = [{"url": u, "titre": "", "citee": True} for u in d.get("citations", []) or []]
    for s in d.get("search_results", []) or []:
        if s.get("url") and not any(x["url"] == s["url"] for x in sources):
            sources.append({"url": s["url"], "titre": s.get("title", ""), "citee": False})
    return {"texte": texte, "sources": sources, "modele": d.get("model", cfg["modele"])}


def mistral(q, cfg, loc):
    key = os.environ.get("MISTRAL_API_KEY") or os.environ["MISTRAL_KEY"]
    d = _post("https://api.mistral.ai/v1/conversations", {"Authorization": f"Bearer {key}"}, {
        "model": cfg["modele"], "instructions": SYSTEME + f" L'internaute se trouve à {loc['ville']}, en France.",
        "inputs": q, "tools": [{"type": "web_search"}], "store": False})
    texte, sources = "", []
    for o in d.get("outputs", []):
        if o.get("type") == "message.output":
            cont = o.get("content")
            if isinstance(cont, str):
                texte += cont
            else:
                for c in cont or []:
                    if c.get("type") == "text":
                        texte += c.get("text", "")
                    elif c.get("type") == "tool_reference" and c.get("url"):
                        sources.append({"url": c["url"], "titre": c.get("title", ""), "citee": True})
    return {"texte": texte, "sources": sources, "modele": cfg["modele"]}


MOTEURS = {"openai": openai, "anthropic": anthropic, "gemini": gemini, "perplexity": perplexity, "mistral": mistral}
CLES = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "perplexity": "PERPLEXITY_API_KEY", "mistral": "MISTRAL_API_KEY"}
