from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader

from models.schemas import TreeDataUpload, AnalysisRequest, ReportRequest
from services.analysis import TreeAnalyzer
from services.report_generator import ReportGenerator
# Visualization removed to avoid matplotlib dependency

# Initialize
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

app = FastAPI(title="ArborTag API", version="1.0.0")

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
        "message": "ArborTag API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/upload-data")
async def upload(data: TreeDataUpload):
    try:
        trees = [tree.dict() for tree in data.trees]
        result = supabase.table('trees').insert(trees).execute()
        return {
            "status": "success",
            "message": f"Uploaded {len(trees)} trees",
            "count": len(trees)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    try:
        query = supabase.table('trees').select("*")
        if request.location:
            query = query.eq('location', request.location)
        result = query.execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="No data found")

        analyzer = TreeAnalyzer(result.data)
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
async def report(request: ReportRequest):
    try:
        query = supabase.table('trees').select("*")
        if request.location:
            query = query.eq('location', request.location)
        result = query.execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="No data found")

        analyzer = TreeAnalyzer(result.data)
        generator = ReportGenerator(analyzer, None)  # No visualizer
        pdf = generator.generate_pdf_report(request.location)

        filename = f"report_{request.location}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        upload = cloudinary.uploader.upload(
            pdf,
            resource_type="raw",
            public_id=filename,
            folder="arbortag_reports"
        )

        return {
            "status": "success",
            "report_url": upload['secure_url'],
            "message": "Report generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def stats():
    try:
        result = supabase.table('trees').select("*").execute()

        if not result.data:
            return {
                "total_trees": 0,
                "total_carbon": 0,
                "total_oxygen": 0,
                "avg_height": 0,
                "avg_width": 0,
                "total_locations": 0,
                "total_species": 0
            }

        analyzer = TreeAnalyzer(result.data)
        return analyzer.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/locations")
async def get_locations():
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