import json
from collections import Counter

# Load the scientific analysis results
with open('data/scientific_analysis_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Research Areas Analysis Based on Real NASA OSDR Data:")
print("=" * 50)

# 1. Data Type Distribution
print("\n1. Data Types Found in Studies:")
for data_type, count in data['data_type_distribution'].items():
    print(f"   - {data_type}: {count} instances")

# 2. File Type Distribution
print("\n2. File Types Processed:")
for file_type, count in data['file_type_distribution'].items():
    print(f"   - {file_type}: {count} files")

# 3. Data Categories
print("\n3. Data Categories Identified:")
for category, count in data['data_category_distribution'].items():
    print(f"   - {category}: {count} files")

# 4. Key Scientific Insights
print("\n4. Key Scientific Insights:")
for i, insight in enumerate(data['key_scientific_insights'][:10], 1):
    print(f"   {i}. {insight}")

# 5. Study Level Analysis
print("\n5. Individual Study Analysis:")
for study in data['study_level_analyses']:
    print(f"\n   Study ID: {study['study_id']}")
    print(f"   - Files Processed: {study['successfully_processed']}/{study['total_files_sampled']}")
    print(f"   - Data Volume: {study['total_data_size_bytes'] / (1024*1024):.2f} MB")
    
    # Research focus from sample file analyses
    if 'sample_file_analyses' in study and study['sample_file_analyses']:
        focus_areas = []
        organisms = []
        for analysis in study['sample_file_analyses']:
            if 'research_focus' in analysis:
                focus_areas.append(analysis['research_focus'])
            # Extract organisms from insights
            for insight in study.get('scientific_insights', []):
                if 'organisms:' in insight:
                    organisms.append(insight.split('organisms: ')[1])
        
        if focus_areas:
            print(f"   - Research Focus Areas: {', '.join(set(focus_areas))}")
        if organisms:
            print(f"   - Organisms Studied: {', '.join(set(organisms))}")

print("\n" + "=" * 50)
print("Explanation of Categories:")
print("- 'osdr': All studies are from NASA's Open Science Data Repository (OSDR)")
print("- 'space biology': Research focused on biological effects of spaceflight")
print("- 'radiation': Studies examining effects of cosmic radiation on organisms")
print("- 'test' and 'debug': These may be from preliminary or sample datasets used for testing the analysis pipeline")