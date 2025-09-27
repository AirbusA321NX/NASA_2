#!/usr/bin/env python3
"""
Test script to demonstrate the progress bar functionality
"""

import json
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transformer_analyzer import TransformerAnalyzer

def test_progress_bar():
    """Test the progress bar functionality"""
    print("Testing AI Engine progress bar functionality...")
    print("=" * 60)
    
    # Create a sample NASA data structure
    sample_data = {
        "totalPublications": 100,
        "researchAreaDistribution": {
            "Plant Biology": 30,
            "Human Research": 25,
            "Cell Biology": 20,
            "Microbiology": 15,
            "Radiation Biology": 10
        },
        "topOrganisms": [
            "Arabidopsis thaliana",
            "Homo sapiens",
            "Mus musculus",
            "Escherichia coli",
            "Drosophila melanogaster"
        ],
        "yearRange": "2010-2023",
        "publicationsByYear": {
            "2010": 5,
            "2011": 8,
            "2012": 12,
            "2013": 15,
            "2014": 18,
            "2015": 20,
            "2016": 22,
            "2017": 25,
            "2018": 30,
            "2019": 35,
            "2020": 40,
            "2021": 45,
            "2022": 50,
            "2023": 55
        }
    }
    
    # Initialize the transformer analyzer
    analyzer = TransformerAnalyzer()
    
    print("AI Engine: Starting test analysis...")
    print("AI Engine: You should see a progress bar below:")
    print("-" * 60)
    print("AI Engine Progress Visualization:")
    print("-" * 60)
    
    # Run the analysis which should show the progress bar
    results = analyzer.analyze_data(sample_data)
    
    print("-" * 60)
    print("AI Engine: Analysis completed!")
    print(f"AI Engine: Generated {len(results)} result categories")
    
    # Show some sample results
    if "overview" in results:
        print("\nSample Overview Results:")
        for item in results["overview"][:2]:
            print(f"  - {item}")
    
    print("\nTest completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_progress_bar()