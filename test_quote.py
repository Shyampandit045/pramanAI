import requests
import json

url = "http://127.0.0.1:8000/api/verify"
payload = {
    "judgment_id": "sc-1950-594",
    "submitted_quote": (
        "freedom of speech and of the press lay at the foundation of all democratic organisations, "
        "for without free political discussion no public education, so essential for the proper functioning "
        "of the processes of popular government, is possible."
    )
}

try:
    print(f"Connecting to {url}...")
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print("\n================ VERIFICATION RESULT ================")
        print(f"Status:            {data.get('status')}")
        print(f"Similarity Score:  {data.get('similarity_score')}%")
        print(f"Case Title:        {data.get('case_details', {}).get('title')}")
        print(f"Citation:          {data.get('case_details', {}).get('citation')}")
        print(f"Page Number:       Page {data.get('page_number')}")
        print(f"Quote DNA:         {data.get('quote_dna', {}).get('submitted', {}).get('fingerprint')}")
        print(f"Explanation:       {data.get('explanation')}")
        print("=====================================================\n")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Failed to connect: {e}")
    print("Please make sure backend server is running with: python run.py")

