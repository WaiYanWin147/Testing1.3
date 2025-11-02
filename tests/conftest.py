# tests/conftest.py
import os
import sys
import types
import tempfile
import pytest

# ----------------------------
# 1) Preload test-friendly modules
# ----------------------------
def _install_stub(name, ns=None):
    mod = types.ModuleType(name)
    if ns:
        for k, v in ns.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod

# app.config.Config expected by app/__init__.py
# (Your factory loads app.config.Config)  # :contentReference[oaicite:0]{index=0}
class _TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

_install_stub("app.config", {"Config": _TestConfig})

# Minimal SQLAlchemy models not required for smoke tests,
# but we must satisfy imports performed in create_app() and routes.
# These modules are imported in create_app() before register_blueprints:  # :contentReference[oaicite:1]{index=1}
for ent in [
    "user_profile", "user_account", "category", "request",
    "shortlist", "match_record", "report"
]:
    _install_stub(f"app.entity.{ent}")

# Controllers imported at top of routes module.  # :contentReference[oaicite:2]{index=2}
def _dummy_controller(cls_name):
    # Each controller can be a class with no-op methods
    return type(cls_name, (), {})()

for ctrl in [
    # Auth
    "auth_controller",
    # UserAdmin
    "useradmin_viewUserAccount_controller",
    "useradmin_searchUserAccount_controller",
    "useradmin_createUserAccount_controller",
    "useradmin_updateUserAccount_controller",
    "useradmin_suspendUserAccount_controller",
    "useradmin_activateUserAccount_controller",
    "useradmin_viewUserProfile_controller",
    "useradmin_createUserProfile_controller",
    "useradmin_updateUserProfile_controller",
    "useradmin_suspendUserProfile_controller",
    "useradmin_activateUserProfile_controller",
    "useradmin_searchUserProfile_controller",
    # CSR
    "csr_searchRequest_controller",
    "csr_viewRequest_controller",
    "csr_saveToShortlist_controller",
    "csr_searchShortlist_controller",
    "csr_viewShortlist_controller",
    "csr_searchHistory_controller",
    "csr_viewHistory_controller",
    "csr_removeShortlist_controller",
    # PIN
    "pin_createRequest_controller",
    "pin_viewRequest_controller",
    "pin_updateRequest_controller",
    "pin_deleteRequest_controller",
    "pin_searchRequest_controller",
    "pin_trackViews_controller",
    "pin_trackShortlists_controller",
    "pin_searchMatchRecord_controller",
    # Platform Manager
    "platform_viewCategory_controller",
    "platform_createCategory_controller",
    "platform_updateCategory_controller",
    "platform_suspendCategory_controller",
    "platform_searchCategory_controller",
    "platform_generateDailyReport_controller",
    "platform_generateWeeklyReport_controller",
    "platform_generateMonthlyReport_controller",
    "platform_activateCategory_controller",
]:
    _install_stub(f"app.control.{ctrl}", {
        # Export a class with the “expected” name if code does `XController()`
        # (Fallback works even if not used in our smoke test.)
        # Example: AuthController().login(...)
        # We'll return sane defaults if someone actually calls them.
        # Adjust if you later test those routes.
        **{
            # Common names used in your routes module:
            "AuthController": type("AuthController", (), {"login": lambda *a, **k: ("/", None), "logout": lambda *a, **k: None}),
            "UserAdminViewUserAccountController": type("UserAdminViewUserAccountController", (), {"viewUserAccount": lambda *a, **k: None}),
            "UserAdminSearchUserAccountController": type("UserAdminSearchUserAccountController", (), {"searchUserAccountByName": lambda *a, **k: []}),
            "UserAdminCreateUserAccountController": type("UserAdminCreateUserAccountController", (), {"createUserAccount": lambda *a, **k: True}),
            "UserAdminUpdateUserAccountController": type("UserAdminUpdateUserAccountController", (), {"updateUserAccount": lambda *a, **k: True, "toggleActivation": lambda *a, **k: True}),
            "UserAdminSuspendUserAccountController": type("UserAdminSuspendUserAccountController", (), {"suspendUserAccount": lambda *a, **k: True}),
            "UserAdminActivateUserAccountController": type("UserAdminActivateUserAccountController", (), {"activateUserAccount": lambda *a, **k: True}),
            "UserAdminViewUserProfileController": type("UserAdminViewUserProfileController", (), {"viewUserProfile": lambda *a, **k: None}),
            "UserAdminCreateUserProfileController": type("UserAdminCreateUserProfileController", (), {"createUserProfile": lambda *a, **k: True}),
            "UserAdminUpdateUserProfileController": type("UserAdminUpdateUserProfileController", (), {"updateUserProfile": lambda *a, **k: True, "toggleActivation": lambda *a, **k: True}),
            "UserAdminSuspendUserProfileController": type("UserAdminSuspendUserProfileController", (), {"suspendUserProfile": lambda *a, **k: True}),
            "UserAdminActivateUserProfileController": type("UserAdminActivateUserProfileController", (), {"activateUserProfile": lambda *a, **k: True}),
            "UserAdminSearchUserProfileController": type("UserAdminSearchUserProfileController", (), {"searchUserByProfile": lambda *a, **k: []}),
            "CsrSearchRequestController": type("CsrSearchRequestController", (), {"searchRequest": lambda *a, **k: []}),
            "CsrViewRequestController": type("CsrViewRequestController", (), {"viewRequestDetails": lambda *a, **k: None}),
            "CsrSaveToShortlistController": type("CsrSaveToShortlistController", (), {"saveToShortlist": lambda *a, **k: True}),
            "CsrSearchShortlistController": type("CsrSearchShortlistController", (), {"searchShortlistByCategory": lambda *a, **k: []}),
            "CsrSearchHistoryController": type("CsrSearchHistoryController", (), {"searchHistory": lambda *a, **k: []}),
            "CsrRemoveShortlistController": type("CsrRemoveShortlistController", (), {"removeFromShortlist": lambda *a, **k: True}),
            "PinCreateRequestController": type("PinCreateRequestController", (), {"createRequest": lambda *a, **k: True}),
            "PinViewRequestController": type("PinViewRequestController", (), {"viewRequestDetails": lambda *a, **k: None}),
            "PinUpdateRequestController": type("PinUpdateRequestController", (), {"updateRequest": lambda *a, **k: True}),
            "PinDeleteRequestController": type("PinDeleteRequestController", (), {"deleteRequest": lambda *a, **k: True}),
            "PinSearchRequestController": type("PinSearchRequestController", (), {"searchRequests": lambda *a, **k: []}),
            "PinTrackViewsController": type("PinTrackViewsController", (), {"trackViews": lambda *a, **k: 0}),
            "PinTrackShortlistsController": type("PinTrackShortlistsController", (), {"trackShortlists": lambda *a, **k: 0}),
            "PinSearchMatchRecordController": type("PinSearchMatchRecordController", (), {"searchMatchRecord": lambda *a, **k: []}),
            "PlatformViewCategoryController": type("PlatformViewCategoryController", (), {}),
            "PlatformCreateCat
