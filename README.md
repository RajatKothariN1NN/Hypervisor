# MLOps Hypervisor Service

## Setup Instructions

### Prerequisites
- Python 3.9+
- PostgreSQL
- Redis (for queueing)
- Docker (optional)

### Local Development
1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate


## API Endpoints

### Authentication
- **POST /api/auth/register/**: Register a new user.
- **POST /api/auth/login/**: Log in and get JWT tokens.
- **GET /api/auth/profile/**: Get the authenticated user's profile.
- **POST /api/auth/token/refresh/**: Refresh an access token.

### Join Organization flow
- **POST /api/auth/organizations/**: create an organization.
- **GET /api/auth/organizations/<id>/invite-code/**: Get invite code of organization.
- **POST /api/auth/organizations/join/**: Join organization using invite code.