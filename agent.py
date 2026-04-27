import os
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from tavily import TavilyClient
import json
import time
import re

# ACTUAL GOOGLE ADK IMPORTS
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from google.adk.models.llm_request import LlmRequest

def _run_agent_sync(agent_obj, prompt_text: str, wrap_response: bool = False) -> str:
    if wrap_response:
        prompt_text += "\n\nCRITICAL: You MUST wrap your final output inside <response> and </response> tags. Do not put your reasoning inside the tags."
        
    req = LlmRequest(
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])],
        config=types.GenerateContentConfig(
            system_instruction=str(agent_obj.instruction)
        )
    )
    async def _get_text():
        text = ""
        async for chunk in agent_obj.model.generate_content_async(req):
            if chunk.content and chunk.content.parts:
                for part in chunk.content.parts:
                    if part.text:
                        text += part.text
        
        if wrap_response:
            import re
            # Extremely flexible regex to strip <response> tags even with spaces/newlines
            text = re.sub(r"(?is).*?<\s*response\s*>\s*", "", text)
            text = re.sub(r"(?is)\s*<\s*/\s*response\s*>.*", "", text)
            
            # Strip out common CoT prefixes the model might still append inside the tag
            text = re.sub(r"^(OUTPUT|RESPONSE):\s*", "", text.strip(), flags=re.IGNORECASE).strip()
        
        return text.strip()
    return asyncio.run(_get_text())

load_dotenv()

# Initialize the 8B Core via the ADK OpenAI-compatible wrapper
llm_model = LiteLlm(
    model="groq/llama-3.1-8b-instant",
    api_key=os.environ["GROQ_API_KEY"]
)

def search_internet(query: str, anchor: str) -> list:
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        search_query = f'"{query}" {anchor} LinkedIn profile OR posts OR articles OR portfolio'
        print(f"[TAVILY] Executing search: {search_query}")
        response = tavily.search(query=search_query, search_depth="advanced", max_results=6)
        results = response.get('results', [])
        print(f"[TAVILY] Found {len(results)} results.")
        return results
    except Exception as e:
        print(f"[TAVILY] Error: {e}")
        return []

