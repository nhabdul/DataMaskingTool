import pandas as pd
import json
import hashlib
import os
import re
import streamlit as st
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import io


class DataMasker:
    """
    A tool to mask identifiers in datasets and restore them when needed.
    Supports Excel (XLS, XLSX) and CSV files with automatic sensitive data detection.
    """
    
    # Patterns for detecting sensitive data types
    SENSITIVE_KEYWORDS = {
        'name': ['name', 'fullname', 'full_name', 'first_name', 'last_name', 
                 'firstname', 'lastname', 'username', 'user_name'],
        'email': ['email', 'e-mail', 'mail', 'email_address'],
        'phone': ['phone', 'mobile', 'telephone', 'cell', 'contact_number'],
        'id': ['ssn', 'social_security', 'passport', 'license', 'national_id', 
               'nric', 'ic', 'id_number', 'employee_id', 'customer_id', 'user_id'],
        'address': ['address', 'street', 'location', 'residence', 'postal'],
        'financial': ['account', 'credit_card', 'card_number', 'bank', 'iban']
    }
    
    # Regex patterns for data content detection
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
    SSN_PATTERN = r'^\d{3}-\d{2}-\d{4}$'
    CREDIT_CARD_PATTERN = r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$'
    
    def __init__(self, mapping_file: str = "masking_map.json"):
        """
        Initialize the DataMasker.
        
        Args:
            mapping_file: Path to store the masking mapping
        """
        self.mapping_file = mapping_file
        self.mapping: Dict[str, Dict[str, str]] = {}
        self.reverse_mapping: Dict[str, Dict[str, str]] = {}
        self._load_mapping()
    
    def _load_mapping(self):
        """Load existing mapping from file if it exists."""
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r') as f:
                self.mapping = json.load(f)
                # Create reverse mapping
                self.reverse_mapping = {
                    col: {v: k for k, v in mappings.items()}
                    for col, mappings in self.mapping.items()
                }
    
    def _save_mapping(self):
        """Save mapping to file."""
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mapping, f, indent=2)
    
    def _generate_masked_value(self, original: str, prefix: str = "MASKED") -> str:
        """
        Generate a masked value using hash-based approach.
        
        Args:
            original: Original value to mask
            prefix: Prefix for masked value
            
        Returns:
            Masked value
        """
        hash_obj = hashlib.md5(str(original).encode())
        return f"{prefix}_{hash_obj.hexdigest()[:8].upper()}"
    
    def _check_column_name(self, column_name: str) -> Tuple[bool, str]:
        """
        Check if column name suggests sensitive data.
        
        Args:
            column_name: Name of the column
            
        Returns:
            Tuple of (is_sensitive, category)
        """
        col_lower = column_name.lower().replace(' ', '_')
        
        for category, keywords in self.SENSITIVE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in col_lower:
                    return True, category
        
        return False, ''
    
    def _check_data_patterns(self, series: pd.Series, sample_size: int = 100) -> Tuple[bool, str]:
        """
        Check if column data matches sensitive data patterns.
        
        Args:
            series: Pandas Series to analyze
            sample_size: Number of samples to check
            
        Returns:
            Tuple of (is_sensitive, pattern_type)
        """
        # Get non-null sample
        sample = series.dropna().astype(str).head(sample_size)
        
        if len(sample) == 0:
            return False, ''
        
        # Check email pattern
        email_matches = sum(1 for val in sample if re.match(self.EMAIL_PATTERN, val))
        if email_matches / len(sample) > 0.7:
            return True, 'email_pattern'
        
        # Check phone pattern
        phone_matches = sum(1 for val in sample if re.match(self.PHONE_PATTERN, val))
        if phone_matches / len(sample) > 0.7:
            return True, 'phone_pattern'
        
        # Check SSN pattern
        ssn_matches = sum(1 for val in sample if re.match(self.SSN_PATTERN, val))
        if ssn_matches / len(sample) > 0.7:
            return True, 'ssn_pattern'
        
        # Check credit card pattern
        cc_matches = sum(1 for val in sample if re.match(self.CREDIT_CARD_PATTERN, val.replace(' ', '')))
        if cc_matches / len(sample) > 0.7:
            return True, 'credit_card_pattern'
        
        return False, ''
    
    def _check_high_cardinality(self, series: pd.Series, threshold: float = 0.8) -> bool:
        """
        Check if column has high cardinality (likely an identifier).
        
        Args:
            series: Pandas Series to analyze
            threshold: Uniqueness ratio threshold
            
        Returns:
            True if high cardinality
        """
        if len(series) == 0:
            return False
        
        uniqueness_ratio = series.nunique() / len(series)
        return uniqueness_ratio > threshold
    
    def auto_detect_sensitive_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Automatically detect columns that likely contain sensitive data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with detected columns categorized by detection method
        """
        detected = {
            'by_name': [],
            'by_pattern': [],
            'by_cardinality': [],
            'all_detected': [],
            'reasons': {}
        }
        
        for col in df.columns:
            reasons = []
            
            # Check column name
            is_sensitive_name, category = self._check_column_name(col)
            if is_sensitive_name:
                detected['by_name'].append(col)
                reasons.append(f"name keyword ({category})")
            
            # Check data patterns (only for object/string columns)
            if df[col].dtype == 'object':
                is_sensitive_pattern, pattern = self._check_data_patterns(df[col])
                if is_sensitive_pattern:
                    detected['by_pattern'].append(col)
                    reasons.append(f"data pattern ({pattern})")
                
                # Check cardinality
                if self._check_high_cardinality(df[col]):
                    detected['by_cardinality'].append(col)
                    reasons.append(f"high uniqueness ({df[col].nunique()}/{len(df)} unique)")
            
            # Add to all_detected if any reason found
            if reasons and col not in detected['all_detected']:
                detected['all_detected'].append(col)
                detected['reasons'][col] = reasons
        
        return detected
    
    def read_file(self, file) -> pd.DataFrame:
        """
        Read uploaded file (Excel or CSV).
        
        Args:
            file: Uploaded file object
            
        Returns:
            DataFrame containing the data
        """
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(file)
        else:
            raise ValueError(f"Unsupported file format. Please upload CSV, XLS, or XLSX files.")
    
    def mask_dataframe(self, 
                       df: pd.DataFrame,
                       columns_to_mask: List[str],
                       prefix: str = "MASKED") -> pd.DataFrame:
        """
        Mask specified columns in the dataframe.
        
        Args:
            df: DataFrame to mask
            columns_to_mask: List of column names to mask
            prefix: Prefix for masked values
            
        Returns:
            Masked DataFrame
        """
        df_masked = df.copy()
        
        # Mask each specified column
        for col in columns_to_mask:
            if col not in self.mapping:
                self.mapping[col] = {}
                self.reverse_mapping[col] = {}
            
            # Process each unique value
            unique_values = df_masked[col].dropna().unique()
            
            for original_value in unique_values:
                original_str = str(original_value)
                if original_str not in self.mapping[col]:
                    masked_value = self._generate_masked_value(original_str, prefix)
                    self.mapping[col][original_str] = masked_value
                    self.reverse_mapping[col][masked_value] = original_str
            
            # Apply masking
            df_masked[col] = df_masked[col].apply(
                lambda x: self.mapping[col].get(str(x), x) if pd.notna(x) else x
            )
        
        # Save mapping
        self._save_mapping()
        
        return df_masked
    
    def unmask_dataframe(self, 
                        df: pd.DataFrame,
                        columns_to_unmask: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Unmask (restore) specified columns in the dataframe.
        
        Args:
            df: Masked DataFrame
            columns_to_unmask: List of column names to unmask (None = all mapped columns)
            
        Returns:
            Unmasked DataFrame
        """
        df_unmasked = df.copy()
        
        # Determine columns to unmask
        if columns_to_unmask is None:
            columns_to_unmask = list(self.reverse_mapping.keys())
        
        # Unmask each specified column
        for col in columns_to_unmask:
            if col in self.reverse_mapping and col in df_unmasked.columns:
                df_unmasked[col] = df_unmasked[col].apply(
                    lambda x: self.reverse_mapping[col].get(str(x), x) if pd.notna(x) else x
                )
        
        return df_unmasked


