"""
Data loaders for synthetic medical data generation.

This module provides classes to load and parse data from various sources:
- FHIR NDJSON files from MIMIC IV dataset
- CSV demographic data
- PDF template files
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class FHIRDataLoader:
    """Loads and parses MIMIC IV FHIR NDJSON files."""
    
    def __init__(self, data_dir: str):
        """Initialize with path to FHIR data directory.
        
        Args:
            data_dir: Path to directory containing FHIR NDJSON files
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            logger.error(f"FHIR data directory not found: {data_dir}")
            raise FileNotFoundError(f"FHIR data directory not found: {data_dir}")
    
    def _load_ndjson_file(self, filename: str) -> List[Dict]:
        """Load and parse NDJSON file.
        
        Args:
            filename: Name of the NDJSON file to load
            
        Returns:
            List of parsed JSON objects
        """
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"FHIR file not found: {file_path}")
            return []
        
        records = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON at line {line_num} in {filename}: {e}")
                        continue
            
            logger.info(f"Loaded {len(records)} records from {filename}")
            return records
            
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
    
    def load_patients(self) -> List[Dict]:
        """Load MimicPatient resources.
        
        Returns:
            List of patient records
        """
        return self._load_ndjson_file("MimicPatient.ndjson")
    
    def load_conditions(self) -> List[Dict]:
        """Load MimicCondition and MimicConditionED resources.
        
        Returns:
            List of condition records
        """
        conditions = []
        conditions.extend(self._load_ndjson_file("MimicCondition.ndjson"))
        conditions.extend(self._load_ndjson_file("MimicConditionED.ndjson"))
        return conditions
    
    def load_observations(self) -> List[Dict]:
        """Load MimicObservationLabevents and vital signs.
        
        Returns:
            List of observation records
        """
        observations = []
        observations.extend(self._load_ndjson_file("MimicObservationLabevents.ndjson"))
        observations.extend(self._load_ndjson_file("MimicObservationVitalSigns.ndjson"))
        return observations
    
    def load_medications(self) -> List[Dict]:
        """Load MimicMedicationRequest resources.
        
        Returns:
            List of medication records
        """
        return self._load_ndjson_file("MimicMedicationRequest.ndjson")
    
    def load_encounters(self) -> List[Dict]:
        """Load MimicEncounter resources.
        
        Returns:
            List of encounter records
        """
        return self._load_ndjson_file("MimicEncounter.ndjson")
    
    def load_procedures(self) -> List[Dict]:
        """Load MimicProcedure resources.
        
        Returns:
            List of procedure records
        """
        return self._load_ndjson_file("MimicProcedure.ndjson")


class CSVDataLoader:
    """Loads healthcare demographic data from CSV."""
    
    def __init__(self, csv_path: str):
        """Initialize with path to CSV file.
        
        Args:
            csv_path: Path to CSV file containing demographic data
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self._data: Optional[pd.DataFrame] = None
    
    def load_demographics(self) -> pd.DataFrame:
        """Load and return demographic data.
        
        Returns:
            DataFrame containing demographic data
        """
        if self._data is None:
            try:
                self._data = pd.read_csv(self.csv_path)
                logger.info(f"Loaded {len(self._data)} demographic records from CSV")
            except Exception as e:
                logger.error(f"Error loading CSV file {self.csv_path}: {e}")
                raise
        
        return self._data
    
    def sample_demographics(self, n: int = 1) -> List[Dict]:
        """Sample n random demographic records.
        
        Args:
            n: Number of records to sample
            
        Returns:
            List of sampled demographic records as dictionaries
        """
        df = self.load_demographics()
        if len(df) == 0:
            logger.warning("No demographic data available for sampling")
            return []
        
        # Sample with replacement if n > len(df)
        replace = n > len(df)
        sampled = df.sample(n=min(n, len(df)), replace=replace)
        
        return sampled.to_dict('records')


class PDFTemplateLoader:
    """Loads PDF scan templates."""
    
    def __init__(self, template_dir: str):
        """Initialize with path to template directory.
        
        Args:
            template_dir: Path to directory containing PDF template files
        """
        self.template_dir = Path(template_dir)
        if not self.template_dir.exists():
            logger.error(f"Template directory not found: {template_dir}")
            raise FileNotFoundError(f"Template directory not found: {template_dir}")
    
    def list_templates(self) -> List[str]:
        """List available template files.
        
        Returns:
            List of template filenames
        """
        try:
            # Look for PDF and PNG files as templates
            templates = []
            for ext in ['*.pdf', '*.png', '*.jpg', '*.jpeg']:
                templates.extend([f.name for f in self.template_dir.glob(ext)])
            
            logger.info(f"Found {len(templates)} template files")
            return sorted(templates)
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def load_template(self, template_name: str) -> bytes:
        """Load specific template file.
        
        Args:
            template_name: Name of the template file to load
            
        Returns:
            Template file content as bytes
        """
        template_path = self.template_dir / template_name
        if not template_path.exists():
            logger.error(f"Template file not found: {template_path}")
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Loaded template: {template_name} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            raise
