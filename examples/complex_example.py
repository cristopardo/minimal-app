"""
Complex example demonstrating minification capabilities.

This module contains various Python constructs to test the minifier.
"""

from typing import List, Optional, Dict, Any


class DataProcessor:
    """
    A class for processing data with various methods.
    
    This class demonstrates how the minifier handles:
    - Class docstrings
    - Method docstrings
    - Type hints
    - Multiple methods
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DataProcessor.
        
        Args:
            name: The name of the processor
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.data: List[int] = []
    
    def add_data(self, values: List[int]) -> None:
        """
        Add data to the processor.
        
        Args:
            values: List of integers to add
        """
        self.data.extend(values)
    
    def process(self) -> Dict[str, Any]:
        """
        Process the data and return statistics.
        
        Returns:
            Dictionary containing statistics about the data
        """
        if not self.data:
            return {"error": "No data to process"}
        
        return {
            "count": len(self.data),
            "sum": sum(self.data),
            "average": sum(self.data) / len(self.data),
            "min": min(self.data),
            "max": max(self.data),
        }
    
    def clear(self) -> None:
        """Clear all data from the processor."""
        self.data = []


async def async_fetch_data(url: str) -> Dict[str, Any]:
    """
    Asynchronously fetch data from a URL.
    
    This is a placeholder async function to demonstrate
    that the minifier handles async functions correctly.
    
    Args:
        url: The URL to fetch from
        
    Returns:
        Dictionary containing the fetched data
    """
    # In a real implementation, this would use aiohttp or similar
    return {"url": url, "status": "success"}


def main() -> None:
    """
    Main entry point for the example.
    
    Demonstrates usage of the DataProcessor class.
    """
    # Create a processor
    processor = DataProcessor("example", {"verbose": True})
    
    # Add some data
    processor.add_data([1, 2, 3, 4, 5])
    processor.add_data([6, 7, 8, 9, 10])
    
    # Process and print results
    results = processor.process()
    print(f"Results: {results}")
    
    # Clear the data
    processor.clear()


if __name__ == "__main__":
    main()
