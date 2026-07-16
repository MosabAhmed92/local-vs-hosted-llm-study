import pandas as pd 

df = pd.read_csv("2026-07-15_17-15-08.csv")

summary_by_cat = df.groupby(by = ['provider','prompt_category'])[['input_tokens', 'output_tokens', 'client_waiting', 'tok_per_sec']].agg(['mean', 'std'])

    # group-by_prompt
summary_by_prompt = df. groupby(by = ['provider','prompt_number', 'prompt_category'])[['output_tokens', 'client_waiting', 'tok_per_sec']].agg(['mean', 'std'])

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print(summary_by_cat)
print(summary_by_prompt)