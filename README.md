# Personal Agentic AI Assistant 🤖

A full-stack **Personal Agentic AI Assistant** designed to act as a digital "Chief of Staff".  
The system supports conversational interaction, contextual memory, and cloud-native deployment with a strong focus on real-world engineering practices.

This project prioritizes **deployment, automation, and infrastructure awareness** alongside AI agent development.

---

## 🚀 Live Deployments

### ✅ AWS Deployment (Primary)

The application is deployed on **AWS** using a cloud-native architecture:

- **Backend:** AWS Lambda (container image via ECR)
- **Frontend:** S3 static hosting + CloudFront CDN
- **Database:** Amazon RDS (PostgreSQL)
- **Container Registry:** Amazon ECR
- **Infrastructure:** Terraform (IaC)
- **CI/CD:** GitHub Actions (automated deployments)

> AWS is the **primary deployment target**, chosen to demonstrate production-oriented cloud engineering.

**Live URLs:**
- Frontend: `https://d2qxcr28lgldld.cloudfront.net`
- Backend API: [Your Lambda Function URL or API Gateway]

---

### 🔁 Render Deployment (Alternative / Earlier Stage)

- The application was also deployed on **Render** during earlier iterations
- Used for rapid development, validation, and stability testing

> Render helped accelerate development, while AWS was used to validate real-world cloud deployment complexity.

---

## 🔄 CI/CD Pipeline

### Automated Deployment Workflow

Every push to `main` triggers an automated deployment pipeline:

```
┌─────────────┐
│  Git Push   │
│   to main   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   GitHub Actions Workflow       │
├─────────────────────────────────┤
│  1. Run Tests                   │
│     • Backend syntax checks     │
│     • Frontend build test       │
│                                 │
│  2. Deploy Backend (Lambda)     │
│     • Build Docker image        │
│     • Push to ECR               │
│     • Update Lambda function    │
│     • Update env variables      │
│                                 │
│  3. Deploy Frontend (S3)        │
│     • Build React production    │
│     • Sync to S3 bucket         │
│     • Invalidate CloudFront     │
└─────────────────────────────────┘
```

### Deployment Features

- ✅ **Automated Testing** - Runs on every push and PR
- ✅ **Multi-stage Deployment** - Backend → Frontend (sequential)
- ✅ **Environment Management** - Secrets managed via GitHub Actions
- ✅ **Cache Optimization** - Proper cache headers for static assets
- ✅ **Rollback Support** - Tagged Docker images for version control
- ✅ **Zero Downtime** - Lambda function waits for update completion

### Deployment Status

