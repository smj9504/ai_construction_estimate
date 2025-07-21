"""Service layer for the construction estimation application."""

def get_data_service():
    """Factory function to get data service instance."""
    from .data.persistence import DataService
    return DataService()

def get_measurement_extractor():
    """Factory function to get measurement extractor instance."""
    from .estimation.measurement_extractor import MeasurementExtractor
    return MeasurementExtractor()