# Streamlit Web Interface
def main():
    st.set_page_config(page_title="Data Masking Tool", page_icon="🔒", layout="wide")
    
    st.title("🔒 Data Masking & Unmasking Tool")
    st.markdown("Upload your Excel or CSV file to mask sensitive identifiers and download the protected data.")
    
    # Initialize masker in session state
    if 'masker' not in st.session_state:
        st.session_state.masker = DataMasker()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Mask Data", "🔓 Unmask Data", "🔑 View Mapping"])
    
    # TAB 1: MASK DATA
    with tab1:
        st.header("Mask Sensitive Data")
        
        uploaded_file = st.file_uploader("Upload your file (CSV, XLS, XLSX)", 
                                        type=['csv', 'xls', 'xlsx'],
                                        key="mask_upload")
        
        if uploaded_file:
            try:
                # Read file
                df = st.session_state.masker.read_file(uploaded_file)
                
                st.success(f"✅ File loaded: {uploaded_file.name} ({len(df)} rows, {len(df.columns)} columns)")
                
                # Show preview
                with st.expander("📊 Preview Original Data"):
                    st.dataframe(df.head(10))
                
                # Auto-detect sensitive columns
                st.subheader("🔍 Automatic Detection")
                
                if st.button("🔍 Detect Sensitive Columns", key="detect_btn"):
                    with st.spinner("Analyzing dataset..."):
                        detected = st.session_state.masker.auto_detect_sensitive_columns(df)
                        st.session_state.detected = detected
                
                if 'detected' in st.session_state:
                    detected = st.session_state.detected
                    
                    if detected['all_detected']:
                        st.success(f"✅ Found {len(detected['all_detected'])} potentially sensitive columns")
                        
                        # Show detected columns with reasons
                        for col in detected['all_detected']:
                            reasons = detected['reasons'][col]
                            st.info(f"**{col}**: {', '.join(reasons)}")
                    else:
                        st.warning("⚠️ No sensitive columns detected automatically")
                
                # Column selection
                st.subheader("📋 Select Columns to Mask")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Pre-select detected columns
                    default_selection = st.session_state.detected['all_detected'] if 'detected' in st.session_state else []
                    selected_columns = st.multiselect(
                        "Choose columns to mask:",
                        options=df.columns.tolist(),
                        default=default_selection
                    )
                
                with col2:
                    mask_prefix = st.text_input("Masked value prefix:", value="MASKED")
                    output_format = st.selectbox("Output format:", ["CSV", "Excel (XLSX)"])
                
                # Mask button
                if st.button("🔒 Mask Selected Columns", type="primary", disabled=len(selected_columns)==0):
                    if selected_columns:
                        with st.spinner("Masking data..."):
                            df_masked = st.session_state.masker.mask_dataframe(
                                df, 
                                selected_columns, 
                                prefix=mask_prefix
                            )
                            st.session_state.masked_df = df_masked
                            st.session_state.masked_columns = selected_columns
                        
                        st.success("✅ Data masked successfully!")
                        
                        # Show masked preview
                        with st.expander("📊 Preview Masked Data"):
                            st.dataframe(df_masked.head(10))
                        
                        # Download button
                        if output_format == "CSV":
                            csv = df_masked.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Masked CSV",
                                data=csv,
                                file_name="masked_data.csv",
                                mime="text/csv"
                            )
                        else:
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df_masked.to_excel(writer, index=False)
                            st.download_button(
                                label="📥 Download Masked Excel",
                                data=buffer.getvalue(),
                                file_name="masked_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        # Download mapping
                        with open(st.session_state.masker.mapping_file, 'r') as f:
                            mapping_json = f.read()
                        st.download_button(
                            label="🔑 Download Mapping File (Keep Safe!)",
                            data=mapping_json,
                            file_name="masking_map.json",
                            mime="application/json"
                        )
                        
                        st.warning("⚠️ **Important:** Download and securely store the mapping file to unmask data later!")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # TAB 2: UNMASK DATA
    with tab2:
        st.header("Unmask Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            masked_file = st.file_uploader("Upload masked file", 
                                          type=['csv', 'xls', 'xlsx'],
                                          key="unmask_upload")
        
        with col2:
            mapping_file = st.file_uploader("Upload mapping file (JSON)", 
                                           type=['json'],
                                           key="mapping_upload")
        
        if masked_file and mapping_file:
            try:
                # Load mapping
                mapping_data = json.load(mapping_file)
                st.session_state.masker.mapping = mapping_data
                st.session_state.masker.reverse_mapping = {
                    col: {v: k for k, v in mappings.items()}
                    for col, mappings in mapping_data.items()
                }
                
                # Read masked file
                df_masked = st.session_state.masker.read_file(masked_file)
                
                st.success(f"✅ Files loaded successfully")
                
                with st.expander("📊 Preview Masked Data"):
                    st.dataframe(df_masked.head(10))
                
                # Select columns to unmask
                available_columns = [col for col in df_masked.columns if col in st.session_state.masker.reverse_mapping]
                
                if available_columns:
                    selected_unmask = st.multiselect(
                        "Select columns to unmask:",
                        options=available_columns,
                        default=available_columns
                    )
                    
                    output_format_unmask = st.selectbox("Output format:", ["CSV", "Excel (XLSX)"], key="unmask_format")
                    
                    if st.button("🔓 Unmask Data", type="primary"):
                        with st.spinner("Unmasking data..."):
                            df_unmasked = st.session_state.masker.unmask_dataframe(
                                df_masked,
                                selected_unmask
                            )
                        
                        st.success("✅ Data unmasked successfully!")
                        
                        with st.expander("📊 Preview Unmasked Data"):
                            st.dataframe(df_unmasked.head(10))
                        
                        # Download button
                        if output_format_unmask == "CSV":
                            csv = df_unmasked.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Unmasked CSV",
                                data=csv,
                                file_name="unmasked_data.csv",
                                mime="text/csv"
                            )
                        else:
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df_unmasked.to_excel(writer, index=False)
                            st.download_button(
                                label="📥 Download Unmasked Excel",
                                data=buffer.getvalue(),
                                file_name="unmasked_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.warning("⚠️ No columns available to unmask with the provided mapping.")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # TAB 3: VIEW MAPPING
    with tab3:
        st.header("View Current Mapping")
        
        if st.session_state.masker.mapping:
            for col, mappings in st.session_state.masker.mapping.items():
                with st.expander(f"📋 {col} ({len(mappings)} values)"):
                    mapping_df = pd.DataFrame([
                        {"Original": k, "Masked": v} 
                        for k, v in list(mappings.items())[:100]  # Limit to 100 for display
                    ])
                    st.dataframe(mapping_df)
                    if len(mappings) > 100:
                        st.info(f"Showing first 100 of {len(mappings)} mappings")
        else:
            st.info("No mapping available. Mask some data first!")


if __name__ == "__main__":
    main()