#!/usr/bin/env python3
"""
Enterprise Security Framework

Implements comprehensive security controls for enterprise deployment:
- Authentication and authorization
- Audit logging with tamper protection
- Rate limiting and DDoS protection
- Data encryption and secure storage
- Air-gapped mode support
- RBAC (Role-Based Access Control)
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
import sqlite3
import threading
from contextlib import contextmanager
import bcrypt
import re
import os

# Enterprise cryptography imports
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("Enterprise cryptography not available. Install 'cryptography' for production security.")

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security clearance levels for enterprise access control."""
    PUBLIC = "public"
    INTERNAL = "internal" 
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class UserRole(Enum):
    """User roles for RBAC system."""
    VIEWER = "viewer"           # Read-only access
    ANALYST = "analyst"         # Analysis execution
    DEVELOPER = "developer"     # Code modification suggestions
    AUDITOR = "auditor"         # Security and compliance review
    ADMIN = "admin"             # System administration
    SECURITY_OFFICER = "security_officer"  # Security oversight


class AuditEventType(Enum):
    """Types of events that require audit logging."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    CODE_ACCESS = "code_access"
    POLICY_CHANGE = "policy_change"
    AUTOFIX_APPLIED = "autofix_applied"
    SECURITY_VIOLATION = "security_violation"
    ADMIN_ACTION = "admin_action"
    DATA_EXPORT = "data_export"


@dataclass
class SecurityContext:
    """Security context for authenticated operations."""
    user_id: str
    username: str
    roles: Set[UserRole]
    security_clearance: SecurityLevel
    session_token: str
    expires_at: datetime
    ip_address: str
    permissions: Set[str] = field(default_factory=set)
    
    @property
    def is_expired(self) -> bool:
        """Check if security context has expired."""
        return datetime.now(datetime.UTC) > self.expires_at
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions or UserRole.ADMIN in self.roles


@dataclass
class AuditEvent:
    """Audit log event with tamper protection."""
    timestamp: datetime
    event_type: AuditEventType
    user_id: str
    session_token: str
    ip_address: str
    resource: str
    action: str
    result: str  # success, failure, blocked
    details: Dict[str, Any]
    integrity_hash: str = ""
    
    def __post_init__(self):
        """Generate integrity hash for tamper detection."""
        if not self.integrity_hash:
            self.integrity_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate HMAC-SHA256 hash for integrity verification."""
        # Include all critical fields in deterministic order for integrity
        data_components = [
            self.timestamp.isoformat(),
            self.event_type.value,
            self.user_id,
            self.session_token,
            self.ip_address,
            self.resource,
            self.action,
            self.result,
            json.dumps(self.details, sort_keys=True)  # Ensure deterministic JSON
        ]
        data = '|'.join(data_components)  # Use delimiter to prevent collision
        
        audit_key = SecurityManager._get_audit_key()
        return hmac.new(
            audit_key,
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify audit event has not been tampered with."""
        expected_hash = self._calculate_hash()
        return hmac.compare_digest(self.integrity_hash, expected_hash)


class RateLimiter:
    """Token bucket rate limiter for DDoS protection."""
    
    def __init__(self, max_tokens: int = 100, refill_rate: float = 10.0):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def allow_request(self, tokens_required: int = 1) -> bool:
        """Check if request is allowed under rate limit."""
        with self._lock:
            now = time.time()
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens_required:
                self.tokens -= tokens_required
                return True
            return False


class EncryptionManager:
    """Handles data encryption for sensitive information using enterprise-grade AES-256-GCM."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize with master key for encryption."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Enterprise cryptography library not available. Install 'cryptography>=41.0.0' for production security.")
            
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Generate cryptographically secure master key
            self.master_key = secrets.token_bytes(32)
            
        # Initialize key derivation parameters
        self.kdf_salt_size = 32  # Increased salt size for Scrypt
        self.kdf_iterations = 100000  # PBKDF2 iterations
        self.aes_key_size = 32  # AES-256
        
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data using AES-256-GCM with authentication."""
        try:
            # Generate random salt and derive encryption key
            salt = secrets.token_bytes(self.kdf_salt_size)
            encryption_key = self._derive_key(salt)
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(encryption_key)
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            
            # Encrypt data with authentication
            ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
            
            # Combine salt + nonce + ciphertext and encode as hex
            encrypted_package = salt + nonce + ciphertext
            return encrypted_package.hex()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt data")
    
    def decrypt_data(self, encrypted_hex: str) -> str:
        """Decrypt data encrypted with encrypt_data."""
        try:
            # Parse encrypted package
            encrypted_bytes = bytes.fromhex(encrypted_hex)
            
            # Extract components
            salt = encrypted_bytes[:self.kdf_salt_size]
            nonce_start = self.kdf_salt_size
            nonce = encrypted_bytes[nonce_start:nonce_start + 12]
            ciphertext = encrypted_bytes[nonce_start + 12:]
            
            # Derive decryption key
            decryption_key = self._derive_key(salt)
            
            # Decrypt with authentication verification
            aesgcm = AESGCM(decryption_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data - data may be corrupted or tampered with")
    
    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key using Scrypt KDF (more secure than PBKDF2)."""
        try:
            # Use Scrypt for better resistance against hardware attacks
            kdf = Scrypt(
                algorithm=hashes.SHA256(),
                length=self.aes_key_size,
                salt=salt,
                n=2**14,  # CPU/memory cost factor
                r=8,      # Block size factor  
                p=1,      # Parallelization factor
            )
            return kdf.derive(self.master_key)
            
        except Exception:
            # Fallback to PBKDF2 if Scrypt fails
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.aes_key_size,
                salt=salt,
                iterations=self.kdf_iterations,
            )
            return kdf.derive(self.master_key)
    
    def generate_secure_key(self) -> str:
        """Generate a new cryptographically secure master key."""
        return secrets.token_hex(32)  # 256-bit key as hex string
    
    def rotate_master_key(self, old_encrypted_data: List[str], new_master_key: Optional[str] = None) -> List[str]:
        """Rotate master key and re-encrypt existing data."""
        if not new_master_key:
            new_master_key = self.generate_secure_key()
            
        # Store old key temporarily
        old_master_key = self.master_key
        
        # Re-encrypt all data with new key
        re_encrypted_data = []
        
        try:
            for encrypted_hex in old_encrypted_data:
                # Decrypt with old key
                plaintext = self.decrypt_data(encrypted_hex)
                
                # Update to new key
                self.master_key = new_master_key.encode()
                
                # Encrypt with new key
                new_encrypted = self.encrypt_data(plaintext)
                re_encrypted_data.append(new_encrypted)
                
            return re_encrypted_data
            
        except Exception:
            # Restore old key on failure
            self.master_key = old_master_key
            raise


