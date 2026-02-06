#!/usr/bin/env python3
"""
ONNX Model Quantization Utility
Quantizes ONNX model to INT8 for better performance on Raspberry Pi
"""

import argparse
from pathlib import Path


def quantize_model(input_model: str, output_model: str, quantization_type: str = 'dynamic'):
    """
    Quantize ONNX model
    
    Args:
        input_model: Path to input ONNX model
        output_model: Path to output quantized model
        quantization_type: 'dynamic' or 'static'
    """
    try:
        import onnx
        from onnxruntime.quantization import quantize_dynamic, quantize_static, QuantType
        from onnxruntime.quantization.calibrate import CalibrationDataReader
        import numpy as np
    except ImportError:
        print("Error: Required packages not installed")
        print("Install with: pip install onnx onnxruntime")
        return False
    
    print(f"Quantizing model: {input_model}")
    print(f"Output model: {output_model}")
    print(f"Quantization type: {quantization_type}")
    
    input_path = Path(input_model)
    output_path = Path(output_model)
    
    if not input_path.exists():
        print(f"Error: Input model not found: {input_model}")
        return False
    
    try:
        if quantization_type == 'dynamic':
            # Dynamic quantization - no calibration data needed
            print("\nPerforming dynamic quantization...")
            quantize_dynamic(
                model_input=str(input_path),
                model_output=str(output_path),
                weight_type=QuantType.QUInt8,
                optimize_model=True
            )
            print("✓ Dynamic quantization completed!")
        
        elif quantization_type == 'static':
            print("\nStatic quantization requires calibration data")
            print("This is a placeholder - implement CalibrationDataReader for your dataset")
            
            # Example static quantization (needs implementation)
            # calibration_data_reader = YourCalibrationDataReader()
            # quantize_static(
            #     model_input=str(input_path),
            #     model_output=str(output_path),
            #     calibration_data_reader=calibration_data_reader
            # )
            
            print("Static quantization not implemented - using dynamic instead")
            quantize_dynamic(
                model_input=str(input_path),
                model_output=str(output_path),
                weight_type=QuantType.QUInt8,
                optimize_model=True
            )
        
        # Check output model
        if output_path.exists():
            input_size = input_path.stat().st_size / (1024 * 1024)
            output_size = output_path.stat().st_size / (1024 * 1024)
            compression = (1 - output_size / input_size) * 100
            
            print(f"\nModel sizes:")
            print(f"  Original: {input_size:.2f} MB")
            print(f"  Quantized: {output_size:.2f} MB")
            print(f"  Compression: {compression:.1f}%")
            
            return True
        else:
            print("Error: Output model not created")
            return False
    
    except Exception as e:
        print(f"Error during quantization: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Quantize ONNX model for better edge performance'
    )
    parser.add_argument(
        'input_model',
        type=str,
        help='Path to input ONNX model'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output model (default: input_quantized.onnx)'
    )
    parser.add_argument(
        '--type',
        type=str,
        choices=['dynamic', 'static'],
        default='dynamic',
        help='Quantization type (default: dynamic)'
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output is None:
        input_path = Path(args.input_model)
        output_path = input_path.parent / f"{input_path.stem}_quantized{input_path.suffix}"
    else:
        output_path = Path(args.output)
    
    # Run quantization
    success = quantize_model(args.input_model, str(output_path), args.type)
    
    if success:
        print("\n✓ Quantization successful!")
        print(f"Quantized model saved to: {output_path}")
        print("\nUpdate your config.yaml to use the quantized model:")
        print(f"  model:\n    path: \"{output_path}\"")
        return 0
    else:
        print("\n✗ Quantization failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
