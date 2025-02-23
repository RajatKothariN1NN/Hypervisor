(Due to technical issues, the search service is temporarily unavailable.)

Here's an optimized README.md that integrates with your Docker setup and environment variables:

```markdown
# MLOps Hypervisor Service

Cluster resource management system with priority-based scheduling and preemption capabilities

## Features

- **JWT Authentication** with refresh tokens
- **Role-Based Access Control** (Admin/Developer/Viewer)
- **Cluster Management** with resource monitoring
- **Intelligent Scheduling** with priority preemption
- **Dockerized Environment** with PostgreSQL & Redis
- **Deployment Dependency Management**

## Quick Start with Docker

```bash
# Start services
docker-compose up -d --build

# Apply migrations
docker-compose exec web python manage.py migrate

# Access API at http://localhost:8000
```

## Environment Configuration

### Required Variables (.env)
```ini
# Database
DB_NAME=Hypervisor
DB_USER=jainrjk9199
DB_PASSWORD=Nayak@4321
DB_HOST=db  # Use 'db' for Docker, 'localhost' for local

# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Redis
REDIS_URL=redis://redis:6379/0  # redis://localhost:6379/0 for local
```

## Development Setup

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Docker Development
```dockerfile
# Rebuild containers after changes
docker-compose up -d --build

# View logs
docker-compose logs -f web
```

## API Endpoints

### Authentication
| Method | Endpoint          | Description                |
|--------|-------------------|----------------------------|
| POST   | /api/auth/register| Register new user          |
| POST   | /api/auth/login   | Obtain JWT tokens          |
| GET    | /api/auth/profile | Get user profile           |

### Organizations
| Method | Endpoint                        | Permission Level       |
|--------|---------------------------------|------------------------|
| POST   | /api/organizations/             | Authenticated User     |
| GET    | /api/organizations/<id>/invite-code/ | Organization Owner |
| POST   | /api/organizations/join/        | Authenticated User     |

### Clusters
| Method | Endpoint            | Permission Level |
|--------|---------------------|------------------|
| GET    | /api/clusters/      | Admin+Viewer     |
| POST   | /api/clusters/      | Admin            |
| GET    | /api/clusters/<id>/ | Authenticated    |

### Deployments
| Method | Endpoint             | Permission Level |
|--------|----------------------|------------------|
| POST   | /api/deployments/    | Developer        |
| GET    | /api/deployments/    | Developer        |
| GET    | /api/deployments/<id>/ | Authenticated  |

## Example API Requests

### Create Cluster (Admin)
```bash
curl -X POST http://localhost:8000/api/clusters/ \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{
    "name": "GPU Cluster",
    "total_ram": 256,
    "total_cpu": 64,
    "total_gpu": 16
  }'
```

### Submit Deployment (Developer)
```bash
curl -X POST http://localhost:8000/api/deployments/ \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{
    "docker_image_path": "tensorflow/serving:latest",
    "required_ram": 64,
    "required_cpu": 16,
    "required_gpu": 4,
    "priority": "HIGH",
    "cluster": 1
  }'
```

## Architecture

### Services
1. **Web**: Django application (Port 8000)
2. **DB**: PostgreSQL database (Port 5432)
3. **Redis**: Job queue for deployments (Port 6379)

### Data Flow
```
User -> API -> Django -> Redis Worker -> Cluster Resources
```

## Testing & Quality

```bash
# Run all tests with coverage
coverage run manage.py test core

# Generate coverage report
coverage report -m

# Check code style
flake8 .

# Run security checks
python manage.py check --deploy
```

## Production Considerations

1. Set `DEBUG=False` in .env
2. Use proper SSL termination
3. Implement database backups
4. Configure monitoring for:
   - Redis queue length
   - Cluster resource utilization
   - Deployment success rates

## Troubleshooting

Common Issues:
```bash
# Database connection issues
docker-compose exec db psql -U ${DB_USER} -d ${DB_NAME}

# Redis connectivity
docker-compose exec redis redis-cli

# View worker logs
docker-compose logs -f web
```

## License
MIT License - See [LICENSE](LICENSE) for details
```
