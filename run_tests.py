#!/usr/bin/env python3
"""
MentaY API Security Test Runner

This script provides a convenient way to run the complete test suite
with proper configuration and reporting for CI/CD environments.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def setup_test_environment():
    """Setup test environment and configuration."""
    # Load test environment variables
    test_env_file = Path(__file__).parent / ".env.test"
    if test_env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(test_env_file)
        print(f"✅ Loaded test configuration from {test_env_file}")
    else:
        print("⚠️  No .env.test file found, using default configuration")


def run_pytest(args):
    """Run pytest with specified arguments."""
    cmd = ["python", "-m", "pytest"] + args
    
    print(f"🧪 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="MentaY API Security Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all tests
  python run_tests.py --auth              # Run only authentication tests
  python run_tests.py --security          # Run only security tests
  python run_tests.py --streaming         # Run only streaming tests
  python run_tests.py --fast              # Skip slow tests
  python run_tests.py --coverage          # Run with coverage report
  python run_tests.py --parallel          # Run tests in parallel
  python run_tests.py --ci                # CI/CD mode with reports
        """
    )
    
    # Test selection arguments
    parser.add_argument("--auth", action="store_true", 
                       help="Run only authentication tests")
    parser.add_argument("--security", action="store_true", 
                       help="Run only security-related tests")
    parser.add_argument("--streaming", action="store_true", 
                       help="Run only streaming tests")
    parser.add_argument("--rate-limit", action="store_true", 
                       help="Run only rate limiting tests")
    parser.add_argument("--audit", action="store_true", 
                       help="Run only audit logging tests")
    parser.add_argument("--harmful", action="store_true", 
                       help="Run only harmful content tests")
    parser.add_argument("--injection", action="store_true", 
                       help="Run only prompt injection tests")
    
    # Test execution arguments
    parser.add_argument("--fast", action="store_true", 
                       help="Skip slow tests")
    parser.add_argument("--parallel", action="store_true", 
                       help="Run tests in parallel")
    parser.add_argument("--coverage", action="store_true", 
                       help="Generate coverage report")
    parser.add_argument("--ci", action="store_true", 
                       help="CI/CD mode with XML reports")
    
    # Output arguments
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", 
                       help="Quiet output")
    parser.add_argument("--html-report", 
                       help="Generate HTML report at specified path")
    parser.add_argument("--json-report", 
                       help="Generate JSON report at specified path")
    
    # Additional pytest arguments
    parser.add_argument("pytest_args", nargs="*", 
                       help="Additional arguments to pass to pytest")
    
    args = parser.parse_args()
    
    # Setup test environment
    setup_test_environment()
    
    # Build pytest command arguments
    pytest_args = []
    
    # Test selection
    if args.auth:
        pytest_args.extend(["tests/test_authentication.py"])
    elif args.security:
        pytest_args.extend(["-m", "security"])
    elif args.streaming:
        pytest_args.extend(["tests/test_streaming.py"])
    elif args.rate_limit:
        pytest_args.extend(["tests/test_rate_limiting.py"])
    elif args.audit:
        pytest_args.extend(["tests/test_audit_logging.py"])
    elif args.harmful:
        pytest_args.extend(["tests/test_harmful_content.py"])
    elif args.injection:
        pytest_args.extend(["tests/test_prompt_injection.py"])
    else:
        pytest_args.extend(["tests/"])
    
    # Test execution options
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    
    if args.parallel:
        pytest_args.extend(["-n", "auto"])
    
    if args.coverage:
        pytest_args.extend([
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    if args.ci:
        pytest_args.extend([
            "--junitxml=test-results.xml",
            "--cov=app",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term"
        ])
    
    # Output options
    if args.verbose:
        pytest_args.extend(["-v"])
    elif args.quiet:
        pytest_args.extend(["-q"])
    
    if args.html_report:
        pytest_args.extend([f"--html={args.html_report}", "--self-contained-html"])
    
    if args.json_report:
        pytest_args.extend([f"--json-report", f"--json-report-file={args.json_report}"])
    
    # Add any additional pytest arguments
    if args.pytest_args:
        pytest_args.extend(args.pytest_args)
    
    # Run tests
    print("🛡️  MentaY API Security Test Suite")
    print("=" * 60)
    
    exit_code = run_pytest(pytest_args)
    
    # Print summary
    if exit_code == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    # Print additional information
    if args.coverage and exit_code == 0:
        print("📊 Coverage report generated in htmlcov/index.html")
    
    if args.html_report and exit_code == 0:
        print(f"📋 HTML report generated at {args.html_report}")
    
    if args.ci:
        print("🔧 CI/CD reports generated:")
        print("   - test-results.xml (JUnit format)")
        print("   - coverage.xml (Cobertura format)")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
