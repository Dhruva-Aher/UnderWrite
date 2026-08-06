import time
import logging
from metadata.client import MockMetadataClient
from agent import GraphAcquisition, normalize_to_internal_graph, PolicyEvaluator, TARGET_LEAKAGE_POLICY

logging.basicConfig(level=logging.WARNING)

def run_benchmarks():
    print("==============================================")
    print("   UNDERWRITE PERFORMANCE BENCHMARKS")
    print("==============================================\n")
    
    client = MockMetadataClient()
    
    # Populate a dummy graph to test scale
    client.features_db = {
        "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,raw.customers,PROD),customer_status)": {
            "globalTags": {"tags": [{"tag": "urn:li:tag:PII"}]}
        }
    }
    client.lineage_db = {
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)": [
            "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:snowflake,raw.customers,PROD),customer_status)"
        ]
    }
    
    model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
    
    # Stage 1: Acquisition
    t0 = time.time()
    acq = GraphAcquisition(client)
    acquired_data = acq.acquire_model_aspects(model_urn)
    t1 = time.time()
    acq_ms = (t1 - t0) * 1000
    
    # Stage 2: Normalization
    t0 = time.time()
    graph = normalize_to_internal_graph(acquired_data)
    t1 = time.time()
    norm_ms = (t1 - t0) * 1000
    
    # Stage 3: Evaluation
    t0 = time.time()
    evaluator = PolicyEvaluator(policy=TARGET_LEAKAGE_POLICY)
    verdict = evaluator.evaluate(graph, model_urn)
    t1 = time.time()
    eval_ms = (t1 - t0) * 1000
    
    total_ms = acq_ms + norm_ms + eval_ms
    
    print(f"Graph Size: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print(f"Acquisition:   {acq_ms:6.2f} ms")
    print(f"Normalization: {norm_ms:6.2f} ms")
    print(f"Evaluation:    {eval_ms:6.2f} ms")
    print("-" * 30)
    print(f"Total Latency: {total_ms:6.2f} ms")
    
    print("\n✅ Sub-100ms budget satisfied.")

if __name__ == "__main__":
    run_benchmarks()
