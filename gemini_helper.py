import google.generativeai as genai
import os
import re
genai.configure(api_key="AIzaSyAJCBUsBaOQxW0uMW5J43Xs8RRfdr_jm5Y")
model = genai.GenerativeModel('learnlm-2.0-flash-experimental')

def analyze_transactions_csv(file_path):
    with open(file_path, "r") as f:
        csv_content = f.read()

    json_sample = """
[
  {
    "heading": "Short-Term Investments",
    "chart_labels": ["FDs"],
    "chart_data": [29912],
    "subsections": [
      {
        "title": "FDs (₹29,912)",
        "content": "Provides stability and liquidity for emergency needs."
      }
    ]
  }
]
"""

    prompt = f"""
Here's my monthly transaction data in CSV format:

{csv_content}

---

Assume I will continue earning and spending in the same pattern.

### Objective:
Generate a personalized investment plan based on this data. I am a moderate-risk investor seeking a balance between safety and returns.

### Instructions:
- Include exact rupee amounts or percentages for FDs, SIPs, Mutual Funds (equity/debt), and Direct Equity.
- Break the plan into:
  - Short-term stability(also suggest current mutual funds in india that are doing good, add 1 year returns in percent along with suggestions)
  - Medium-term goals (3–5 years)
  - Long-term wealth generation
- For each section, give:
  - A heading
  - A pie chart structure: `chart_labels` and `chart_data`
  - A `subsections` list with investment titles and short explanations

### Output format:
Return only a raw JSON array. No explanations, markdown, or backticks. Output should look exactly like:

{json_sample}
"""



    response = model.generate_content(prompt)
    response_text = response.text.strip()

    # Strip triple backticks and language tags if present
    response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
    response_text = re.sub(r"\s*```$", "", response_text)

    return response_text
