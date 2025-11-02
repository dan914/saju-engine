#!/usr/bin/env python3
"""
Policy Signature Auditor - CLI Entry Point

Commands:
  sign   - Sign policy file(s) with SHA-256 hash
  verify - Verify policy file(s) signatures
  diff   - Compare two policy files (excluding signatures)

Exit codes:
  0 - Success
  1 - Verification failed (mismatch)
  2 - Error (file not found, invalid JSON, etc.)
"""

import argparse
import glob
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from policy_signature_auditor.auditor import diff_files, sign_file, verify_file


def cmd_sign(args):
    """Sign command handler."""
    files = _expand_patterns(args.files)

    if not files:
        print("❌ No files matched the pattern", file=sys.stderr)
        return 2

    results = []
    for file_path in files:
        try:
            result = sign_file(
                file_path,
                in_place=args.in_place,
                write_sidecar=args.write_sidecar,
                strict=args.strict,
            )
            results.append(result)

            status = "✅ Signed"
            if args.in_place:
                status += " (in-place)"
            if args.write_sidecar:
                status += " (sidecar)"

            print(f"{status}: {result['path']}")
            print(f"   SHA-256: {result['hash']}")

        except Exception as e:
            print(f"❌ Error signing {file_path}: {e}", file=sys.stderr)
            return 2

    print(f"\n✅ Signed {len(results)} file(s)")
    return 0


def cmd_verify(args):
    """Verify command handler."""
    files = _expand_patterns(args.files)

    if not files:
        print("❌ No files matched the pattern", file=sys.stderr)
        return 2

    all_valid = True
    results = []

    for file_path in files:
        try:
            result = verify_file(file_path, strict=args.strict)
            results.append(result)

            if result["is_valid"]:
                print(f"✅ Valid: {result['path']}")
                print(f"   SHA-256: {result['expected']}")
            else:
                all_valid = False
                print(f"❌ Invalid: {result['path']}")
                print(f"   Expected: {result['expected']}")
                print(f"   Actual:   {result['actual']}")

        except Exception as e:
            all_valid = False
            print(f"❌ Error verifying {file_path}: {e}", file=sys.stderr)
            return 2

    print(f"\n{'✅' if all_valid else '❌'} Verified {len(results)} file(s)")
    return 0 if all_valid else 1


def cmd_diff(args):
    """Diff command handler."""
    if len(args.files) != 2:
        print("❌ Diff requires exactly 2 files", file=sys.stderr)
        return 2

    try:
        result = diff_files(args.files[0], args.files[1])

        if result["are_equal"]:
            print("✅ Files are structurally identical (excluding signatures)")
            print(f"   A: {args.files[0]}")
            print(f"   B: {args.files[1]}")
        else:
            print("❌ Files differ")
            print(f"   A: {args.files[0]}")
            print(f"   B: {args.files[1]}")

            if args.verbose:
                print("\nCanonical A:")
                print(result["canonical_a"][:500])
                print("\nCanonical B:")
                print(result["canonical_b"][:500])

        return 0 if result["are_equal"] else 1

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 2


def _expand_patterns(patterns):
    """Expand glob patterns to file list."""
    files = []
    for pattern in patterns:
        # Handle glob patterns
        if "*" in pattern or "?" in pattern:
            matched = glob.glob(pattern, recursive=True)
            files.extend(matched)
        else:
            files.append(pattern)

    # Deduplicate and sort
    return sorted(set(files))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Policy Signature Auditor - Sign, verify, and diff policy files"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Sign command
    sign_parser = subparsers.add_parser("sign", help="Sign policy file(s)")
    sign_parser.add_argument("files", nargs="+", help="Policy file(s) or pattern")
    sign_parser.add_argument("--in-place", action="store_true", help="Update file with signature")
    sign_parser.add_argument(
        "--write-sidecar", action="store_true", help="Write <file>.sha256 sidecar"
    )
    sign_parser.add_argument("--strict", action="store_true", help="Validate meta fields")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify policy file(s)")
    verify_parser.add_argument("files", nargs="+", help="Policy file(s) or pattern")
    verify_parser.add_argument("--strict", action="store_true", help="Validate meta fields")

    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Compare two policy files")
    diff_parser.add_argument("files", nargs=2, help="Two policy files to compare")
    diff_parser.add_argument("--verbose", "-v", action="store_true", help="Show canonical forms")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 2

    # Route to command handler
    if args.command == "sign":
        return cmd_sign(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "diff":
        return cmd_diff(args)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
