import json

def load_field_descriptions():
    """Load Georgian field descriptions from JSON file"""
    try:
        with open('field_descrptions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading field descriptions: {e}")
        return []

def get_field_context() -> str:
    """Generate Georgian context from field descriptions"""
    fields = load_field_descriptions()
    
    context = "ველების აღწერა და მნიშვნელობა:\n\n"
    
    for field in fields:
        field_name = field.get('field_name', '')
        label_name = field.get('label_name', '')
        field_desc = field.get('field_desc', '')
        
        if field_name and field_desc:
            context += f"• {label_name} ({field_name}): {field_desc}\n"
    
    return context

def get_field_mapping() -> dict:
    """Get mapping of field names to Georgian labels and descriptions"""
    fields = load_field_descriptions()
    mapping = {}
    
    for field in fields:
        field_name = field.get('field_name', '')
        if field_name:
            mapping[field_name] = {
                'label': field.get('label_name', ''),
                'description': field.get('field_desc', ''),
                'questions': field.get('question', '')
            }
    
    return mapping