Current deployment status: ![Deploy Status](https://github.com/Adhii04/Personal-AI-Assistant/workflows/Deploy%20Full%20Stack%20to%20AWS/badge.svg)

---

## 🧠 Key Features

### 🔐 Authentication
- OAuth 2.0 integration (Google)
- Secure JWT token handling
- Environment-based configuration
- Session management

### 💬 Agentic Chat Assistant
- Built using **LangGraph / LangChain**
- Supports stateful conversations
- OpenRouter API integration (GPT-3.5-turbo)
- Designed for extensible tool-based agent workflows

### 🧠 Contextual & Dynamic Memory
- User preferences extracted from chat
- Context preserved across interactions
- PostgreSQL-backed persistent storage
- Memory graph architecture for long-term intelligence

### 🖥️ Frontend
- **React + Vite** for fast development
- Clean, minimal UI design
- Environment-based API configuration
- Optimized production builds
- CloudFront CDN for global delivery

### ⚙️ Backend
- **Python + FastAPI** framework
- Modular service architecture
- SQLAlchemy ORM with PostgreSQL
- Production-ready Docker configuration
- Lambda-compatible container image
- CORS configuration for secure cross-origin requests

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     User Browser                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   CloudFront CDN     │
              │  (Global Distribution)│
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │    S3 Bucket         │
              │  (React Frontend)    │
              └──────────────────────┘
                         │
                         │ API Calls
                         ▼
              ┌──────────────────────┐
              │   API Gateway /      │
              │   Lambda Function    │
              │   URL                │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   AWS Lambda         │
              │  (FastAPI Backend)   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Amazon RDS         │
              │   (PostgreSQL)       │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   OpenRouter API     │
              │   (LLM Provider)     │
              └──────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL (AWS RDS)
- **AI/ML:** LangChain, LangGraph
- **LLM Provider:** OpenRouter (GPT-3.5-turbo)
- **Authentication:** OAuth 2.0, JWT
- **Deployment:** AWS Lambda (Container)

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** JavaScript/JSX
- **Styling:** CSS
- **Deployment:** S3 + CloudFront

### Infrastructure
- **Cloud Provider:** AWS
- **IaC:** Terraform
- **CI/CD:** GitHub Actions
- **Container Registry:** Amazon ECR
- **CDN:** CloudFront
- **Object Storage:** S3

### DevOps
- **Version Control:** Git, GitHub
- **Containerization:** Docker
- **Automation:** GitHub Actions workflows
- **Secrets Management:** GitHub Secrets

---

## 📦 Project Structure

```
Personal-AI-Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLAlchemy models
│   │   └── ...
│   ├── Dockerfile.lambda        # Lambda-optimized Dockerfile
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── App.jsx              # Main application
│   │   └── ...
│   ├── dist/                    # Production build (generated)
│   ├── package.json             # Node dependencies
│   └── vite.config.js           # Vite configuration
├── .github/
│   └── workflows/
│       └── aws-deploy.yml       # CI/CD pipeline
├── terraform/                   # Infrastructure as Code
│   ├── main.tf
│   ├── lambda.tf
│   ├── s3.tf
│   └── ...
├── .env.example                 # Environment variables template
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- AWS Account
- GitHub Account

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file (see .env.example)
cp .env.example .env

# Run locally
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

---

## 🔧 Deployment

### Automated Deployment (Recommended)

Simply push to the `main` branch:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

The GitHub Actions workflow will automatically:
1. Run tests
2. Build and deploy backend to Lambda
3. Build and deploy frontend to S3/CloudFront

### Manual Deployment

#### Backend to Lambda
```bash
# Build Docker image
docker build -f backend/Dockerfile.lambda -t my-assistant-backend .

# Tag and push to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ECR_REGISTRY>
docker tag my-assistant-backend:latest <ECR_REGISTRY>/<ECR_REPOSITORY>:latest
docker push <ECR_REGISTRY>/<ECR_REPOSITORY>:latest

# Update Lambda
aws lambda update-function-code \
  --function-name <LAMBDA_FUNCTION_NAME> \
  --image-uri <ECR_REGISTRY>/<ECR_REPOSITORY>:latest
```

#### Frontend to S3
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://<FRONTEND_BUCKET> --delete
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
```

---

## 🔐 Environment Variables

### Required Secrets (GitHub Actions)

Set these in **GitHub → Repository → Settings → Secrets**:

#### AWS
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REGISTRY`
- `ECR_REPOSITORY`
- `LAMBDA_FUNCTION_NAME`
- `FRONTEND_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID`

#### Backend
- `DATABASE_URL`
- `SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

#### Frontend
- `VITE_API_URL`

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Run CI tests locally
act -j test  # Requires 'act' CLI tool
```

---

## 📈 Monitoring & Logs

- **Lambda Logs:** CloudWatch Logs
- **Frontend Metrics:** CloudFront metrics
- **Deployment Status:** GitHub Actions dashboard

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- OpenRouter for LLM API access
- AWS for cloud infrastructure
- FastAPI and React communities
- LangChain framework

---

## 📧 Contact

Project Link: [https://github.com/Adhii04/Personal-AI-Assistant](https://github.com/Adhii04/Personal-AI-Assistant)

---

**Built with ❤️ for learning cloud-native AI engineering**
