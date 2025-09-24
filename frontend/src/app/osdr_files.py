import requests
import time

BASE_URL = "https://osdr.nasa.gov/osdr/data/osd"

def get_all_studies():
    """Fetch list of all studies"""
    studies = []
    page = 1
    size = 50  # adjust if needed
    while True:
        url = f"{BASE_URL}/studies?page={page}&size={size}"
        r = requests.get(url)
        if r.status_code != 200:
            print("Error fetching studies:", r.status_code)
            break
        data = r.json()
        studies.extend(data['results'])
        if page >= data['total_pages']:
            break
        page += 1
        time.sleep(0.1)  # be polite to server
    return studies

def get_files_for_study(study_id):
    """Fetch files for a single study"""
    url = f"{BASE_URL}/files/{study_id}?page=1&size=100&all_files=true"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Error fetching files for {study_id}: {r.status_code}")
        return []
    return r.json().get('results', [])

def main():
    all_studies = get_all_studies()
    print(f"Found {len(all_studies)} studies.")
    
    all_files = []
    for study in all_studies:
        study_id = study['study_id']
        files = get_files_for_study(study_id)
        for f in files:
            all_files.append({
                "study_id": study_id,
                "file_name": f.get('file_name'),
                "file_url": f.get('file_url')
            })
        print(f"Fetched {len(files)} files for {study_id}")
        time.sleep(0.1)  # avoid hammering server

    # Save to CSV
    import csv
    with open("osdr_all_files.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["study_id","file_name","file_url"])
        writer.writeheader()
        writer.writerows(all_files)

    print(f"Total files collected: {len(all_files)}")
    print("Saved to osdr_all_files.csv")

if __name__ == "__main__":
    main()
