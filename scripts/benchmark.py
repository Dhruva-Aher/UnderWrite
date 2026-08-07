import time
import logging
from metadata.client import MockMetadataClient
from agent import Agent, load_policies_from_yaml

logging.basicConfig(level=logging.WARNING)

def run_benchmarks():
    print("==============================================")
    print("   UNDERWRITE PERFORMANCE BENCHMARKS")
    print("==============================================\n")
    
    # Load realistic fixture and policies
    client = MockMetadataClient.load_fixture("demo/fixtures/target_leakage_metadata.json")
    policies = load_policies_from_yaml("policies.yaml")
    
    model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
    
    # Stage 1: Full Pipeline (Acquisition + Normalization + Evaluation)
    t0 = time.perf_counter()
    agent = Agent(client=client, settings=None, policies=policies)
    verdict = agent.evaluate_model(model_urn)
    t1 = time.perf_counter()
    total_ms = (t1 - t0) * 1000
    
    # Stage 2: Pure Policy Evaluation (in-memory, no network/acquisition)
    # We can measure this by repeatedly evaluating the cached graph
    graph = agent.last_graph
    
    from agent import PolicyEvaluator
    
    t0 = time.perf_counter()
    # Evaluate 100 times to get a stable average
    iterations = 100
    for _ in range(iterations):
        for policy in policies:
            _ = PolicyEvaluator(policy=policy).evaluate(graph, model_urn)
    t1 = time.perf_counter()
    pure_eval_ms = ((t1 - t0) * 1000) / iterations
    
    print(f"Graph Size: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print(f"Total Latency (Full Pipeline): {total_ms:6.2f} ms")
    print(f"Pure Policy Evaluation (avg):  {pure_eval_ms:6.2f} ms")

if __name__ == "__main__":
    run_benchmarks()
