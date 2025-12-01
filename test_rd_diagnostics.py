"""
R.D Diagnostic Test Suite
Create intentional errors and log them to test R.D's diagnostic capabilities
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import DB
from app.core.system_logger import system_logger
import traceback
import uuid

class ErrorTestScenarios:
    """Generate various error scenarios for R.D testing"""
    
    @staticmethod
    def scenario_1_null_pointer():
        """Test Scenario 1: Null pointer / NoneType error"""
        trace_id = f"test_{uuid.uuid4().hex[:8]}"
        print(f"\n🧪 SCENARIO 1: NoneType Error (trace: {trace_id})")
        
        try:
            # Intentional error: accessing attribute on None
            buggy_value = None
            result = buggy_value.strip()  # This will fail
        except Exception as e:
            # Log to Supabase
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "scenario": "null_pointer_access",
                "function": "scenario_1_null_pointer",
                "trigger": "Accessing .strip() on None value"
            }
            system_logger.log_event(
                trace_id=trace_id,
                component="test_suite",
                event_type="scenario_1_error",
                status="error",
                details=error_details
            )
            print(f"✅ Logged error to Supabase: {str(e)}")
            return trace_id
    
    @staticmethod
    def scenario_2_division_by_zero():
        """Test Scenario 2: Division by zero error"""
        trace_id = f"test_{uuid.uuid4().hex[:8]}"
        print(f"\n🧪 SCENARIO 2: Division by Zero (trace: {trace_id})")
        
        try:
            # Intentional error: division by zero
            numerator = 100
            denominator = 0
            result = numerator / denominator  # This will fail
        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "scenario": "division_by_zero",
                "function": "scenario_2_division_by_zero",
                "trigger": "100 / 0",
                "numerator": numerator,
                "denominator": denominator
            }
            system_logger.log_event(
                trace_id=trace_id,
                component="test_suite",
                event_type="scenario_2_error",
                status="error",
                details=error_details
            )
            print(f"✅ Logged error to Supabase: {str(e)}")
            return trace_id
    
    @staticmethod
    def scenario_3_database_error():
        """Test Scenario 3: Database query error (invalid table)"""
        trace_id = f"test_{uuid.uuid4().hex[:8]}"
        print(f"\n🧪 SCENARIO 3: Database Error (trace: {trace_id})")
        
        try:
            # Intentional error: querying non-existent table
            result = DB.supabase.table("nonexistent_table_xyz").select("*").execute()
        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "scenario": "database_query_error",
                "function": "scenario_3_database_error",
                "trigger": "SELECT * FROM nonexistent_table_xyz",
                "database": "supabase",
                "table_name": "nonexistent_table_xyz"
            }
            system_logger.log_event(
                trace_id=trace_id,
                component="test_suite",
                event_type="scenario_3_error",
                status="error",
                details=error_details
            )
            print(f"✅ Logged error to Supabase: {str(e)}")
            return trace_id
    
    @staticmethod
    def scenario_4_type_error():
        """Test Scenario 4: Type error (string + int)"""
        trace_id = f"test_{uuid.uuid4().hex[:8]}"
        print(f"\n🧪 SCENARIO 4: Type Error (trace: {trace_id})")
        
        try:
            # Intentional error: adding string and integer
            message = "The answer is: "
            number = 42
            result = message + number  # This will fail
        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "scenario": "type_error",
                "function": "scenario_4_type_error",
                "trigger": "'The answer is: ' + 42",
                "var1_type": "str",
                "var2_type": "int"
            }
            system_logger.log_event(
                trace_id=trace_id,
                component="test_suite",
                event_type="scenario_4_error",
                status="error",
                details=error_details
            )
            print(f"✅ Logged error to Supabase: {str(e)}")
            return trace_id
    
    @staticmethod
    def scenario_5_function_execution_failure():
        """Test Scenario 5: Function execution failure (missing argument)"""
        trace_id = f"test_{uuid.uuid4().hex[:8]}"
        print(f"\n🧪 SCENARIO 5: Function Execution Failure (trace: {trace_id})")
        
        def add_task_buggy(title, due_date, priority):
            """Simulated buggy function"""
            if not title:
                raise ValueError("Task title cannot be empty")
            return f"Task: {title}, Due: {due_date}, Priority: {priority}"
        
        try:
            # Intentional error: calling function with empty/None title
            result = add_task_buggy(title=None, due_date="2025-12-01", priority=1)
        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "scenario": "function_execution_failure",
                "function": "add_task_buggy",
                "trigger": "add_task_buggy(title=None, ...)",
                "provided_args": {"title": None, "due_date": "2025-12-01", "priority": 1},
                "expected_behavior": "Should validate title before processing"
            }
            system_logger.log_event(
                trace_id=trace_id,
                component="test_suite",
                event_type="scenario_5_error",
                status="error",
                details=error_details
            )
            print(f"✅ Logged error to Supabase: {str(e)}")
            return trace_id

def run_all_scenarios():
    """Run all error scenarios and collect trace IDs"""
    print("=" * 60)
    print("R.D DIAGNOSTIC TEST SUITE - CREATING INTENTIONAL ERRORS")
    print("=" * 60)
    
    trace_ids = []
    
    # Run all scenarios
    trace_ids.append(ErrorTestScenarios.scenario_1_null_pointer())
    trace_ids.append(ErrorTestScenarios.scenario_2_division_by_zero())
    trace_ids.append(ErrorTestScenarios.scenario_3_database_error())
    trace_ids.append(ErrorTestScenarios.scenario_4_type_error())
    trace_ids.append(ErrorTestScenarios.scenario_5_function_execution_failure())
    
    print("\n" + "=" * 60)
    print("ALL SCENARIOS COMPLETE")
    print("=" * 60)
    print(f"\nGenerated {len(trace_ids)} test errors")
    print("\nTrace IDs for R.D analysis:")
    for i, tid in enumerate(trace_ids, 1):
        print(f"  {i}. {tid}")
    
    return trace_ids

if __name__ == "__main__":
    trace_ids = run_all_scenarios()
    
    print("\n" + "=" * 60)
    print("NEXT STEP: Use these trace IDs to test R.D")
    print("=" * 60)
    print("\nCommands to try:")
    for tid in trace_ids:
        print(f"  /trace {tid}")
    print(f"\n  /repair  (to trigger R.D on these errors)")
    print("\n" + "=" * 60)