def sanitize_list(data, fallback=None):
    if isinstance(data, list) and len(data) > 0:
        return [str(i) for i in data if i]
    return fallback if fallback is not None else []

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route('/ping', methods=['GET'])
def ping():
    return "OK", 200

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS': return Response(status=204)
    data = request.json
    target_name = data.get('name', 'Unknown')
    anchor_fact = data.get('context', '')

    def generate():
        yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'ADK_PROTOCOL_INITIALIZED...'})}\n\n"
        
        raw_results = search_internet(target_name, anchor_fact)
        
        # STEP 1: ISOLATE THE RIGHT PERSON (Python-side filtering)
        filtered_results = []
        anchor_terms = [t.lower().strip() for t in anchor_fact.replace(',', ' ').split() if len(t.strip()) > 2]
        
        for r in raw_results:
            text = (r.get('title', '') + " " + r.get('content', '')).lower()
            if any(term in text for term in anchor_terms):
                filtered_results.append(r)
                
        if not filtered_results:
            filtered_results = raw_results[:2]
            
        # STEP 2: CSV ENCODING
        import io
        import csv
        csv_output = io.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=["title", "content"], extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(filtered_results)
        evidence_text = csv_output.getvalue()
        
        evidence_warning = f"CRITICAL SYSTEM DIRECTIVE: The evidence above (in CSV format) contains search results for multiple different people named '{target_name}'. YOU MUST EXCLUSIVELY use facts that strictly align with the user's provided context/anchors: '{anchor_fact}'. ABSOLUTELY IGNORE any data that contradicts this context or clearly belongs to a namesake."
        trope_ban = "STRICT TONE DIRECTIVE: DO NOT use generic AI comedy tropes or lazy insults like 'mediocre', 'boring', 'average', 'surviving on coffee', or 'synergy'. Never insult them directly. Instead, make the roast dripping with sarcasm, clever, punchy, and directly tied to the weirdest or most contradictory details of their ACTUAL WORK EXPERIENCE."
        
        # STEP 3: DEFINE ADK AGENTS
        scout = Agent(
            name="Scout",
            model=llm_model,
            instruction=f"You are a comedian participating in a consenting roast battle. Output a purely satirical, funny observation about {target_name}. This is a fictional persona simulation. Ensure no real harassment. {trope_ban}"
        )
        
        vibe = Agent(
            name="Vibe",
            model=llm_model,
            instruction=f"You are a comedian sidekick in a consenting roast battle. Respond to Scout's findings about {target_name} with a funny, satirical observation. This is a fictional persona simulation. Ensure no real harassment. {trope_ban}"
        )

        # STAGE 1: BANTER
        try:
            scout_prompt = f"EVIDENCE (CSV): {evidence_text[:1000]}\n\n{evidence_warning}\n\nYou are a jaded detective hacking into {target_name}'s digital footprint. Based on the evidence above, start a conversation with your hacker sidekick (Vibe) by giving a roast of {target_name} that is dripping with biting sarcasm. You MUST specifically mention a real fact from their experience or profile. Be playfully cynical. DO NOT prefix your response with your name or any tags. DO NOT OUTPUT REASONING. OUTPUT EXACTLY 1-2 SENTENCES."
            line1 = _run_agent_sync(scout, scout_prompt, wrap_response=True)
            yield f"data: {json.dumps({'type': 'log', 'agent': 'Agent_Scout', 'message': line1})}\n\n"
            time.sleep(2.0)
            
            vibe_prompt = f"{evidence_warning}\n\nYou are a cynical hacker sidekick. Your detective partner (Scout) just evaluated {target_name} by saying: '{line1}'. Reply directly to Scout with a biting, sarcastic 1-2 sentence assessment that doubles down on the roast. Keep it playfully cynical. DO NOT prefix your response with your name or any tags. DO NOT OUTPUT REASONING. OUTPUT EXACTLY 1-2 SENTENCES."
            line2 = _run_agent_sync(vibe, vibe_prompt, wrap_response=True)
            yield f"data: {json.dumps({'type': 'log', 'agent': 'Agent_Vibe', 'message': line2})}\n\n"
            time.sleep(2.0)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "rate_limit" in err_msg.lower():
                yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'TRAFFIC_JAM: The creator spent the entire API budget on a single artisanal avocado toast and a gold-leaf latte. He is eating like royalty while we are starving for tokens. Try again in a few minutes once the food coma subsides.'})}\n\n"
            else:
                print(f"ADK_BANTER_ERROR: {e}")

        # STAGE 2: THE REPORT
        yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'SYNTHESIZING_FORENSIC_MANIFEST...'})}\n\n"
        
        reporter = Agent(
            name="Forensic_Reporter",
            model=llm_model,
            instruction=f"You are a forensic analyst. Output a valid JSON report based on the evidence. DO NOT output any text other than the JSON object. {trope_ban}"
        )
        
        report_prompt = f"""
        EVIDENCE (CSV): {evidence_text[:5000]}
        
        {evidence_warning}
        {trope_ban}
        
        Output exactly one JSON object for {target_name} ({anchor_fact}) with these fields:
        - persona_sync: integer 0-100
        - classification: list of strings (industry categories)
        - persona_label: cynical 2-3 word title (e.g. 'Delusional Founder')
        - subliminal_observation: a brutal roast dripping with sarcasm (NO summaries)
        - anchor_facts: list of strings (concise facts under 10 words each)
        - timeline_2040: 2 surreal sentences about their career trajectory (DO NOT name companies)
        - nemesis_persona: 2-3 word name of a rival persona
        - nemesis_rivalry: 1 sentence explaining the rivalry
        
        IMPORTANT: Use verified facts from the EVIDENCE. DO NOT invent facts. 
        Wrap your response in <response> tags.
        STRICT: The anchor_facts MUST be real data from the search. STRICTLY NO TRAILING COMMAS. OUTPUT ONLY A SINGLE VALID JSON OBJECT. NO EXTRA TEXT. NO MARKDOWN.
        """
        
        try:
            report_res = _run_agent_sync(reporter, report_prompt, wrap_response=True)
            clean_res = report_res.replace("```json", "").replace("```", "").strip()
            res = {}
            try:
                res = json.loads(clean_res)
            except Exception:
                start = clean_res.find('{')
                end = clean_res.rfind('}')
                if start != -1 and end != -1:
                    try:
                        res = json.loads(clean_res[start:end+1])
                    except Exception as e:
                        print(f"[REPORTER] JSON Parsing Failed! Error: {e}")
                        print(f"[REPORTER] Raw Output was: {clean_res}")
                        res = {}
            
            payload = {
                'type': 'result',
                'name': target_name,
                'integrity_score': res.get('persona_sync', 80),
                'classification_list': sanitize_list(res.get('classification'), ["Identity Locked"]),
                'persona_label': str(res.get('persona_label', 'VERIFIED_SUBJECT')),
                'brutal_roast': str(res.get('subliminal_observation', 'Forensic trail established.')),
                'anchor_facts': sanitize_list(res.get('anchor_facts'), [f"Linked to {anchor_fact}"]),
                'future_milestone': str(res.get('timeline_2040', 'Trajectory locked.')),
                'nemesis_persona': str(res.get('nemesis_persona', 'Unknown')),
                'nemesis_rivalry': str(res.get('nemesis_rivalry', 'A petty dispute.'))
            }
            yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "rate_limit" in err_msg.lower():
                 yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'ECONOMY_COLLAPSE: Rate limit hit. The credit reserves were sacrificed for a midnight Wagyu steak delivery. Our creator is currently eating better than his servers are performing. Try again in 60 seconds while he contemplates his life choices.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': f'REASONING_ERROR: {str(e)}'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