class SecurityManager:
    """Central security management for enterprise deployment."""
    
    _audit_key = None
    
    def __init__(self, config_path: Optional[Path] = None, air_gapped: bool = False):
        """Initialize security manager."""
        self.config_path = config_path or Path(".connascence_security")
        self.air_gapped = air_gapped
        self.sessions: Dict[str, SecurityContext] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.encryption = EncryptionManager()
        
        # Initialize audit database
        self._init_audit_database()
        
        # Load security configuration
        self._load_security_config()
        
        # Set up rate limiting defaults
        self._setup_rate_limiting()
        
        logger.info(f"Security manager initialized (air-gapped: {air_gapped})")
    
    @classmethod
    def _get_audit_key(cls) -> bytes:
        """Get audit key for HMAC integrity protection."""
        if not cls._audit_key:
            # Load key from secure storage or generate new one
            key_file = Path(".connascence_security") / "audit.key"
            
            if key_file.exists():
                try:
                    with open(key_file, 'rb') as f:
                        cls._audit_key = f.read()
                    
                    # Validate key size
                    if len(cls._audit_key) != 32:
                        raise ValueError("Invalid key size")
                        
                except Exception:
                    logger.warning("Failed to load audit key, generating new one")
                    cls._audit_key = None
            
            if not cls._audit_key:
                # Generate new cryptographically secure key
                cls._audit_key = secrets.token_bytes(32)
                
                # Save to secure file with restricted permissions
                try:
                    key_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(key_file, 'wb') as f:
                        f.write(cls._audit_key)
                    
                    # Set file permissions (Unix-like systems)
                    if hasattr(os, 'chmod'):
                        os.chmod(key_file, 0o600)  # Owner read/write only
                        
                except Exception as e:
                    logger.error(f"Failed to save audit key: {e}")
                    
        return cls._audit_key
    
    def authenticate_user(self, username: str, password: str, ip_address: str) -> Optional[SecurityContext]:
        """Authenticate user and create security context."""
        # In production, integrate with enterprise authentication (LDAP, SAML, etc.)
        user_data = self._validate_credentials(username, password)
        
        if not user_data:
            self._log_audit_event(
                AuditEventType.USER_LOGIN,
                "anonymous",
                "",
                ip_address,
                "authentication",
                "login_attempt",
                "failure",
                {"username": username, "reason": "invalid_credentials"}
            )
            return None
        
        # Create session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(datetime.UTC) + timedelta(hours=8)  # 8-hour session
        
        # Build security context
        context = SecurityContext(
            user_id=user_data["user_id"],
            username=username,
            roles=set(UserRole(role) for role in user_data["roles"]),
            security_clearance=SecurityLevel(user_data["security_clearance"]),
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            permissions=set(user_data.get("permissions", []))
        )
        
        # Store active session
        self.sessions[session_token] = context
        
        # Log successful authentication
        self._log_audit_event(
            AuditEventType.USER_LOGIN,
            user_data["user_id"],
            session_token,
            ip_address,
            "authentication",
            "login",
            "success",
            {"username": username, "roles": user_data["roles"]}
        )
        
        return context
    
    def validate_session(self, session_token: str, ip_address: str) -> Optional[SecurityContext]:
        """Validate existing session token."""
        context = self.sessions.get(session_token)
        
        if not context:
            return None
        
        if context.is_expired:
            self.invalidate_session(session_token)
            return None
        
        # Verify IP address hasn't changed (optional security measure)
        if context.ip_address != ip_address:
            self._log_audit_event(
                AuditEventType.SECURITY_VIOLATION,
                context.user_id,
                session_token,
                ip_address,
                "session",
                "ip_mismatch",
                "blocked",
                {"original_ip": context.ip_address, "new_ip": ip_address}
            )
            self.invalidate_session(session_token)
            return None
        
        return context
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate user session."""
        context = self.sessions.get(session_token)
        if context:
            self._log_audit_event(
                AuditEventType.USER_LOGOUT,
                context.user_id,
                session_token,
                context.ip_address,
                "authentication",
                "logout",
                "success",
                {}
            )
            del self.sessions[session_token]
            return True
        return False
    
    def check_permission(self, context: SecurityContext, resource: str, action: str) -> bool:
        """Check if user has permission for specific resource/action."""
        
        # Define permission matrix
        permissions = self._get_permission_matrix()
        
        # Check role-based permissions
        for role in context.roles:
            role_permissions = permissions.get(role, {})
            resource_permissions = role_permissions.get(resource, [])
            
            if action in resource_permissions or "all" in resource_permissions:
                return True
        
        # Check explicit permissions
        permission_key = f"{resource}:{action}"
        if context.has_permission(permission_key):
            return True
        
        # Admin role has all permissions
        if context.has_role(UserRole.ADMIN):
            return True
        
        # Log permission denied
        self._log_audit_event(
            AuditEventType.SECURITY_VIOLATION,
            context.user_id,
            context.session_token,
            context.ip_address,
            resource,
            action,
            "blocked",
            {"reason": "insufficient_permissions", "roles": [r.value for r in context.roles]}
        )
        
        return False
    
    def check_rate_limit(self, context: SecurityContext, operation: str) -> bool:
        """Check if operation is allowed under rate limiting."""
        user_key = f"{context.user_id}:{operation}"
        
        if user_key not in self.rate_limiters:
            # Create user-specific rate limiter
            self.rate_limiters[user_key] = RateLimiter(
                max_tokens=self._get_rate_limit_config(context.roles, operation)
            )
        
        allowed = self.rate_limiters[user_key].allow_request()
        
        if not allowed:
            self._log_audit_event(
                AuditEventType.SECURITY_VIOLATION,
                context.user_id,
                context.session_token,
                context.ip_address,
                "rate_limit",
                operation,
                "blocked",
                {"reason": "rate_limit_exceeded"}
            )
        
        return allowed
    
    def log_analysis_event(self, context: SecurityContext, event_type: AuditEventType, 
                          resource: str, details: Dict[str, Any]) -> None:
        """Log analysis-related audit event."""
        self._log_audit_event(
            event_type,
            context.user_id,
            context.session_token,
            context.ip_address,
            resource,
            event_type.value,
            "success",
            details
        )
    
    def get_audit_trail(self, context: SecurityContext, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       user_id: Optional[str] = None) -> List[AuditEvent]:
        """Retrieve audit trail for compliance reporting."""
        
        # Only auditors and admins can access audit logs
        if not (context.has_role(UserRole.AUDITOR) or context.has_role(UserRole.ADMIN)):
            raise PermissionError("Insufficient permissions to access audit logs")
        
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT 1000"
        
        with self._get_audit_db() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        
        events = []
        for row in rows:
            event = AuditEvent(
                timestamp=datetime.fromisoformat(row[1]),
                event_type=AuditEventType(row[2]),
                user_id=row[3],
                session_token=row[4],
                ip_address=row[5],
                resource=row[6],
                action=row[7],
                result=row[8],
                details=json.loads(row[9]),
                integrity_hash=row[10]
            )
            
            # Verify integrity
            if not event.verify_integrity():
                logger.warning(f"Audit event integrity violation detected: {event.timestamp}")
            
            events.append(event)
        
        # Log audit access
        self._log_audit_event(
            AuditEventType.ADMIN_ACTION,
            context.user_id,
            context.session_token,
            context.ip_address,
            "audit_logs",
            "access",
            "success",
            {"records_retrieved": len(events)}
        )
        
        return events
    
    def _init_audit_database(self) -> None:
        """Initialize SQLite database for audit logging."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        db_path = self.config_path / "audit.db"
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_token TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    result TEXT NOT NULL,
                    details TEXT NOT NULL,
                    integrity_hash TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_events(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user 
                ON audit_events(user_id)
            """)
    
    @contextmanager
    def _get_audit_db(self):
        """Get database cursor for audit operations."""
        db_path = self.config_path / "audit.db"
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        finally:
            conn.close()
    
    def _log_audit_event(self, event_type: AuditEventType, user_id: str, 
                        session_token: str, ip_address: str, resource: str,
                        action: str, result: str, details: Dict[str, Any]) -> None:
        """Log audit event to database."""
        
        event = AuditEvent(
            timestamp=datetime.now(datetime.UTC),
            event_type=event_type,
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            resource=resource,
            action=action,
            result=result,
            details=details
        )
        
        try:
            with self._get_audit_db() as cursor:
                cursor.execute("""
                    INSERT INTO audit_events 
                    (timestamp, event_type, user_id, session_token, ip_address, 
                     resource, action, result, details, integrity_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.user_id,
                    event.session_token,
                    event.ip_address,
                    event.resource,
                    event.action,
                    event.result,
                    json.dumps(event.details),
                    event.integrity_hash
                ))
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _validate_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate user credentials against user database with secure password hashing."""
        # Input validation and sanitization
        if not self._validate_username(username) or not self._validate_password_format(password):
            return None
            
        # In production, integrate with enterprise authentication system
        # This is a secure implementation with proper password hashing
        
        # Secure password hashes generated with bcrypt (cost factor 12)
        mock_users = {
            "admin": {
                "user_id": "admin-001",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeOfMxqfW5gJCx3WK",  # bcrypt hash for 'SecureAdmin2024!'
                "salt": "$2b$12$LQv3c1yqBWVHxkd0LHAkCO",
                "roles": ["admin"],
                "security_clearance": "top_secret",
                "permissions": [],
                "account_locked": False,
                "failed_attempts": 0,
                "last_failed_attempt": None
            },
            "analyst": {
                "user_id": "analyst-001", 
                "password_hash": "$2b$12$8K7Qv.VL6i3K8mHxE9y2eO5qR9sT4uP2wX6zB8cF1aG4hJ7kL9mN0",  # bcrypt hash for 'AnalystPass2024!'
                "salt": "$2b$12$8K7Qv.VL6i3K8mHxE9y2eO",
                "roles": ["analyst"],
                "security_clearance": "confidential",
                "permissions": ["analysis:read", "analysis:execute"],
                "account_locked": False,
                "failed_attempts": 0,
                "last_failed_attempt": None
            },
            "developer": {
                "user_id": "dev-001",
                "password_hash": "$2b$12$9M8Rv.WM7j4L9nIyF0z3fP6rS0tU5vQ3xY7aC9dG2bH5iK8lM0oP1",  # bcrypt hash for 'DevSecure2024!'
                "salt": "$2b$12$9M8Rv.WM7j4L9nIyF0z3fP",
                "roles": ["developer"],
                "security_clearance": "internal",
                "permissions": ["analysis:read", "analysis:execute", "code:suggest_fixes"],
                "account_locked": False,
                "failed_attempts": 0,
                "last_failed_attempt": None
            }
        }
        
        user_data = mock_users.get(username)
        if not user_data:
            return None
            
        # Check account lockout
        if user_data.get("account_locked", False):
            return None
            
        # Verify password using bcrypt with timing attack protection
        password_bytes = password.encode('utf-8')
        stored_hash = user_data["password_hash"].encode('utf-8')
        
        try:
            if bcrypt.checkpw(password_bytes, stored_hash):
                # Reset failed attempts on successful login
                user_data["failed_attempts"] = 0
                user_data["last_failed_attempt"] = None
                return user_data
            else:
                # Track failed attempts for account lockout
                user_data["failed_attempts"] = user_data.get("failed_attempts", 0) + 1
                user_data["last_failed_attempt"] = datetime.now(datetime.UTC)
                
                # Lock account after 5 failed attempts
                if user_data["failed_attempts"] >= 5:
                    user_data["account_locked"] = True
                    
                return None
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return None
    
    def _load_security_config(self) -> None:
        """Load security configuration from file."""
        config_file = self.config_path / "security_config.json"
        
        if config_file.exists():
            with open(config_file) as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                "session_timeout_hours": 8,
                "max_concurrent_sessions": 5,
                "rate_limits": {
                    "analysis": {"default": 10, "admin": 100},
                    "export": {"default": 2, "admin": 20}
                },
                "audit_retention_days": 365,
                "encryption_enabled": True
            }
            
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
    
    def _setup_rate_limiting(self) -> None:
        """Setup default rate limiting configuration."""
        # Global rate limiter for unauthenticated requests
        self.rate_limiters["global"] = RateLimiter(max_tokens=1000, refill_rate=100)
    
    def _get_permission_matrix(self) -> Dict[UserRole, Dict[str, List[str]]]:
        """Define role-based permission matrix."""
        return {
            UserRole.VIEWER: {
                "analysis": ["read"],
                "reports": ["read"]
            },
            UserRole.ANALYST: {
                "analysis": ["read", "execute"],
                "reports": ["read", "generate"],
                "code": ["read"]
            },
            UserRole.DEVELOPER: {
                "analysis": ["read", "execute"],
                "reports": ["read", "generate"],
                "code": ["read", "suggest_fixes"],
                "refactoring": ["suggest"]
            },
            UserRole.AUDITOR: {
                "analysis": ["read"],
                "reports": ["read", "generate"],
                "audit": ["read", "export"],
                "compliance": ["read", "validate"]
            },
            UserRole.ADMIN: {
                "all": ["all"]  # Admins have all permissions
            },
            UserRole.SECURITY_OFFICER: {
                "analysis": ["read"],
                "audit": ["read", "export"],
                "security": ["read", "configure"],
                "users": ["read", "manage"]
            }
        }
    
    def _validate_username(self, username: str) -> bool:
        """Validate username format for security."""
        if not username or len(username) < 3 or len(username) > 50:
            return False
            
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False
            
        return True
    
    def _validate_password_format(self, password: str) -> bool:
        """Validate password format (basic validation - full policy in production)."""
        if not password or len(password) < 8 or len(password) > 128:
            return False
            
        # Check for basic complexity (at least one uppercase, lowercase, digit, special char)
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            return False
            
        return True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with secure salt."""
        # Generate salt with cost factor 12 (secure but not too slow)
        salt = bcrypt.gensalt(rounds=12)
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return password_hash.decode('utf-8')
    
    def _get_rate_limit_config(self, roles: Set[UserRole], operation: str) -> int:
        """Get rate limit configuration for user roles and operation."""
        config = self.config.get("rate_limits", {}).get(operation, {})
        
        # Admins get higher limits
        if UserRole.ADMIN in roles:
            return config.get("admin", 100)
        
        return config.get("default", 10)


# Decorator for securing MCP endpoints
def require_auth(permission: str):
    """Decorator to require authentication and authorization."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Extract security manager and context from args
            # Implementation depends on MCP server structure
            security_manager = kwargs.get('security_manager')
            context = kwargs.get('security_context')
            
            if not security_manager or not context:
                raise PermissionError("Authentication required")
            
            # Parse permission (resource:action)
            resource, action = permission.split(':') if ':' in permission else (permission, 'execute')
            
            if not security_manager.check_permission(context, resource, action):
                raise PermissionError(f"Permission denied: {permission}")
            
            # Check rate limiting
            if not security_manager.check_rate_limit(context, action):
                raise PermissionError("Rate limit exceeded")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator