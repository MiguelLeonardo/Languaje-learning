# GCP skeleton: Artifact Registry, Cloud SQL (Postgres), Secret Manager, Cloud Run (staging/production).
# Usage: terraform init && terraform apply -var project=<id> -var env=staging
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
  # backend "gcs" { bucket = "<tf-state-bucket>" prefix = "languaje" }
}

variable "project" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "env" {
  type = string
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

resource "google_artifact_registry_repository" "repo" {
  repository_id = "languaje"
  format        = "DOCKER"
  location      = var.region
}

resource "google_service_account" "api" {
  account_id   = "languaje-api-${var.env}"
  display_name = "Languaje API (${var.env})"
}

resource "google_sql_database_instance" "pg" {
  name             = "languaje-${var.env}"
  database_version = "POSTGRES_16"
  settings {
    tier              = var.env == "production" ? "db-custom-2-7680" : "db-f1-micro"
    availability_type = var.env == "production" ? "REGIONAL" : "ZONAL"
    backup_configuration { enabled = true }
    ip_configuration { ipv4_enabled = false } # private IP / Cloud SQL connector only
  }
  deletion_protection = var.env == "production"
}

resource "google_sql_database" "db" {
  name     = "languaje"
  instance = google_sql_database_instance.pg.name
}

locals {
  secrets = ["JWT_SECRET", "DATABASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
}

resource "google_secret_manager_secret" "s" {
  for_each  = toset(local.secrets)
  secret_id = "languaje-${var.env}-${lower(replace(each.key, "_", "-"))}"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "api_access" {
  for_each  = google_secret_manager_secret.s
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "sql_client" {
  project = var.project
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "languaje-api-${var.env}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = var.env == "production" ? 1 : 0
      max_instance_count = 10
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance { instances = [google_sql_database_instance.pg.connection_name] }
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
        value = "openai_whisper"
      }
      env {
        name  = "LLM_PROVIDER"
        value = "anthropic"
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
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
      startup_probe {
        http_get { path = "/ready" }
      }
    }
  }
  lifecycle { ignore_changes = [template[0].containers[0].image] } # image managed by CI
}

output "url" { value = google_cloud_run_v2_service.api.uri }
