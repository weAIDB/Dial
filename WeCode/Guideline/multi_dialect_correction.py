import argparse
import json
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add parent directory to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from magic.llm_service import LLMService, VLLMService
from magic.agents import ManagerAgent
from magic.guideline_manager import GuidelineManager

def parse_arguments():
    parser = argparse.ArgumentParser(description="Multi-Dialect SQL Correction & Learning Framework")
    
    parser.add_argument("--input_file", type=str, required=True, help="Path to generation_results jsonl file")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save trajectories and guidelines")
    
    parser.add_argument("--mode", type=str, choices=["api", "local"], default="api", help="Inference mode")
    parser.add_argument("--model_name", type=str, default="deepseek-v3", help="Model name for API or path for local")
    parser.add_argument("--api_key", type=str, required=True, help="API Key for remote models")
    parser.add_argument("--base_url", type=str, default=None, help="Base URL for API models")
    parser.add_argument("--gpu_devices", type=str, default="0", help="CUDA devices for vLLM")

    parser.add_argument("--enable_success_analysis", action="store_true", help="Enable analysis of correct generations")
    parser.add_argument("--guidelines_path", type=str, help="Path to load/save guidelines.json (enables online learning)")
    parser.add_argument("--max_threads", type=int, default=5, help="Parallel processing threads")
    parser.add_argument("--max_retries", type=int, default=3, help="Max correction attempts")

    return parser.parse_args()

def get_llm_service(args):
    if args.mode == "local":
        return VLLMService(model_path=args.model_name, gpu_devices=args.gpu_devices)
    else:
        return LLMService(api_key=args.api_key, base_url=args.base_url, model_name=args.model_name)

def main():
    args = parse_arguments()
    
    # print(f"Initializing LLM Service in {args.mode} mode...")
    llm = get_llm_service(args) 

    # Initialize Guideline Manager (Singleton for Online Learning)
    guideline_manager = None
    if args.guidelines_path:
        print(f"Enabling Online Rolling Guidelines (Path: {args.guidelines_path})")
        guideline_manager = GuidelineManager(llm, args.guidelines_path)

    # Initialize Manager Agent
    # Note: ManagerAgent is stateless regarding guidelines, it queries the GuidelineManager
    manager = ManagerAgent(
        llm_service=llm,
        guideline_manager=guideline_manager,
        enable_success_analysis=args.enable_success_analysis,
        max_retries=args.max_retries
    )

    data = []
    with open(args.input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    print(f"Loaded {len(data)} entries. Output Dir: {args.output_dir}")
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    
    # Define runner function
    def run_one(item):
        try:
            # Redirect stdout to capture print statements from agents if needed, 
            # but keeping them visible might be better for debugging. 
            # Since we use tqdm, raw prints might mess up the bar, 
            # but it's acceptable for critical "Fixed!" messages.
            return manager.run(item)
        except Exception as e:
            # print(f"Error processing {item.get('db_id')}: {e}")
            # traceback.print_exc()
            return {
                "question": item.get("question"),
                "db_id": item.get("db_id"),
                "error": str(e),
                "steps": []
            }

    # Run in parallel with tqdm
    print(f"Starting correction with {args.max_threads} threads...")
    
    with ThreadPoolExecutor(max_workers=args.max_threads) as executor:
        future_to_item = {executor.submit(run_one, item): item for item in data}
        
        # Using tqdm for progress bar
        with tqdm(total=len(data), desc="MAGIC Correction", unit="sample") as pbar:
            for future in as_completed(future_to_item):
                res = future.result()
                results.append(res)
                
                # Extract short info for display
                db_id = res.get("db_id", "N/A")
                
                # Count how many dialects ended up correct (True)
                final_status = res.get("final_status", {})
                correct_count = sum(1 for v in final_status.values() if v is True)
                
                # Update tqdm description/postfix
                pbar.set_postfix(last_db=db_id, correct_dialects=correct_count)
                pbar.update(1)

    # Save Trajectories
    traj_path = os.path.join(args.output_dir, "correction_trajectory.json")
    with open(traj_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nCorrection trajectory saved to {traj_path}")
    
    # --- Calculate and Print Statistics ---
    print("\n" + "="*65)
    print("MAGIC Correction Statistics")
    print("="*65)
    
    stats = {}
    dialects = ["sqlite", "mysql", "postgres"]
    
    for d in dialects:
        stats[d] = {
            "total": 0, 
            "init_exec": 0, "init_res": 0,
            "final_exec": 0, "final_res": 0
        }
        
    for res in results:
        # Skip failed entries
        if "error" in res: continue
        
        initial_status = res.get("initial_status", {})
        final_status = res.get("final_status", {})
        
        for d in dialects:
            # Check if this dialect was evaluated for this sample
            if d in initial_status: 
                stats[d]["total"] += 1
                
                # Initial Stats
                init_s = initial_status[d]
                if init_s.get("exec", False): stats[d]["init_exec"] += 1
                if init_s.get("correct", False): stats[d]["init_res"] += 1
                
                # Final Stats
                final_s = final_status.get(d, {})
                if final_s.get("exec", False): stats[d]["final_exec"] += 1
                if final_s.get("correct", False): stats[d]["final_res"] += 1

    # Header
    print(f"{'Dialect':<10} | {'Init EX':<15} | {'Final EX':<15} | {'Gain EX':<8} || {'Init RES':<15} | {'Final RES':<15} | {'Gain RES':<8}")
    print("-" * 110)
    
    for d in dialects:
        data = stats[d]
        total = data["total"]
        if total == 0:
            print(f"{d.capitalize():<10} | {'N/A':<15} | {'N/A':<15} | {'N/A':<8} || {'N/A':<15} | {'N/A':<15} | {'N/A':<8}")
            continue
            
        # Calculate percentages
        i_ex = (data["init_exec"] / total) * 100
        f_ex = (data["final_exec"] / total) * 100
        g_ex = f_ex - i_ex
        
        i_res = (data["init_res"] / total) * 100
        f_res = (data["final_res"] / total) * 100
        g_res = f_res - i_res
        
        print(f"{d.capitalize():<10} | {i_ex:6.2f}% ({data['init_exec']}/{total}) | {f_ex:6.2f}% ({data['final_exec']}/{total}) | +{g_ex:5.2f}% || {i_res:6.2f}% ({data['init_res']}/{total}) | {f_res:6.2f}% ({data['final_res']}/{total}) | +{g_res:5.2f}%")
        
    print("="*110 + "\n")
    
    if guideline_manager:
        print(f"Final Guidelines saved to {args.guidelines_path}")

if __name__ == "__main__":
    main()
