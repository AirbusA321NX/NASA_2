from scientific_data_analyzer import ScientificDataAnalyzer

def test_extract_study_info():
    try:
        analyzer = ScientificDataAnalyzer()
        
        # Test case 1: Microarray data
        filename1 = 'https://nasa-osdr.s3.amazonaws.com/OSD-1/version-6/array/GLDS-1_array_Dmel_OR_wo_FLT_infdw-Bbas_Rep1_GSM1287106_raw.CEL.gz'
        result1 = analyzer._extract_study_info_from_filename(filename1)
        print("Test 1 - Microarray data:")
        print(result1)
        print()
        
        # Test case 2: RNA-seq data
        filename2 = 'https://nasa-osdr.s3.amazonaws.com/OSD-100/version-5/rna_seq/GLDS-100_rna_seq_Mmus_C57-6J_EYE_FLT_Rep1_M23_R1_raw.fastq.gz'
        result2 = analyzer._extract_study_info_from_filename(filename2)
        print("Test 2 - RNA-seq data:")
        print(result2)
        print()
        
        # Test case 3: Generic data
        filename3 = 'https://nasa-osdr.s3.amazonaws.com/OSD-50/version-3/proteomics/sample_proteomics_data.csv'
        result3 = analyzer._extract_study_info_from_filename(filename3)
        print("Test 3 - Proteomics data:")
        print(result3)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extract_study_info()