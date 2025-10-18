"""
Policy Signature Auditor v1.0

RFC-8785 style policy signing and verification system.
"""

from .auditor import diff_files, diff_policies, sign_file, sign_policy, verify_file, verify_policy
from .jcs import canonicalize

__version__ = "1.0.0"
__all__ = [
    "sign_policy",
    "verify_policy",
    "diff_policies",
    "sign_file",
    "verify_file",
    "diff_files",
    "canonicalize"
]
