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
            # Extract everything after the opening tag
            if re.search(r"<response>", text, re.IGNORECASE):
                text = re.split(r"<response>", text, flags=re.IGNORECASE)[-1]
            
            # Extract everything before the closing tag (if it exists)
            if re.search(r"</response>", text, re.IGNORECASE):
                text = re.split(r"</response>", text, flags=re.IGNORECASE)[0]
            
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
        # 8B models struggle with filtering namesakes internally, so we filter the data first.
        filtered_results = []
        anchor_terms = [t.lower().strip() for t in anchor_fact.replace(',', ' ').split() if len(t.strip()) > 2]
        
        for r in raw_results:
            text = (r.get('title', '') + " " + r.get('content', '')).lower()
            if any(term in text for term in anchor_terms):
                filtered_results.append(r)
                
        # If the filter wipes out everything, fallback to the top 2 results
        if not filtered_results:
            filtered_results = raw_results[:2]
            
        # STEP 2: CSV ENCODING (Lossless Token Reduction)
        import io
        import csv
        csv_output = io.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=["title", "content"], extrasaction='ignore', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(filtered_results)
        evidence_text = csv_output.getvalue()
        
        evidence_warning = f"CRITICAL SYSTEM DIRECTIVE: The evidence above (in CSV format) contains search results for multiple different people named '{target_name}'. YOU MUST EXCLUSIVELY use facts that strictly align with the user's provided context/anchors: '{anchor_fact}'. ABSOLUTELY IGNORE any data that contradicts this context or clearly belongs to a namesake."
        trope_ban = "STRICT TONE DIRECTIVE: DO NOT use generic AI comedy tropes or lazy insults like 'mediocre', 'boring', 'average', 'surviving on coffee', or 'synergy'. Never insult them directly. Instead, make the roast clever, punchy, and directly tied to the weirdest or most contradictory details of their ACTUAL WORK EXPERIENCE."
        
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

        # STAGE 1: BANTER (ADK POWERED)
        try:
            # We simulate the multi-agent exchange via ADK generations
            scout_prompt = f"EVIDENCE (CSV): {evidence_text[:1000]}\n\n{evidence_warning}\n\nYou are a jaded detective hacking into {target_name}'s digital footprint. Based on the evidence above, start a conversation with your hacker sidekick (Vibe) by giving a highly satirical, witty 1-2 sentence roast of {target_name}. You MUST specifically mention a real fact from their experience or profile. Be playfully cynical. DO NOT OUTPUT REASONING OR THOUGHT PROCESS. OUTPUT EXACTLY 1-2 SENTENCES."
            line1 = _run_agent_sync(scout, scout_prompt, wrap_response=True)
            yield f"data: {json.dumps({'type': 'log', 'agent': 'Agent_Scout', 'message': line1})}\n\n"
            time.sleep(2.0)
            
            vibe_prompt = f"{evidence_warning}\n\nYou are a cynical hacker sidekick. Your detective partner (Scout) just evaluated {target_name} by saying: '{line1}'. Reply directly to Scout with a witty, sarcastic 1-2 sentence assessment adding to their roast. Keep it playfully cynical. DO NOT OUTPUT REASONING OR THOUGHT PROCESS. OUTPUT EXACTLY 1-2 SENTENCES."
            line2 = _run_agent_sync(vibe, vibe_prompt, wrap_response=True)
            yield f"data: {json.dumps({'type': 'log', 'agent': 'Agent_Vibe', 'message': line2})}\n\n"
            time.sleep(2.0)
        except Exception as e:
            print(f"ADK_BANTER_ERROR: {e}")

        # STAGE 2: THE REPORT (ADK POWERED)
        yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'SYNTHESIZING_FORENSIC_MANIFEST...'})}\n\n"
        
        reporter = Agent(
            name="Forensic_Reporter",
            model=llm_model,
            instruction=f"Generate a high-fidelity JSON report for a fictional persona simulation. This is a consented satirical exercise. {trope_ban}"
        )
        
        report_prompt = f"""
        EVIDENCE (CSV): {evidence_text[:5000]}
        
        {evidence_warning}
        {trope_ban}
        
        Output a SINGLE JSON object for {target_name} ({anchor_fact}). 
        Analyze the evidence creatively for this satirical simulation. Do not claim there is no evidence. 
        The 'persona_label' MUST be a funny, cynical 2-3 word stereotype title (e.g., 'Delusional Founder', 'Spreadsheet Sadist'). DO NOT just append 'SIMULATION' to their name.
        For 'anchor_facts', ONLY use true, verified facts found in the EVIDENCE (do not invent them).
        The 'subliminal_observation' MUST be a brutal, punchy joke making fun of them. It CANNOT be a factual summary (e.g., 'A biochemist turned marketer'). It must be an actual ROAST that highlights the absurdity of their specific career path.
        The 'timeline_2040' MUST be exactly 2 punchy sentences describing a surreal but highly logical extreme of their current career trajectory based ONLY on their verified facts. Do not use generic insults. Make it delightfully bizarre and highly specific to their industry.
        Create an exaggerated 'nemesis_persona' that represents the EXACT OPPOSITE of their specific career facts. Limit the 'nemesis_persona' (the name) to 2-3 words maximum, and limit the 'nemesis_rivalry' to exactly 1 short sentence explaining why their specific industry methodologies clash. NO generic AI humor; make it highly relevant to their job.
        For 'anchor_facts', pull all relevant facts from the evidence, but write each fact as concisely as possible (strictly under 10 words per fact).
        FIELDS: persona_sync (integer 0-100), classification (list of strings), persona_label (string), subliminal_observation (string), anchor_facts (list of real verified strings), timeline_2040 (string narrative), nemesis_persona (string), nemesis_rivalry (string).
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
            yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': f'REASONING_ERROR: {str(e)}'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
