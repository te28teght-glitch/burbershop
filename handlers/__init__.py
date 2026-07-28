from .start import router as start_router
from .booking import router as booking_router
from .admin_panel import router as admin_router

__all__ = ['start_router', 'booking_router', 'admin_router']