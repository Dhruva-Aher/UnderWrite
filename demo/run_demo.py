import json
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent import Agent
from datahub_client import process_verdict_writeback_event
from metadata.client import MockMetadataClient
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demo")

def run_judge_mode():
    print("==============================================")
    print("   JUDGE MODE: END-TO-END DEMO ORCHESTRATOR")
    print("==============================================\n")
    
    # 1. Offline Demo Snapshot Lookup
    print("Loading offline demo snapshot...")
    try:
        client = MockMetadataClient.load_fixture("demo/fixtures/target_leakage_metadata.json")
        print("✅ Offline Demo Snapshot loaded")
    except Exception as e:
        print(f"❌ Failed to load fixture: {e}")
        return

    # 2. Traversal and Evaluation
    agent = Agent(client=client, settings=settings)
    
    model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
    print(f"\nEvaluating deployment for model: {model_urn}")
    verdict = agent.evaluate_model(model_urn)
    
    print(f"\nDiscovered {len(agent.last_graph.nodes)} assets via Lineage.")
    print(f"Policies Evaluated: {verdict.policies_evaluated}")
    print(f"Verdict: {verdict.verdict.value.upper()}")
    print(f"Reason Code: {verdict.reason_code}")
    
    if verdict.verdict.value == "blocked" and verdict.evidence_paths:
        print("\n--- Evidence Paths ---")
        for i, ep in enumerate(verdict.evidence_paths, start=1):
            print(f"{i}. Policy {ep.policy_id} triggered on node {ep.tainted_urn} (tagged '{ep.tag_found}')")
            print(f"   Path: {' -> '.join(ep.path)}")
            if hasattr(ep, "rationale") and ep.rationale:
                print(f"   Rationale: {ep.rationale}")
        print("----------------------")
    else:
        print("\n✅ Merge Approved. No policy violations.")
    
    # 3. REAL DataHub Writeback
    print("\nInitiating background write-back...")
    wb_result = process_verdict_writeback_event(
        verdict_data={
            "model_urn": model_urn, 
            "reason_code": verdict.reason_code, 
            "verdict": verdict.verdict.value, 
            "evidence_paths": verdict.evidence_paths
        },
        client=client
    )
    print(f"Writeback Status: {wb_result.status} - {wb_result.message}")
    print("\n🎉 Demo Execution Complete.")

if __name__ == "__main__":
    run_judge_mode()
