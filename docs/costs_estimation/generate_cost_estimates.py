#!/usr/bin/env python3
"""
Cost Estimation Generator for CDK Stacks

This script synthesizes each CDK stack individually and generates cost estimates
using AWS CloudFormation's estimate-template-cost command.
"""

import os
import json
import subprocess
import sys
from pathlib import Path

# Stack configurations - based on app.py
STACKS = {
    "documentstack": {
        "name": "AWSomeBuilder2-DocumentWorkflowStack",
        "description": "Document workflow processing stack"
    },
    "backendstack": {
        "name": "AWSomeBuilder2-BackendStack", 
        "description": "Database infrastructure stack"
    },
    "apistack": {
        "name": "AWSomeBuilder2-ApiStack",
        "description": "API Gateway stack"
    },
    "genaistack": {
        "name": "AWSomeBuilder2-VirtualAssistantStack",
        "description": "GenAI virtual assistant stack"
    }
}

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def synthesize_stack(stack_id):
    """Synthesize a specific CDK stack"""
    print(f"Synthesizing stack: {stack_id}")
    
    # Change to project root
    project_root = Path(__file__).parent.parent.parent
    
    success, stdout, stderr = run_command(f"cdk synth {stack_id}", cwd=project_root)
    
    if not success:
        print(f"Error synthesizing {stack_id}: {stderr}")
        return False
    
    print(f"Successfully synthesized {stack_id}")
    return True

def get_template_path(stack_name):
    """Get the path to the synthesized CloudFormation template"""
    project_root = Path(__file__).parent.parent.parent
    template_path = project_root / "cdk.out" / f"{stack_name}.template.json"
    return template_path

def estimate_stack_cost(stack_id, stack_info):
    """Generate cost estimate for a stack using AWS CLI"""
    print(f"Generating cost estimate for: {stack_id}")
    
    template_path = get_template_path(stack_info["name"])
    
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        return False
    
    # Generate cost estimate using AWS CLI
    estimate_command = f"aws cloudformation estimate-template-cost --template-body file://{template_path}"
    
    success, stdout, stderr = run_command(estimate_command)
    
    if not success:
        print(f"Error estimating cost for {stack_id}: {stderr}")
        return False
    
    # Save the cost estimate
    output_file = Path(__file__).parent / f"{stack_id}_cost_estimate.json"
    
    try:
        # Parse and pretty-print the JSON response
        cost_data = json.loads(stdout)
        with open(output_file, 'w') as f:
            json.dump(cost_data, f, indent=2)
        
        print(f"Cost estimate saved to: {output_file}")
        
        # Extract and display the estimate URL
        if 'Url' in cost_data:
            print(f"AWS Cost Calculator URL: {cost_data['Url']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error parsing cost estimate response: {e}")
        return False

def generate_summary_report():
    """Generate a summary report of all cost estimates"""
    print("Generating summary report...")
    
    summary = {
        "generated_at": subprocess.check_output(["date"], text=True).strip(),
        "stacks": {},
        "total_estimated_monthly_cost": "See individual stack estimates",
        "notes": [
            "These are rough estimates based on CloudFormation templates",
            "Actual costs will vary based on usage patterns",
            "Some services may have free tier benefits not reflected here",
            "Consider Reserved Instances and Savings Plans for production workloads"
        ]
    }
    
    costs_dir = Path(__file__).parent
    
    for stack_id, stack_info in STACKS.items():
        estimate_file = costs_dir / f"{stack_id}_cost_estimate.json"
        
        if estimate_file.exists():
            try:
                with open(estimate_file, 'r') as f:
                    cost_data = json.load(f)
                
                summary["stacks"][stack_id] = {
                    "name": stack_info["name"],
                    "description": stack_info["description"],
                    "estimate_file": str(estimate_file.name),
                    "calculator_url": cost_data.get("Url", "Not available"),
                    "status": "Generated"
                }
            except Exception as e:
                summary["stacks"][stack_id] = {
                    "name": stack_info["name"],
                    "description": stack_info["description"],
                    "status": f"Error reading estimate: {e}"
                }
        else:
            summary["stacks"][stack_id] = {
                "name": stack_info["name"],
                "description": stack_info["description"],
                "status": "Estimate not generated"
            }
    
    # Save summary
    summary_file = costs_dir / "cost_estimates_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary report saved to: {summary_file}")

def main():
    """Main execution function"""
    print("Starting CDK Cost Estimation Process")
    print("=" * 50)
    
    # Check if AWS CLI is available
    success, _, _ = run_command("aws --version")
    if not success:
        print("Error: AWS CLI not found. Please install and configure AWS CLI.")
        sys.exit(1)
    
    # Check if CDK is available
    success, _, _ = run_command("cdk --version")
    if not success:
        print("Error: CDK CLI not found. Please install AWS CDK.")
        sys.exit(1)
    
    print("Prerequisites check passed")
    print()
    
    # Process each stack
    for stack_id, stack_info in STACKS.items():
        print(f"Processing {stack_id} ({stack_info['name']})")
        print("-" * 40)
        
        # Synthesize the stack
        if not synthesize_stack(stack_id):
            print(f"Skipping cost estimation for {stack_id} due to synthesis error")
            continue
        
        # Generate cost estimate
        if not estimate_stack_cost(stack_id, stack_info):
            print(f"Failed to generate cost estimate for {stack_id}")
        
        print()
    
    # Generate summary report
    generate_summary_report()
    
    print("Cost estimation process completed!")
    print("\nNext steps:")
    print("1. Review individual cost estimate files")
    print("2. Visit the AWS Cost Calculator URLs for detailed breakdowns")
    print("3. Use the AWS Pricing MCP server for more detailed analysis")

if __name__ == "__main__":
    main()
