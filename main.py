from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
import json
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader
from typing import List
import pandas as pd
from io import BytesIO
import base64

from models.schemas import TreeDataUpload, AnalysisRequest, ReportRequest
from services.analysis import TreeAnalyzer
from services.visualization import TreeVisualizer
from services.report_generator import ReportGenerator

# Initialize Supabase (Free PostgreSQL Database)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "your-project-url.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-anon-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Cloudinary (Free File Storage)
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "your-cloud-name"),
    api_key=os.environ.get("CLOUDINARY_API_KEY", "your-api-key"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET", "your-api-secret")
)

app = FastAPI(
    title="ArborTag API",
    description="Free hosted backend for ArborTag mobile app",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "ArborTag API - Free Hosted Version",
        "status": "online",
        "version": "1.0.0",
        "hosting": "Render.com (Free Tier)",
        "database": "Supabase (Free Tier)",
        "storage": "Cloudinary (Free Tier)"
    }

@app.get("/api/health")
async def health_check():
    try:
        # Check database connection
        result = supabase.table('trees').select("count").execute()
        db_status = "healthy"
    except:
        db_status = "error"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "hosting": "free"
    }

@app.post("/api/upload-data")
async def upload_data(data: TreeDataUpload):
    """Upload tree data to Supabase"""
    try:
        trees_list = [tree.dict() for tree in data.trees]
        
        # Insert into Supabase
        result = supabase.table('trees').insert(trees_list).execute()
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(trees_list)} trees",
            "uploaded_count": len(trees_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/analyze")
async def analyze_data(request: AnalysisRequest):
    """Analyze tree data from Supabase"""
    try:
        # Fetch data from Supabase
        if request.location:
            result = supabase.table('trees').select("*").eq('location', request.location).execute()
        else:
            result = supabase.table('trees').select("*").execute()
        
        trees = result.data
        
        if not trees:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Analyze
        analyzer = TreeAnalyzer(trees)
        stats = analyzer.get_statistics()
        species_dist = analyzer.get_species_distribution()
        carbon_by_species = analyzer.get_carbon_by_species()
        
        return {
            "status": "success",
            "statistics": stats,
            "species_distribution": species_dist,
            "carbon_by_species": carbon_by_species
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-report")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """Generate PDF report and upload to Cloudinary"""
    try:
        # Fetch data
        if request.location:
            result = supabase.table('trees').select("*").eq('location', request.location).execute()
        else:
            result = supabase.table('trees').select("*").execute()
        
        trees = result.data
        
        if not trees:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Generate report
        analyzer = TreeAnalyzer(trees)
        visualizer = TreeVisualizer(analyzer)
        generator = ReportGenerator(analyzer, visualizer)
        
        pdf_buffer = generator.generate_pdf_report(request.location)
        
        # Upload to Cloudinary
        filename = f"report_{request.location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        upload_result = cloudinary.uploader.upload(
            pdf_buffer,
            resource_type="raw",
            public_id=filename,
            folder="arbortag_reports"
        )
        
        # Store report metadata in Supabase
        report_data = {
            "location": request.location,
            "report_url": upload_result['secure_url'],
            "created_at": datetime.now().isoformat(),
            "tree_count": len(trees)
        }
        
        supabase.table('reports').insert(report_data).execute()
        
        return {
            "status": "success",
            "report_url": upload_result['secure_url'],
            "message": "Report generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    """Get overall statistics from Supabase"""
    try:
        result = supabase.table('trees').select("*").execute()
        trees = result.data
        
        if not trees:
            return {
                "total_trees": 0,
                "total_carbon": 0,
                "total_oxygen": 0,
                "avg_height": 0,
                "avg_width": 0,
                "total_locations": 0,
                "total_species": 0
            }
        
        analyzer = TreeAnalyzer(trees)
        stats = analyzer.get_statistics()
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations")
async def get_locations():
    """Get all unique locations"""
    try:
        result = supabase.table('trees').select("location").execute()
        locations = list(set([tree['location'] for tree in result.data]))
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)