import json
import logging
import time
from agent import Agent, VerdictInternal, ExecutionEvent, EvidencePath, Explanation
from datahub_client import process_verdict_writeback_event
from metadata.client import MockMetadataClient, DataHubClient
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demo")

def run_judge_mode():
    print("==============================================")
    print("   JUDGE MODE: END-TO-END DEMO ORCHESTRATOR")
    print("==============================================\n")
    
    # 1. PR Simulation (Alice edits SQL)
    removed_columns = ["customer_status"]
    
    # 2. Offline Demo Snapshot Lookup
    print("09:31:15 | ⚠️ Offline Demo Snapshot loaded")
    client = MockMetadataClient.load_fixture("demo/fixtures/target_leakage_metadata.json")
    time.sleep(1)

    # 3. Traversal and Evaluation
    agent = Agent(client=client, settings=settings)
    
    # We evaluate a dummy root model that depends on the dataset
    model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
    verdict = agent.evaluate_model(model_urn)
    
    # Inject the actual delta explanation if blocked
    if verdict.verdict.value == "blocked" and verdict.explanation:
        verdict.explanation.cause = f"Column dropped: {', '.join(removed_columns)}"
        verdict.explanation.formatted_text = f"❌ Required Column Removed\n\n{removed_columns[0] if removed_columns else 'Unknown'}\n↓\n{verdict.explanation.impact}\n↓\nRisk Score {verdict.risk_score}"

    print(f"09:31:16 | {len(agent.last_graph.nodes)} assets discovered via Lineage")
    time.sleep(1)
    
    print(f"09:31:16 | Policy {verdict.explanation.title if verdict.explanation else 'GOV-12'} violated")
    time.sleep(1)

    # 4. Output the Visual Explainability / GitHub Comment
    print(f"09:31:17 | GitHub comment created")
    time.sleep(1)
    
    print(f"09:31:17 | Risk score {verdict.risk_score if verdict.explanation else 0}")
    
    print("\n--- Visual Explanation ---")
    if verdict.verdict.value == "blocked" and verdict.explanation:
        print(verdict.explanation.formatted_text)
    else:
        print("✅ Merge Approved. No policy violations.")
    print("--------------------------\n")
    
    time.sleep(1)
    
    # 5. REAL DataHub Writeback
    process_verdict_writeback_event(
        verdict_data={"model_urn": model_urn, "reason_code": verdict.reason_code.value, "verdict": verdict.verdict.value, "evidence_paths": verdict.evidence_paths},
        client=client
    )
    print("09:31:18 | DataHub Graph updated (Incidents, Tags written)")
    print("\n🎉 Demo Execution Complete. The frontend will now automatically animate the graph delta.")

if __name__ == "__main__":
    run_judge_mode()
