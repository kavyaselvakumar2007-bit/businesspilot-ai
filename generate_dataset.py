import pandas as pd
import random

industries = [
    "Software", "Healthcare", "Finance",
    "Retail", "Manufacturing", "Education",
    "Logistics", "Energy", "Telecommunications"
]

countries = [
    "India", "USA", "UK",
    "Canada", "Singapore", "Germany"
]

data = []

for i in range(1, 26):
    data.append({
        "lead_id": i,
        "company_name": f"Company_{i}",
        "industry": random.choice(industries),
        "annual_revenue": random.randint(500000, 50000000),
        "employee_count": random.randint(20, 1000),
        "country": random.choice(countries)
    })

df = pd.DataFrame(data)
df.to_csv("test_leads.csv", index=False)

print("test_leads.csv created successfully!")