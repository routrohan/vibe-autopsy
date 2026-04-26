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
        system_instruction=types.Content(role="system", parts=[types.Part.from_text(text=str(agent_obj.instruction))]),
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])]
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

# Initialize the 120B Core via the ADK OpenAI-compatible wrapper
llm_model = LiteLlm(
    model="groq/openai/gpt-oss-120b",
    api_key=os.environ["GROQ_API_KEY"]
)

def search_internet(query: str, anchor: str) -> list:
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        search_query = f'"{query}" {anchor} LinkedIn "work experience" career profile'
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

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS': return Response(status=204)
    data = request.json
    target_name = data.get('name', 'Unknown')
    anchor_fact = data.get('context', '')
    linkedin_url = data.get('linkedin_url', '')

    def generate():
        yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': 'ADK_PROTOCOL_INITIALIZED...'})}\n\n"
        
        results = search_internet(target_name, f"{anchor_fact} {linkedin_url}")
        evidence_text = "\n".join([f"FACT: {r['title']} | DETAILS: {r['content']}" for r in results])
        
        # STEP 1: DEFINE ADK AGENTS
        scout = Agent(
            name="Scout",
            model=llm_model,
            instruction=f"You are a comedian participating in a consenting roast battle. Use this data: {evidence_text[:3000]} to output a purely satirical, funny observation about {target_name}. This is a fictional persona simulation. Ensure no real harassment."
        )
        
        vibe = Agent(
            name="Vibe",
            model=llm_model,
            instruction=f"You are a comedian sidekick in a consenting roast battle. Respond to Scout's findings about {target_name} with a funny, satirical observation. This is a fictional persona simulation. Ensure no real harassment."
        )

        # STAGE 1: BANTER (ADK POWERED)
        try:
            # We simulate the multi-agent exchange via ADK generations
            scout_prompt = f"EVIDENCE: {evidence_text[:3000]}\n\nYou are a jaded detective hacking into {target_name}'s digital footprint. Based on the evidence above, start a conversation with your hacker sidekick (Vibe) by giving a highly satirical, witty 1-2 sentence roast of {target_name}. You MUST specifically mention a real fact from their experience or profile. Be playfully cynical. DO NOT OUTPUT REASONING OR THOUGHT PROCESS. OUTPUT EXACTLY 1-2 SENTENCES."
            line1 = _run_agent_sync(scout, scout_prompt, wrap_response=True)
            yield f"data: {json.dumps({'type': 'log', 'agent': 'Agent_Scout', 'message': line1})}\n\n"
            time.sleep(2.0)
            
            vibe_prompt = f"EVIDENCE: {evidence_text[:3000]}\n\nYou are a cynical hacker sidekick. Your detective partner (Scout) just evaluated {target_name} by saying: '{line1}'. Reply directly to Scout with a witty, sarcastic 1-2 sentence assessment adding to their roast. Keep it playfully cynical and mention another real fact from the evidence if possible. DO NOT OUTPUT REASONING OR THOUGHT PROCESS. OUTPUT EXACTLY 1-2 SENTENCES."
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
            instruction=f"Generate a high-fidelity JSON report for a fictional persona simulation. This is a consented satirical exercise. EVIDENCE: {evidence_text[:5000]}"
        )
        
        report_prompt = f"""
        EVIDENCE: {evidence_text[:5000]}
        
        Output a SINGLE JSON object for {target_name} ({anchor_fact}). 
        Analyze the evidence creatively for this satirical simulation. Do not claim there is no evidence. 
        For 'anchor_facts', ONLY use true, verified facts found in the EVIDENCE (do not invent them).
        The 'subliminal_observation' MUST be an absolutely hilarious, side-splittingly funny roast based strictly on their ACTUAL WORK EXPERIENCE found in the evidence. It should be the funniest, punchiest, most cleverly written corporate roast imaginable. Crack them up! (Keep it playful, not genuinely offensive).
        The 'timeline_2040' MUST be a short (1-2 sentences max), funny, and highly surreal twist on their career trajectory. Make it delightfully bizarre and abstract!
        Make up an exaggerated 'nemesis_persona' based on the true facts provided.
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
            
            yield f"data: {json.dumps({
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
            })}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'log', 'agent': 'System', 'message': f'REASONING_ERROR: {str(e)}'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
