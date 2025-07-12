#!/usr/bin/env python3

print("🔍 Starting debug server...")

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    print("✅ FastAPI imported successfully")
    
    app = FastAPI(title="Debug Server")
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    print("✅ CORS middleware added")
    
    @app.get("/")
    def root():
        return {"message": "Debug server is working", "status": "ok"}
    
    @app.get("/test")
    def test():
        return {"test": "success"}
    
    print("✅ Routes defined")
    print("🚀 Starting uvicorn...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()