# GCP & Firebase IaC:
# 1. Enables Firebase project, Identity Platform (with Anonymous Auth), Cloud Firestore (Native),
#    Firebase Hosting, and the 3rd service group: Google Cloud Speech/TTS/Translation + Gemini AI Free Tier.
# 2. Provisions Artifact Registry, Secret Manager, Cloud SQL (optional) and Cloud Run v2.
# Usage: terraform init && terraform apply -var project=<id> -var env=staging

terraform {
  required_version = ">= 1.6"
  required_providers {
    google      = { source = "hashicorp/google", version = "~> 6.0" }
    google-beta = { source = "hashicorp/google-beta", version = "~> 6.0" }
  }
}

variable "project" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "env" {
  type    = string
  default = "production"
  validation {
    condition     = contains(["staging", "production"], var.env)
    error_message = "env must be staging or production"
  }
}
variable "image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}

provider "google" {
  project = var.project
  region  = var.region
}

provider "google-beta" {
  project = var.project
  region  = var.region
}

locals {
  required_apis = [
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
    "identitytoolkit.googleapis.com",      # Service 1: Firebase Authentication (Anonymous Auth)
    "firestore.googleapis.com",            # Service 2: Cloud Firestore Database
    "generativelanguage.googleapis.com",   # Service 3a: Gemini API Free Tier (Roleplay + Translator)
    "aiplatform.googleapis.com",           # Service 3b: Vertex AI in Firebase
    "speech.googleapis.com",               # Service 3c: Google Cloud Speech-to-Text (60 min/mo free)
    "texttospeech.googleapis.com",         # Service 3d: Google Cloud Text-to-Speech (4M chars/mo free)
    "translate.googleapis.com",            # Service 3e: Google Cloud Translation (500k chars/mo free)
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.required_apis)
  project            = var.project
  service            = each.value
  disable_on_destroy = false
}

# --- Firebase Project & Web App ---
resource "google_firebase_project" "default" {
  provider   = google-beta
  project    = var.project
  depends_on = [google_project_service.apis]
}

resource "google_firebase_web_app" "web" {
  provider     = google-beta
  project      = var.project
  display_name = "SpeakFlow Web & Mobile (${var.env})"
  depends_on   = [google_firebase_project.default]
}

data "google_firebase_web_app_config" "web" {
  provider   = google-beta
  web_app_id = google_firebase_web_app.web.app_id
}

# --- Service 1: Firebase Authentication with Anonymous Auth Enabled ---
resource "google_identity_platform_config" "auth" {
  provider                   = google-beta
  project                    = var.project
  autodelete_anonymous_users = true
  sign_in {
    allow_duplicate_emails = false
    anonymous {
      enabled = true
    }
    email {
      enabled           = true
      password_required = false
    }
  }
  depends_on = [google_project_service.apis]
}

# --- Service 2: Cloud Firestore Database (Native Mode) ---
resource "google_firestore_database" "database" {
  project                     = var.project
  name                        = "(default)"
  location_id                 = var.region
  type                        = "FIRESTORE_NATIVE"
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
  depends_on                  = [google_project_service.apis]
}

# --- Service 3: Cloud Run Backend + Secret Manager ---
resource "google_artifact_registry_repository" "repo" {
  repository_id = "languaje"
  format        = "DOCKER"
  location      = var.region
  depends_on    = [google_project_service.apis]
}

resource "google_service_account" "api" {
  account_id   = "languaje-api-${var.env}"
  display_name = "Languaje API (${var.env})"
}

locals {
  secrets = ["JWT_SECRET", "GEMINI_API_KEY", "GOOGLE_CLOUD_API_KEY"]
}

resource "google_secret_manager_secret" "s" {
  for_each  = toset(local.secrets)
  secret_id = "languaje-${var.env}-${lower(replace(each.key, "_", "-"))}"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_iam_member" "api_access" {
  for_each  = google_secret_manager_secret.s
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "languaje-api-${var.env}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = var.image
      resources { limits = { cpu = "1", memory = "512Mi" } }
      env {
        name  = "ENV"
        value = var.env
      }
      env {
        name  = "SPEECH_PROVIDER"
        value = "google_cloud"
      }
      env {
        name  = "TTS_PROVIDER"
        value = "google_cloud"
      }
      env {
        name  = "LLM_PROVIDER"
        value = "gemini"
      }
      dynamic "env" {
        for_each = google_secret_manager_secret.s
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = "latest"
            }
          }
        }
      }
      startup_probe {
        http_get { path = "/ready" }
      }
    }
  }
  lifecycle { ignore_changes = [template[0].containers[0].image] }
}

output "url" { value = google_cloud_run_v2_service.api.uri }
output "firebase_web_config" {
  value = {
    projectId        = var.project
    appId            = google_firebase_web_app.web.app_id
    apiKey           = data.google_firebase_web_app_config.web.api_key
    authDomain       = data.google_firebase_web_app_config.web.auth_domain
    storageBucket    = lookup(data.google_firebase_web_app_config.web, "storage_bucket", "")
    messagingSenderId = lookup(data.google_firebase_web_app_config.web, "messaging_sender_id", "")
  }
}
