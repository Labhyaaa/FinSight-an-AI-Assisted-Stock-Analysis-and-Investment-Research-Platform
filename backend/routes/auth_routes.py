"""
Auth Routes – Registration, OTP-based Login, Password management.
Tickertape-style: user enters email/phone → gets OTP → verifies → logged in.
"""
import random
import re
from flask import Blueprint, request, jsonify
from functools import wraps
import bcrypt

from models.user import (
    create_user, find_by_email, find_by_phone, find_by_id,
    create_otp, verify_otp, verify_email, update_password
)
from services.email_service import send_otp_email, send_login_otp, send_password_reset_otp
from config import Config

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

auth_bp = Blueprint("auth", __name__)


def _create_token(user_id, role):
    """Lazy import to avoid circular imports."""
    from app import create_token
    return create_token(user_id, role)


def _get_current_user():
    """Extract user from JWT in Authorization header."""
    from app import decode_token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        return None
    return find_by_id(payload["user_id"])


def _is_phone(identifier):
    """Check if identifier looks like a phone number."""
    cleaned = re.sub(r'[\s\-\+\(\)]', '', identifier)
    return cleaned.isdigit() and len(cleaned) >= 10


def _find_user_by_identifier(identifier):
    """Find user by email or phone number."""
    identifier = identifier.strip()
    if _is_phone(identifier):
        return find_by_phone(identifier), "phone"
    else:
        return find_by_email(identifier.lower()), "email"


def _generate_otp():
    return str(random.randint(100000, 999999))


# ══════════════════════════════════════════════════════════════
#  REGISTRATION
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if not name:
        return jsonify({"error": "Name is required"}), 400

    existing = find_by_email(email)
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = create_user(email, password_hash, name)

    # Generate and send verification OTP
    otp_code = _generate_otp()
    create_otp(user["id"], otp_code, Config.OTP_EXPIRY_MINUTES)
    send_otp_email(email, otp_code)

    response = {
        "message": "Registration successful. Check your email for OTP.",
        "user_id": user["id"],
        "email": email,
    }
    # In DEBUG mode, expose OTP directly so it can be shown on the page
    if Config.DEBUG:
        response["dev_otp"] = otp_code

    return jsonify(response), 201


# ══════════════════════════════════════════════════════════════
#  OTP-BASED LOGIN (Tickertape-style)
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    """Step 1: User provides email or phone → we send an OTP."""
    data = request.get_json()
    identifier = data.get("identifier", "").strip()

    if not identifier:
        return jsonify({"error": "Email or phone number is required"}), 400

    user, method = _find_user_by_identifier(identifier)
    if not user:
        return jsonify({"error": "No account found with this " + method}), 404

    if not user.get("is_active", True):
        return jsonify({"error": "Account is disabled. Contact admin."}), 403

    otp_code = _generate_otp()
    create_otp(user["id"], otp_code, Config.OTP_EXPIRY_MINUTES)

    # Send OTP (in dev mode, prints to console)
    contact = user.get("email") or identifier
    send_login_otp(contact, otp_code, method)

    # For masking, show the identifier the user typed (phone or email)
    display_contact = identifier if method == "phone" else contact

    return jsonify({
        "message": f"OTP sent to your {method}",
        "method": method,
        "user_id": user["id"],
        "masked_contact": _mask_contact(display_contact, method),
    })


@auth_bp.route("/verify-login-otp", methods=["POST"])
def verify_login_otp():
    """Step 2: User provides OTP → we verify and return JWT."""
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    otp_code = data.get("otp", "").strip()

    if not identifier or not otp_code:
        return jsonify({"error": "Identifier and OTP are required"}), 400

    user, method = _find_user_by_identifier(identifier)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not verify_otp(user["id"], otp_code):
        return jsonify({"error": "Invalid or expired OTP"}), 400

    # Auto-verify email on successful OTP login
    verify_email(user["id"])

    token = _create_token(user["id"], user["role"])
    return jsonify({
        "access_token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        },
    })


