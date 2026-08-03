"""
Report formatter supporting multiple output formats.
"""

import json
import csv
import os
from datetime import datetime
from core.scanner.base import ScanResult
from core.storage.repository import ScanRepository
from app.config import AppConfig


class ReportFormatter:
    """Format and save scan results."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.repo = ScanRepository(config)

    def save(self, result: ScanResult, filename: str = None, format: str = 'json'):
        """Save a ScanResult to a file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{result.scan_type}_{result.target.replace('://', '_').replace('/', '_')}_{timestamp}.{format}"
        
        data = result.to_dict()
        self._write(data, filename, format)

    def save_dict(self, data: dict, filename: str, format: str = 'json'):
        """Save arbitrary dictionary."""
        self._write(data, filename, format)

    def _write(self, data: dict, filename: str, format: str):
        output_dir = self.config.output.output_dir
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        if format == 'json':
            # Use repository which handles encryption
            self.repo.save(data, filename)
        elif format == 'csv':
            self._write_csv(data, filepath)
        elif format == 'html':
            self._write_html(data, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _write_csv(self, data: dict, filepath: str):
        # Flatten dict for CSV
        flat = self._flatten_dict(data)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flat.keys())
            writer.writeheader()
            writer.writerow(flat)

    def _write_html(self, data: dict, filepath: str):
        html = f"<html><body><h1>God Web Master Report</h1><pre>{json.dumps(data, indent=4)}</pre></body></html>"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    @staticmethod
    def _flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ReportFormatter._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)