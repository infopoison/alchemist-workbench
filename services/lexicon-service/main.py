import json
from fastapi import FastAPI, HTTPException

app = FastAPI()

# A dictionary to hold our astrological data in memory
knowledge_base = {}

@app.on_event("startup")
def load_knowledge_base():
    """
    Load the first_order.json file into the knowledge_base dict
    when the application starts. This is done once for low-latency responses.
    [cite: 64]
    """
    try:
        # The path is relative to where the Docker container is running (/app)
        with open("knowledge_base/first_order.json", "r") as f:
            data = json.load(f)
            # Pre-process the data for easy lookups by component type
            for component_type in data:
                knowledge_base[component_type] = {item['id']: item for item in data[component_type]}
        print("✅ Knowledge base loaded successfully.")
    except FileNotFoundError:
        print("❌ CRITICAL ERROR: knowledge_base/first_order.json not found.")
    except json.JSONDecodeError:
        print("❌ CRITICAL ERROR: Could not decode JSON from first_order.json.")


@app.get("/components/{component_type}")
def get_component_list(component_type: str):
    """
    Retrieves a list of all components of a given type.
    Example: GET /components/planets
    """
    if component_type not in knowledge_base:
        raise HTTPException(status_code=404, detail=f"Component type '{component_type}' not found.")
    
    # Return the list of components for that type
    return list(knowledge_base[component_type].values())


@app.get("/components/{component_type}/{component_id}")
def get_component_detail(component_type: str, component_id: str):
    """
    Retrieves the detailed definition for a single component.
    Example: GET /components/planets/mars
    """
    if component_type not in knowledge_base:
        raise HTTPException(status_code=404, detail=f"Component type '{component_type}' not found.")
    
    component = knowledge_base[component_type].get(component_id)
    
    if not component:
        raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found in '{component_type}'.")
        
    return component