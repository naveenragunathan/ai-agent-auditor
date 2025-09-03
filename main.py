from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List, Union
import asyncio
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

from agents.audit_agents import AuditAgents
from scrapers.website_scraper import WebsiteScraper
from scrapers.profile_scraper import ProfileScraper
from database.db_manager import DatabaseManager

load_dotenv()

app = FastAPI(title="AI Website Audit Agent Suite", version="1.0.0")

# Configure static files
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Ensure static directory exists
os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class AuditRequest(BaseModel):
    website_url: HttpUrl
    industry: Optional[str] = Field(
        "general",
        description="The industry of the business (e.g., 'coaching', 'consulting', 'ecommerce')"
    )
    monthly_visitors: Optional[int] = Field(
        None,
        description="Average monthly visitors to the website. If not provided, will use industry defaults."
    )
    average_client_value: Optional[float] = Field(
        None,
        description="Average value of a new client/customer in USD. If not provided, will use industry averages."
    )
    creator_profile: Optional[str] = Field(
        None,
        description="Optional URL to the creator's profile (LinkedIn, Twitter, etc.)"
    )
    email: Optional[str] = Field(
        None,
        description="Optional email address to receive the audit report"
    )

# Initialize components
try:
    print("Initializing components...")
    audit_agents = AuditAgents()
    website_scraper = WebsiteScraper()
    profile_scraper = ProfileScraper()
    db_manager = DatabaseManager()
    print("Components initialized successfully")
except Exception as e:
    error_msg = f"Error initializing components: {str(e)}"
    print(error_msg)
    # Initialize with None to allow the app to start, but it will fail on actual requests
    audit_agents = None
    website_scraper = None
    profile_scraper = None
    db_manager = None
    # Re-raise the exception to prevent the app from starting with broken components
    raise RuntimeError(error_msg)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def _process_audit(
    website_url: str,
    industry: str = "general",
    monthly_visitors: Optional[int] = None,
    average_client_value: Optional[float] = None,
    creator_profile: Optional[str] = None,
    email: Optional[str] = None
) -> Dict[str, Any]:
    """Process an audit request and return the results"""
    # Generate a unique audit ID
    audit_id = str(uuid.uuid4())
    
    try:
        # Step 1: Scrape website data
        print(f"[{audit_id}] Scraping website: {website_url}")
        website_data = await website_scraper.scrape(website_url)
        
        # Step 2: Scrape profile data (if provided)
        profile_data = {}
        if creator_profile:
            print(f"Scraping profile: {creator_profile}")
            profile_data = await profile_scraper.scrape(creator_profile)
        
        # Prepare audit parameters
        audit_params = {
            "industry": industry,
            "monthly_visitors": monthly_visitors,
            "average_client_value": average_client_value,
            "website_url": website_url
        }
        
        # Step 3: Run the audit
        print(f"[{audit_id}] Running audit...")
        audit_results = await audit_agents.run_all_agents(
            website_data=website_data,
            profile_data=profile_data,
            audit_params=audit_params
        )
        
        # Add metadata to the results
        audit_results['metadata'] = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "website_url": website_url,
            "industry": industry,
            "monthly_visitors": monthly_visitors,
            "average_client_value": average_client_value
        }
        
        # Step 4: Save to database (if configured)
        if email:
            try:
                await db_manager.save_audit(
                    email=email,
                    website_url=website_url,
                    profile_url=creator_profile or "",  # Ensure this is never None
                    audit_data=audit_results
                )
            except Exception as e:
                print(f"Error saving to database: {str(e)}")
                # Don't fail the request if database save fails
                pass
        
        # Step 5: Prepare response
        return {
            "status": "success",
            "audit_id": audit_id,
            "data": audit_results
        }
    except Exception as e:
        error_msg = f"[{audit_id}] Error during audit: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "audit_id": audit_id,
            "error": str(e),
            "details": str(e) if str(e) else "Unknown error occurred"
        }

@app.post("/audit")
async def run_audit(request: AuditRequest):
    """Main audit endpoint"""
    if not all([audit_agents, website_scraper, profile_scraper, db_manager]):
        raise HTTPException(
            status_code=503, 
            detail="One or more services are not initialized. Check server logs for errors on startup."
        )
    
    try:
        results = await _process_audit(
            website_url=str(request.website_url),
            industry=request.industry,
            monthly_visitors=request.monthly_visitors,
            average_client_value=request.average_client_value,
            creator_profile=request.creator_profile,
            email=request.email
        )
        
        if results.get("status") == "error":
            # The audit process itself returned an error
            raise HTTPException(
                status_code=500,
                detail=results.get("details", "An unknown error occurred during the audit.")
            )
        
        return JSONResponse(content=results)
        
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions from the audit process
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unhandled exception in /audit endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if required components are initialized
        checks = {
            "api_online": True,
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "database_connected": db_manager.is_configured() if db_manager else False,
            "components_initialized": all([audit_agents, website_scraper, profile_scraper])
        }
        
        status = "healthy" if all(checks.values()) else "degraded"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "service": "AI Website Audit Agent Suite",
            "version": "1.0.0",
            "documentation": "/docs"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')

# Simple health check endpoint that redirects to the full health check
from fastapi.responses import RedirectResponse

@app.get("/health")
async def simple_health_check():
    """Simple health check endpoint that redirects to the full health check"""
    return RedirectResponse(url="/api/health")

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"Starting server on {host}:{port}")
    print(f"Environment: {os.getenv('ENV', 'development')}")
    print(f"Debug mode: {reload}")
    
    # Run the FastAPI app
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        workers=int(os.getenv("WEB_CONCURRENCY", 1))
    )
