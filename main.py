import requests
import json
import pandas as pd
from time import perf_counter
from datetime import datetime

with open ('prompts.json', 'r') as file:
    data = json.load(file)


overlall_output_list = []
# for loop to loop through the prompts in the JSON file

warmup_payload =  {"model" : "mistral:7b-instruct-q5_K_S",
                    "prompt" : "Hello Mistral, How are you?",
                    "stream" : False }

warmup_response = requests.post('http://localhost:11434/api/generate', json = warmup_payload)

for i in range(len(data['prompts'])):
    print(f'prompt number {i+1}')
    for k in range(5):
        my_prompt = data['prompts'][i]['prompt']
        start = perf_counter()
        payload = {"model" : "mistral:7b-instruct-q5_K_S",
            "prompt" : my_prompt,
            "stream" : False }
        response = requests.post('http://localhost:11434/api/generate', json = payload)
        elapsed_time = perf_counter() - start
        result = response.json()
        row_dict = {'prompt' : i + 1,
                    'prompt_cat' : data['prompts'][i]['category'],
                    'total_duration' : result['total_duration'],
                    'load_duration' : result['load_duration'],
                    'prompt_eval_count' : result['prompt_eval_count'],
                    'prompt_eval_duration' : result['prompt_eval_duration'],
                    'eval_count' : result['eval_count'],
                    'eval_duration' : result['eval_duration'],
                    'client_waiting' : elapsed_time
                    }
        overlall_output_list.append(row_dict)

df = pd.DataFrame(overlall_output_list)

df['gen_tok_per_sec'] = df['eval_count'] / (df['eval_duration'] / 1e9)
df['prompt_tok_per_sec'] = df['prompt_eval_count'] / (df['prompt_eval_duration'] / 1e9)

safe_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

df.to_csv(f'{safe_timestamp}.csv', index=False)

df_groupby_per_prompt = df.groupby(['prompt', 'prompt_cat'])[['gen_tok_per_sec', 'prompt_tok_per_sec', 'client_waiting']].agg(['mean', 'std'])

df_groupby_per_category= df.groupby(['prompt_cat'])[['gen_tok_per_sec', 'prompt_tok_per_sec', 'client_waiting']].agg(['mean', 'std'])

print('\n per prompt')
print(df_groupby_per_prompt)

print('\n per category')
print(df_groupby_per_category)
