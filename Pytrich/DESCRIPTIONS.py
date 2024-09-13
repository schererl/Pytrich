import json
import os

class Descriptions:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Descriptions, cls).__new__(cls)
            cls._instance._load_descriptions()
        return cls._instance

    def _load_descriptions(self):
        """Load descriptions from JSON file."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "../descriptions.json")
        
        with open(json_path, "r") as f:
            self.descriptions = json.load(f)

    def __call__(self, key, value):
        """Get description by key and format it with the value, handling precision for floats."""
        # Fetch the description details from the JSON
        description_info = self.descriptions.get(key, {})
        description = description_info.get("description", "No description available")
        
        # Check if the value should be formatted with precision
        value_type = description_info.get("type", None)
        precision = description_info.get("precision", None)
        
        # If it's a float and precision is specified, format the value accordingly
        if value_type == "float" and isinstance(value, (float, int)):
            value = f'{value:.{precision}f}' if precision is not None else f'{value}'
        
        return f'{description} : {value}'
