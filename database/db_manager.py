import asyncio
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Simple file-based storage for now (can be replaced with Supabase later)
class DatabaseManager:
    def __init__(self):
        self.data_dir = "data"
        self.audits_file = os.path.join(self.data_dir, "audits.json")
        self._ensure_data_dir()
    
    def is_configured(self) -> bool:
        """Check if the database is properly configured"""
        try:
            # Check if data directory exists and is writable
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)
            
            # Check if we can read/write to the audits file
            test_file = os.path.join(self.data_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            return True
        except Exception as e:
            print(f"Database configuration check failed: {str(e)}")
            return False
            
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.audits_file):
            with open(self.audits_file, 'w') as f:
                json.dump([], f)
    
    async def save_audit(self, email: str, website_url: str, profile_url: Optional[str], audit_data: Dict[str, Any]) -> str:
        """Save audit data to storage"""
        try:
            audit_id = str(uuid.uuid4())
            audit_record = {
                "id": audit_id,
                "email": email,
                "website_url": website_url,
                "profile_url": profile_url,
                "audit_data": audit_data,
                "created_at": datetime.now().isoformat()
            }
            
            # Load existing audits
            with open(self.audits_file, 'r') as f:
                audits = json.load(f)
            
            # Add new audit
            audits.append(audit_record)
            
            # Save back to file
            with open(self.audits_file, 'w') as f:
                json.dump(audits, f, indent=2)
            
            print(f"Audit saved with ID: {audit_id}")
            return audit_id
        
        except Exception as e:
            print(f"Error saving audit: {str(e)}")
            return ""
    
    async def get_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit by ID"""
        try:
            with open(self.audits_file, 'r') as f:
                audits = json.load(f)
            
            for audit in audits:
                if audit["id"] == audit_id:
                    return audit
            
            return None
        
        except Exception as e:
            print(f"Error retrieving audit: {str(e)}")
            return None
    
    async def get_audits_by_email(self, email: str) -> list:
        """Get all audits for a specific email"""
        try:
            with open(self.audits_file, 'r') as f:
                audits = json.load(f)
            
            return [audit for audit in audits if audit["email"] == email]
        
        except Exception as e:
            print(f"Error retrieving audits by email: {str(e)}")
            return []
