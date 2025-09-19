"""
Validation utility for EchoScan pipeline outputs using Pydantic schemas.
Ensures all pipeline outputs conform to expected schema before returning results.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator, ValidationError
import json

# Configure logging for validation errors
validation_logger = logging.getLogger('echoscan.validation')


class SBSHHashSchema(BaseModel):
    """Schema for SBSH hash output validation."""
    delta_hash: str = Field(..., description="Numeric string representing delta S value")
    fold_hash: str = Field(..., min_length=1, description="Hexadecimal fold hash")
    glyph_hash: Optional[str] = Field(None, description="Optional glyph hash")
    status: str = Field(..., description="Hash status (LOCKED/ERROR)")
    
    @validator('delta_hash')
    def validate_delta_hash(cls, v):
        try:
            float(v)
            return v
        except ValueError:
            raise ValueError("delta_hash must be a valid numeric string")
    
    @validator('fold_hash')
    def validate_fold_hash(cls, v):
        try:
            int(v, 16)
            return v
        except ValueError:
            raise ValueError("fold_hash must be valid hexadecimal")
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['LOCKED', 'ERROR']:
            raise ValueError("status must be 'LOCKED' or 'ERROR'")
        return v


class EchoVerifierSchema(BaseModel):
    """Schema for EchoVerifier output validation."""
    input: str = Field(..., description="Original input text (truncated)")
    verdict: str = Field(..., description="Authenticity verdict")
    delta_s: float = Field(..., ge=0.0, le=1.0, description="Delta S value")
    fold_vector: List[float] = Field(..., min_items=1, description="Echo fold vector")
    glyph_id: str = Field(..., pattern=r'^GHX-[A-F0-9]{4}$', description="Glyph identifier")
    ancestry_depth: int = Field(..., ge=1, le=20, description="Ancestry depth")
    echo_sense: float = Field(..., ge=0.0, le=1.0, description="EchoSense trust score")
    vault_permission: bool = Field(..., description="Vault access permission")
    
    @validator('verdict')
    def validate_verdict(cls, v):
        if v not in ['Authentic', 'Plausible', 'Hallucination']:
            raise ValueError("verdict must be 'Authentic', 'Plausible', or 'Hallucination'")
        return v
    
    @validator('fold_vector')
    def validate_fold_vector(cls, v):
        if not all(0.0 <= val <= 1.0 for val in v):
            raise ValueError("all fold_vector values must be between 0.0 and 1.0")
        return v


class DetectorResultSchema(BaseModel):
    """Schema for individual detector output validation."""
    echo_score_penalty: Optional[float] = Field(0, description="Score penalty/modifier")
    echo_score_modifier: Optional[float] = Field(0, description="Score modifier")
    source_classification: Optional[str] = Field(None, description="Source classification")
    advisory_flag: Optional[str] = Field(None, description="Advisory flag message")


class PipelineResultSchema(BaseModel):
    """Schema for complete pipeline output validation."""
    EchoScore: float = Field(..., ge=0.0, le=100.0, description="Overall echo score")
    Decision: str = Field(..., description="Overall pipeline decision") 
    AdvisoryFlags: List[str] = Field(default_factory=list, description="Advisory flags")
    FullResults: Dict[str, Any] = Field(..., description="Complete module results")
    
    @validator('Decision')
    def validate_decision(cls, v):
        valid_decisions = ['Authentic', 'Plausible', 'Synthetic', 'Questionable', 'Error']
        if v not in valid_decisions:
            raise ValueError(f"Decision must be one of {valid_decisions}")
        return v


class ValidationUtility:
    """Central validation utility for EchoScan pipeline outputs."""
    
    def __init__(self, error_reporter=None):
        self.error_reporter = error_reporter
        self.validation_errors = []
    
    def validate_sbsh_output(self, output: Dict[str, Any]) -> bool:
        """Validate SBSH hash output against schema."""
        try:
            SBSHHashSchema(**output)
            validation_logger.info("SBSH output validation passed")
            return True
        except ValidationError as e:
            error_msg = f"SBSH validation failed: {e}"
            validation_logger.error(error_msg)
            self.validation_errors.append(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ValidationError", error_msg, {"output": output})
            return False
    
    def validate_echoverifier_output(self, output: Dict[str, Any]) -> bool:
        """Validate EchoVerifier output against schema."""
        try:
            EchoVerifierSchema(**output)
            validation_logger.info("EchoVerifier output validation passed")
            return True
        except ValidationError as e:
            error_msg = f"EchoVerifier validation failed: {e}"
            validation_logger.error(error_msg)
            self.validation_errors.append(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ValidationError", error_msg, {"output": output})
            return False
    
    def validate_detector_output(self, output: Dict[str, Any], detector_name: str) -> bool:
        """Validate individual detector output against schema."""
        try:
            DetectorResultSchema(**output)
            validation_logger.info(f"Detector {detector_name} output validation passed")
            return True
        except ValidationError as e:
            error_msg = f"Detector {detector_name} validation failed: {e}"
            validation_logger.error(error_msg)
            self.validation_errors.append(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ValidationError", error_msg, 
                                            {"detector": detector_name, "output": output})
            return False
    
    def validate_pipeline_output(self, output: Dict[str, Any]) -> bool:
        """Validate complete pipeline output against schema."""
        try:
            PipelineResultSchema(**output)
            validation_logger.info("Pipeline output validation passed")
            return True
        except ValidationError as e:
            error_msg = f"Pipeline validation failed: {e}"
            validation_logger.error(error_msg)
            self.validation_errors.append(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ValidationError", error_msg, {"output": output})
            return False
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.validation_errors.copy()
    
    def clear_validation_errors(self):
        """Clear accumulated validation errors."""
        self.validation_errors.clear()
    
    def validate_and_sanitize(self, output: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
        """Validate output and return sanitized version or raise exception."""
        schema_map = {
            'sbsh': SBSHHashSchema,
            'echoverifier': EchoVerifierSchema, 
            'detector': DetectorResultSchema,
            'pipeline': PipelineResultSchema
        }
        
        if schema_type not in schema_map:
            raise ValueError(f"Unknown schema type: {schema_type}")
        
        try:
            schema = schema_map[schema_type]
            validated = schema(**output)
            return validated.dict()
        except ValidationError as e:
            error_msg = f"{schema_type} validation failed: {e}"
            validation_logger.error(error_msg)
            if self.error_reporter:
                self.error_reporter.log_error("ValidationError", error_msg, {"output": output})
            raise ValidationError(error_msg) from e


# Global validation instance
validator = ValidationUtility()


def validate_output(output: Dict[str, Any], output_type: str) -> bool:
    """Convenience function for output validation."""
    return validator.validate_and_sanitize(output, output_type)