# ══════════════════════════════════════════════════════════════
#  PASSWORD-BASED LOGIN (fallback)
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = find_by_email(email)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get("is_active", True):
        return jsonify({"error": "Account is disabled. Contact admin."}), 403

    stored_hash = user["password_hash"]
    if stored_hash.startswith("$2"):
        if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return jsonify({"error": "Invalid email or password"}), 401
    else:
        if password != stored_hash:
            return jsonify({"error": "Invalid email or password"}), 401

    if not user.get("is_email_verified", False):
        otp_code = _generate_otp()
        create_otp(user["id"], otp_code, Config.OTP_EXPIRY_MINUTES)
        send_otp_email(email, otp_code)
        return jsonify({
            "error": "Email not verified. A new OTP has been sent.",
            "requires_verification": True,
        }), 403

    token = _create_token(user["id"], user["role"])
    return jsonify({
        "access_token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        },
    })


# ══════════════════════════════════════════════════════════════
#  EMAIL VERIFICATION (signup flow)
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    otp_code = data.get("otp", "").strip()

    user = find_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if verify_otp(user["id"], otp_code):
        verify_email(user["id"])
        return jsonify({"message": "Email verified successfully"})
    else:
        return jsonify({"error": "Invalid or expired OTP"}), 400


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json()
    identifier = data.get("identifier", "") or data.get("email", "")
    identifier = identifier.strip()

    user, method = _find_user_by_identifier(identifier)
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp_code = _generate_otp()
    create_otp(user["id"], otp_code, Config.OTP_EXPIRY_MINUTES)
    contact = user.get("email") or identifier
    send_login_otp(contact, otp_code, method)

    response = {"message": "OTP resent"}
    if Config.DEBUG:
        response["dev_otp"] = otp_code
    return jsonify(response)


# ══════════════════════════════════════════════════════════════
#  PASSWORD MANAGEMENT
# ══════════════════════════════════════════════════════════════

@auth_bp.route("/set-password", methods=["POST"])
def set_password():
    """Set password for first time (requires JWT)."""
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    new_password = data.get("new_password", "")

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    update_password(user["id"], password_hash)

    return jsonify({"message": "Password set successfully"})


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """Change password (requires JWT + current password)."""
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    # Verify current password
    stored_hash = user["password_hash"]
    if stored_hash.startswith("$2"):
        if not bcrypt.checkpw(current_password.encode(), stored_hash.encode()):
            return jsonify({"error": "Current password is incorrect"}), 401
    else:
        if current_password != stored_hash:
            return jsonify({"error": "Current password is incorrect"}), 401

    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    update_password(user["id"], password_hash)

    return jsonify({"message": "Password changed successfully"})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Send a password reset OTP."""
    data = request.get_json()
    identifier = data.get("identifier", "").strip()

    if not identifier:
        return jsonify({"error": "Email or phone number is required"}), 400

    user, method = _find_user_by_identifier(identifier)
    if not user:
        # Don't reveal if user exists or not for security
        return jsonify({"message": "If an account exists, a reset OTP has been sent"})

    otp_code = _generate_otp()
    create_otp(user["id"], otp_code, Config.OTP_EXPIRY_MINUTES)
    contact = user.get("email") or identifier
    send_password_reset_otp(contact, otp_code)

    return jsonify({
        "message": "Reset OTP sent",
        "method": method,
        "masked_contact": _mask_contact(contact, method),
    })


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Verify OTP and set new password."""
    data = request.get_json()
    identifier = data.get("identifier", "").strip()
    otp_code = data.get("otp", "").strip()
    new_password = data.get("new_password", "")

    if not identifier or not otp_code or not new_password:
        return jsonify({"error": "Identifier, OTP, and new password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    user, method = _find_user_by_identifier(identifier)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not verify_otp(user["id"], otp_code):
        return jsonify({"error": "Invalid or expired OTP"}), 400

    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    update_password(user["id"], password_hash)

    return jsonify({"message": "Password reset successfully. You can now log in."})


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _mask_contact(contact, method):
    """Mask email/phone for display: lag***@gmail.com or ****2830"""
    if method == "phone":
        if len(contact) >= 4:
            return "****" + contact[-4:]
        return "****"
    else:
        if "@" in contact:
            local, domain = contact.split("@", 1)
            if len(local) > 3:
                return local[:3] + "***@" + domain
            return local[0] + "***@" + domain
        return contact
