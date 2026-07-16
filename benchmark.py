import requests
from time import perf_counter
import json
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime



load_dotenv()
anthropic_api_key = os.environ['ANTHROPIC_API_KEY']
claude_url = os.environ["CLAUDE_URL"]

def ollama_sender(prompt : str):
    payload = {"model" : "mistral:7b-instruct-q5_K_S",
               "prompt" : prompt,
               "stream" : False}
    
    start = perf_counter()
    response = requests.post(url = "http://localhost:11434/api/generate", json = payload)
    client_waiting = perf_counter() - start
    response = response.json()
    raw_dict = {"provider" : "Ollama",
                "input_tokens" : response['prompt_eval_count'],
                "output_tokens" : response['eval_count'],
                "client_waiting" : client_waiting,
                "raw_response" : response}
    return raw_dict

def haiku_sender(prompt : str):
    headers = {"x-api-key":anthropic_api_key,
            "anthropic-version":"2023-06-01"}
    
    body = {"model":"claude-haiku-4-5-20251001",
            "max_tokens":2048,
            "messages":[{"role":"user", "content":prompt}]
            }
    start = perf_counter()
    response = requests.post(url=claude_url, headers= headers, json = body)
    client_waiting = perf_counter() - start
    result = response.json()
    raw_dict = {"provider" : "haiku",
                "input_tokens" : result["usage"]['input_tokens'],
                "output_tokens" : result["usage"]['output_tokens'],
                "client_waiting" : client_waiting,
                "raw_response" : result}
    return raw_dict



def sonnet_sender(prompt : str):
    headers = {"x-api-key":anthropic_api_key,
            "anthropic-version":"2023-06-01"}
    
    body = {"model":"claude-sonnet-5",
            "max_tokens":2048,
            "messages":[{"role":"user", "content":prompt}]
            }
    start = perf_counter()
    response = requests.post(url=claude_url, headers= headers, json = body)
    client_waiting = perf_counter() - start
    result = response.json()
    raw_dict = {"provider" : "sonnet",
                "input_tokens" : result['usage']['input_tokens'],
                "output_tokens" : result['usage']['output_tokens'],
                "client_waiting" : client_waiting,
                "raw_response" : result}
    return raw_dict


def run_benchmark(prompts, sender , num_runs = 2):
    # warmup the model (for a bettwr benchmarking)
    sender("Hello")
    final_result = []
    for i in range(len(prompts)):
        prompt_number = i + 1
        print(f"Working on prompt number {prompt_number}")
        for _ in range(num_runs):
            category = prompts[i]["category"]
            print(f"its a {category} prompt")
            result = sender(prompts[i]['prompt'])
            result['prompt_number'] = prompt_number
            result["prompt_category"] = category
            final_result.append(result)
    return final_result



def compute_summaries(result):
    df = pd.DataFrame(result)
    # Generated tokens (How many seconds the client waited to get the reponse)
    df['tok_per_sec'] = df['output_tokens']/ df['client_waiting']

    # group-by (summary by category)
    summary_by_cat = df.groupby(by = ['provider','prompt_category'])[['input_tokens', 'output_tokens', 'client_waiting', 'tok_per_sec']].agg(['mean', 'std'])

    # group-by_prompt
    summary_by_prompt = df. groupby(by = ['provider','prompt_number', 'prompt_category'])[['output_tokens', 'client_waiting', 'tok_per_sec']].agg(['mean', 'std'])

    return df, summary_by_cat, summary_by_prompt



if __name__ == "__main__":
    with open ('prompts.json', 'r') as f:
        data = json.load(f)

    test_prompts = data['prompts']

    print("Current Provider is Mistral")
    ollama_raws = run_benchmark(test_prompts, sender=ollama_sender, num_runs=5)
    print("Current Provider is Haiku")
    haiku_raws = run_benchmark(test_prompts, sender=haiku_sender, num_runs=5)
    print("Current Provider is Sonnet")
    sonnet_raws = run_benchmark(test_prompts, sender=sonnet_sender, num_runs=5)

    all_rows = ollama_raws + haiku_raws + sonnet_raws

    df, by_cat, by_prompt = compute_summaries(all_rows)

    print("\n=== BY CATEGORY ===")
    print(by_cat)
    print("\n=== BY PROMPT ===")
    print(by_prompt)

    safe_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    df.to_csv(f'{safe_timestamp}.csv', index=False)
