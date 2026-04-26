import os
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from tavily import TavilyClient
from groq import Groq
import json
import time
import re

load_dotenv()

MODEL_NAME = "openai/gpt-oss-120b"

def search_internet(query: str, anchor: str) -> list:
    """Multi-anchor search with hard-coded imposter exclusion."""
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        # Split anchors for multi-term matching
        anchor_list = [a.strip() for a in anchor.split(',')]
        anchor_query = " OR ".join([f'"{a}"' for a in anchor_list])
        
        # Build strict query with negative filters to block the NSW Police imposter
        strict_query = f'"{query}" ({anchor_query}) -NSW -"Police Force" -Australia -Compliance'
        
        response = tavily.search(query=strict_query, search_depth="advanced", max_results=10)
        results = response.get('results', [])
        
        filtered = []
        for r in results:
            content = r.get('content', '').lower()
            title = r.get('title', '').lower()
            # Verify that at least one anchor is actually present
            if any(a.lower() in content or a.lower() in title for a in anchor_list):
                filtered.append({
                    'title': r.get('title'),
                    'content': content[:1000]
                })
        return filtered
    except: return []

def sanitize_list(data, fallback=None):
    if isinstance(data, list) and len(data) > 0:
        return [str(i) for i in data if i]
    return fallback if fallback is not None else []

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS': return Response(status=204)
    data = request.json
    target_name = data.get('name', 'Unknown')
    anchor_fact = data.get('context', '')
    linkedin_url = data.get('linkedin_url', '')

    def generate():
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': f'ID_PURGE: EXCLUDING_IMPOSTERS_FOR_{anchor_fact.upper()}...'})}\n\n"
        
        results = search_internet(target_name, anchor_fact)
        evidence_text = "\n".join([f"FACT: {r['title']} | DETAILS: {r['content']}" for r in results])
        
        # STAGE 1: BANTER
        banter_prompt = f"""
        SYSTEM: You are a jaded Digital Forensic investigator. 
        MANDATORY: Analyze "{target_name}" ({anchor_fact}). 
        STRICT: The "NSW Police" or "Australia" profiles are IMPOSTERS. DISCARD THEM.
        ONLY mention details linked to {anchor_fact} (Oxford, Sequentis, etc.).
        DATA: {evidence_text[:3500]}
        
        TASK: Output 4 snarky banter lines. Format Agent_Name: [Message].
        """
        
        try:
            banter_res = client.chat.completions.create(model=MODEL_NAME, messages=[{"role": "user", "content": banter_prompt}], temperature=0.85).choices[0].message.content
            for line in banter_res.split('\n'):
                if ":" in line:
                    agent = line.split(":")[0].strip()
                    msg = line.split(":")[-1].strip()
                    yield f"data: {json.dumps({'type': 'log', 'agent': agent, 'message': msg})}\n\n"
                    time.sleep(2.0)
        except: pass

        # STAGE 2: REPORT
        yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'SYNTHESIZING_VERIFIED_MANIFEST...'})}\n\n"
        
        report_prompt = f"""
        SYSTEM: Generate a high-fidelity JSON report for {target_name}.
        EVIDENCE: {evidence_text[:5000]}
        
        MANDATORY IDENTITY RULES:
        - Target is linked to: {anchor_fact}.
        - The "Application Analyst at NSW Police Force" is a DIFFERENT person. DO NOT use their data.
        - Discard any mention of Payment Security or Australia.
        
        JSON SCHEMA:
        - persona_sync: 0-100
        - classification: [4 specific professional traits]
        - persona_label: Funny professional title.
        - subliminal_observation: 2 sentences of professional irony based on {anchor_fact} findings.
        - anchor_facts: [List of 6-8 verified facts found in evidence]
        - timeline_2040: Surreal narrative destiny (NOT A LIST).
        - nemesis_persona: Archetype.
        - nemesis_rivalry: One petty sentence.

        STRICT: OUTPUT JSON ONLY.
        """
        
        try:
            report_res = client.chat.completions.create(model=MODEL_NAME, messages=[{"role": "user", "content": report_prompt}], temperature=0.7).choices[0].message.content
            json_match = re.search(r"(\{.*\})", report_res, re.DOTALL)
            res = json.loads(json_match.group(1)) if json_match else {}
            
            yield f"data: {json.dumps({
                'type': 'result',
                'name': target_name,
                'integrity_score': res.get('persona_sync', 75),
                'classification_list': sanitize_list(res.get('classification'), ["Identity Locked"]),
                'persona_label': str(res.get('persona_label', 'VERIFIED_SUBJECT')),
                'brutal_roast': str(res.get('subliminal_observation', 'Forensic trail established.')),
                'anchor_facts': sanitize_list(res.get('anchor_facts'), [f"Linked to {anchor_fact}"]),
                'future_milestone': str(res.get('timeline_2040', 'Trajectory locked.')),
                'nemesis_persona': str(res.get('nemesis_persona', 'Unknown')),
                'nemesis_rivalry': str(res.get('nemesis_rivalry', 'A petty dispute.'))
            })}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': f'REASONING_ERROR: {str(e)}'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
