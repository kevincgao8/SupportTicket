from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Literal, List
import re
import csv
import io

app = FastAPI(title="Support Ticket Triage", version="1.0.0")

class TriageRequest(BaseModel):
    text: str

class TriageResponse(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
    urgency: Literal["low", "medium", "high"]
    rationale: str
    text: str = ""  # Original ticket text

class BulkTriageResponse(BaseModel):
    tickets: List[TriageResponse]
    total_processed: int

def categorize_ticket(text: str) -> str:
    """Determine ticket category based on keywords"""
    text_lower = text.lower()
    
    # Billing keywords
    billing_keywords = [
        "charged", "charge", "billed", "bill", "payment", "pay", "money", 
        "refund", "credit", "debit", "subscription", "plan", "price", "cost",
        "invoice", "receipt", "transaction", "duplicate", "overcharge"
    ]
    
    # Bug keywords
    bug_keywords = [
        "error", "broken", "crash", "fail", "not working", "doesn't work",
        "issue", "problem", "bug", "glitch", "freeze", "hang", "slow",
        "crashed", "failed", "broken", "malfunction", "defect"
    ]
    
    # Feature keywords
    feature_keywords = [
        "add", "new feature", "enhancement", "improvement", "suggestion",
        "request", "would like", "could you", "missing", "need", "want",
        "idea", "proposal", "recommendation", "wish", "hope"
    ]
    
    # Count keyword matches
    billing_count = sum(1 for word in billing_keywords if word in text_lower)
    bug_count = sum(1 for word in bug_keywords if word in text_lower)
    feature_count = sum(1 for word in feature_keywords if word in text_lower)
    
    # Return category with highest keyword count, default to "other"
    if billing_count > bug_count and billing_count > feature_count:
        return "billing"
    elif bug_count > feature_count:
        return "bug"
    elif feature_count > 0:
        return "feature"
    else:
        return "other"

def determine_urgency(text: str, category: str) -> str:
    """Determine urgency level based on category and keywords"""
    text_lower = text.lower()
    
    # High urgency indicators
    high_urgency_keywords = [
        "urgent", "asap", "immediately", "critical", "emergency", "broken",
        "not working", "can't access", "locked out", "security", "hacked",
        "data loss", "down", "outage", "duplicate charge", "overcharged"
    ]
    
    # Medium urgency indicators
    medium_urgency_keywords = [
        "soon", "today", "this week", "important", "blocking", "stuck",
        "can't proceed", "issue", "problem", "bug", "glitch"
    ]
    
    # Category-specific urgency rules
    if category == "billing":
        # Billing issues are often high priority due to financial impact
        if any(word in text_lower for word in ["duplicate", "overcharge", "wrong amount", "double"]):
            return "high"
        elif any(word in text_lower for word in ["refund", "credit", "dispute"]):
            return "medium"
        else:
            return "medium"
    
    elif category == "bug":
        # Bug severity based on impact keywords
        if any(word in text_lower for word in ["crash", "broken", "not working", "can't access"]):
            return "high"
        elif any(word in text_lower for word in ["slow", "glitch", "minor"]):
            return "low"
        else:
            return "medium"
    
    # Check for explicit urgency keywords
    if any(word in text_lower for word in high_urgency_keywords):
        return "high"
    elif any(word in text_lower for word in medium_urgency_keywords):
        return "medium"
    
    return "low"

def generate_rationale(category: str, urgency: str, text: str) -> str:
    """Generate human-readable rationale for the classification"""
    text_lower = text.lower()
    
    rationale_parts = []
    
    # Category rationale
    if category == "billing":
        if "duplicate" in text_lower or "overcharge" in text_lower:
            rationale_parts.append("Payment/billing keywords detected")
        else:
            rationale_parts.append("Billing/payment related issue")
    elif category == "bug":
        if "crash" in text_lower or "broken" in text_lower:
            rationale_parts.append("System failure/crash keywords detected")
        else:
            rationale_parts.append("Technical issue/bug reported")
    elif category == "feature":
        rationale_parts.append("Feature request/enhancement suggested")
    else:
        rationale_parts.append("General inquiry/other category")
    
    # Urgency rationale
    if urgency == "high":
        if category == "billing":
            rationale_parts.append("Financial impact; time-sensitive")
        elif category == "bug":
            rationale_parts.append("System critical; immediate attention needed")
        else:
            rationale_parts.append("High priority indicators detected")
    elif urgency == "medium":
        if category == "billing":
            rationale_parts.append("Moderate financial impact")
        elif category == "bug":
            rationale_parts.append("Moderate system impact")
        else:
            rationale_parts.append("Moderate priority indicators")
    else:
        rationale_parts.append("Low priority; can be addressed later")
    
    return "; ".join(rationale_parts) + "."

@app.post("/api/triage", response_model=TriageResponse)
async def triage_ticket(request: TriageRequest):
    """Triage a support ticket and return structured classification"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Ticket text cannot be empty")
    
    # Determine category and urgency
    category = categorize_ticket(request.text)
    urgency = determine_urgency(request.text, category)
    rationale = generate_rationale(category, urgency, request.text)
    
    return TriageResponse(
        category=category,
        urgency=urgency,
        rationale=rationale,
        text=request.text
    )

def process_csv_tickets(csv_content: str) -> List[str]:
    """Parse CSV content and extract ticket texts from cells"""
    tickets = []
    
    try:
        # Create a StringIO object to read the CSV content
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
            for cell in row:
                # Clean the cell content and add if it's not empty
                cell_text = cell.strip()
                if cell_text and len(cell_text) > 3:  # Minimum length to be meaningful
                    tickets.append(cell_text)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    
    return tickets

@app.post("/api/triage/bulk", response_model=BulkTriageResponse)
async def triage_bulk_tickets(file: UploadFile = File(...)):
    """Triage multiple support tickets from a CSV file"""
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        # Read CSV content
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        # Extract ticket texts from CSV
        ticket_texts = process_csv_tickets(csv_text)
        
        if not ticket_texts:
            raise HTTPException(status_code=400, detail="No valid ticket texts found in CSV")
        
        # Process each ticket
        triaged_tickets = []
        for text in ticket_texts:
            category = categorize_ticket(text)
            urgency = determine_urgency(text, category)
            rationale = generate_rationale(category, urgency, text)
            
            triaged_tickets.append(TriageResponse(
                category=category,
                urgency=urgency,
                rationale=rationale,
                text=text
            ))
        
        return BulkTriageResponse(
            tickets=triaged_tickets,
            total_processed=len(triaged_tickets)
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@app.get("/")
async def read_index():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

# Serve static files from root (after API routes)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
